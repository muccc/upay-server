import logging
import sqlalchemy
from sqlalchemy import Table, Column, DateTime, String, MetaData, select
from functools import partial

import time
from datetime import datetime
from decimal import Decimal

from session import SessionConnectionError
from token import Token

class NoValidTokenFoundError(Exception):
    pass

class TimeoutError(Exception):
    pass

class TokenAuthority(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        try:
            isolation_level = 'SERIALIZABLE'
            self._engine = sqlalchemy.create_engine(config.get('Database', 'url'),
                                                    echo = False,
                                                    isolation_level = isolation_level)
            self.connect()
            self.disconnect()
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)
        self._init_metadata()
    
    def _init_metadata(self):
        self._metadata = MetaData()
        self._tokens = Table('tokens', self._metadata,
            Column('hash', String(Token.HASH_STRING_LENGTH), primary_key=True),
            Column('created', DateTime),
            Column('used', DateTime)
        )

    def connect(self):
        self._logger.debug("connect()")
        self._connection = self._engine.connect()
        self._transaction = self._connection.begin()

    def disconnect(self):
        self._logger.debug("disconnect()")
        self._transaction.close()
        self._transaction = None
        self._connection.close()
        self._connection = None

    def commit(self):
        self._logger.debug("commit()")
        self._transaction.commit() 
        self._transaction = self._connection.begin()

    def rollback(self):
        self._logger.debug("rollback()")
        self._transaction.rollback() 
        self._transaction = self._connection.begin()
        
    def bootstrap_db(self):
        if self.config.get('Database','allow_bootstrap') != 'True':
            self.logger.error('Bootstrapping is disabled in the configuration')
            return

        self._metadata.drop_all(self._engine)
        self._metadata.create_all(self._engine)

    def split_token(self, token, split_tokens):

        total_split_value = sum([t.value for t in split_tokens])

        if total_split_value != token.value:
            raise ValueError("Split value does not match token value")
        
        
        with self._connection.begin() as trans:
            self.validate_token(token)
            self.void_token(token)
            map(self.create_token, split_tokens)
            return split_tokens 
    
    def merge_tokens(self, tokens):
        total_value = sum([token.value for token in tokens])
        token = Token(value = total_value)

        with self._connection.begin() as trans:
            map(self.validate_token, tokens)
            map(self.void_token, tokens)
            self.create_token(token)
            return token

    def create_token(self, token):
        # Do not use utcnow() as time.time() gets mocked by the unit tests
        now = datetime.utcfromtimestamp(time.time())
        if abs((token.created - now).total_seconds()) >= 60:
            raise TimeoutError("Token is too old")

        with self._connection.begin() as trans:
            ins = self._tokens.insert().values(hash = token.hash_string, created = token.created)
            self._execute(ins)

    def void_token(self, token):
        with self._connection.begin() as trans:
            statement = self._tokens.update().where(self._tokens.c.hash == token.hash_string) \
                                            .where(self._tokens.c.created == token.created) \
                                            .where(self._tokens.c.used == None) \
                                            .values(used = datetime.utcnow())
            res = self._execute(statement)
            if res.rowcount != 1:
                raise NoValidTokenFoundError('Token could not be voided')
    
    def validate_token(self, token):
        result = self._execute(select([self._tokens]) \
                            .where(self._tokens.c.hash == token.hash_string) \
                            .where(self._tokens.c.created == token.created) \
                            .where(self._tokens.c.used == None)).fetchone()
        if result == None:
            raise NoValidTokenFoundError('Token not found')

    def _execute(self, statement):
        return self._connection.execute(statement)

