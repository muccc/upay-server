import requests
import sys
import json
import logging
import ssl
import time
import ConfigParser
from decimal import Decimal
from collections import defaultdict

from token import Token
from token_client import TokenClient

class SessionConnectionError(Exception):
    pass

class NotEnoughCreditError(Exception):
    pass

class RollbackError(Exception):
    pass

class CashTimeoutError(Exception):
    pass

class ConnectionError(Exception):
    pass

class SessionError(Exception):
    pass

class SessionManager(object):
    def __init__(self, collectors,\
                    max_value = Token.MAX_VALUE,\
                    config_location = None):

        self._logger = logging.getLogger(__name__)
        if config_location:
            self._client = TokenClient(config_location = config_location)
        else:
            self._client = TokenClient()

        self._collectors = collectors
        self._max_value = max_value

    def create_session(self):
        return Session(self._client, self._collectors, self._max_value)


class Session(object):
    def __init__(self, client, collectors, max_value):
        self._logger = logging.getLogger(__name__)
        self._client = client
        self._collectors = collectors
        self._tokens = set()
        self._max_value = max_value
        #self._total = 0
        self._cashed_tokens = []
        self._locked_tokens = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self._locked_tokens == []:
            return False

        if type is None:
            # There was no exception. Lets collect our tokens
            self.collect()
        else:
            # There was an exception. Rollback tokens which
            # have not yet been collected
            self.rollback()

        # Do not suppress exceptions
        return False

    @property
    def credit(self):
        return sum([token.value for token in self._tokens])

    #@property
    #def total(self):
    #    return sum([token.value for token in self.cashed_tokens])

    #@property
    #def total(self):
    #    return self._total

    def validate_tokens(self, new_tokens = [], callback = None):
        tokens = self._tokens | set([t for t in new_tokens \
            if t.value <= self._max_value])

        #try:
        self._tokens = set(self._client.validate_tokens(tokens))
        #except :
            # TODO
        #    pass

        return self.credit

    def select_tokens(self, amount):
        # The problem is the subset sum problem

        # For now just have a look if there is a token
        # with the correct amount or if there are enough
        # tokens with the same value that we can use

        sorted_tokens = defaultdict(list)
        for token in self._tokens:
            if token.value == amount:
                return [token]
            if amount % token.value == 0:
                sorted_tokens[token.value].append(token)

        tokens = []
        for value in sorted_tokens:
            needed_count = amount / value
            if len(sorted_tokens[value]) >= needed_count:
                return sorted_tokens[value][:int(needed_count)]

        raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    def cash(self, amount):
        # First we need to figure out if some combination
        # of tokens can create the needed amount
        tokens_to_cash = self.select_tokens(amount)
        assert(sum([t.value for t in tokens_to_cash]) == amount)
        new_tokens = [Token(amount)]

        self.collect()

        try:
            self._client.transform_tokens(tokens_to_cash, new_tokens)
        except (SessioError, ConnectionError, \
                    NotEnoughCreditError) as e:
            # Nothing happened
            raise e
        except TimeoutError:
            # We don't know what happened
            if not self._check_tokens(new_tokens):
                raise e
        except RuntimeError as e:
            # We don't know what happened
            if not self._check_tokens(new_tokens):
                raise e
        except Exception as e:
            # We don't know what happened
            self._logger.warning("Unknown exception while cashing", exc_info=True)
            if not self._check_tokens(new_tokens):
                raise e

        self._locked_tokens = new_tokens
        self._cashed_tokens = tokens_to_cash

        self.validate_tokens()

    def collect(self):
         if self._locked_tokens != []:
            for collector in self._collectors:
                collector.collect_tokens(self._locked_tokens)
            self._locked_tokens = []

    def rollback(self):
        # Take the locked_tokens and transform them back
        for i in range(5):
            try:
                self._client.transform_tokens(self._locked_tokens, self._cashed_tokens)
                break
            except Exception as e:
                self._logger.warning("Exception while rolling back tokens", exc_info=True)
            time.sleep(1)

        self._locked_tokens = []

    def _check_tokens(self, tokens):
        # Check that all tokens do exist:
        for i in range(5):
            try:
                tokens = self._client.validate(new_tokens)
                break
            except Exception as e:
                self._logger.warning("Exception while checking tokens", exc_info=True)
        else:
            return False

        for t in new_tokens:
            if t not in tokens:
                return False

        return True
