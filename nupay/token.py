import re
import hashlib
import time
import os
import logging
from decimal import Decimal


class BadTokenFormatError(Exception):
    pass


class Token(object):
    
    MIN_VALUE = Decimal("0.01")
    MAX_VALUE = Decimal("999.99")
    TOKEN_FORMAT = re.compile(r'\d{3}\.\d{2}\%[A-Za-z0-9]{64}\%[0-9]{10}$')

    def __init__(self, token_string = None, value = None):
        self.logger = logging.getLogger(__name__)

        if (value is None and token_string is None) or (value is not None and token_string is not None):
            raise ValueError("Either token_string or value must be defined")

        if token_string is None:
            token_string = Token._create_token_string(value)
        
        token_string = token_string.strip()

        Token._check_token_string_format(token_string)

        self._token_string = token_string
        self._hash_string = None

        self.logger.debug("New token: %s" % token_string)
    
    @staticmethod
    def _check_token_string_format(token_string):
        if Token.TOKEN_FORMAT.match(token_string) is None:    
            logger = logging.getLogger(__name__)
            logger.warning("Token %s is badly formatted" % token_string)
            raise BadTokenFormatError()

    @staticmethod
    def _create_token_string(value):
        if type(value) != Decimal:
            raise TypeError("Value must be a Decimal type")
        
        if value < Token.MIN_VALUE or value > Token.MAX_VALUE:
            raise ValueError("Value is out of bounds")

        t = str(int(time.time()))
        sha256 = hashlib.sha256()
        sha256.update(os.urandom(256))

        token_string = "%06.02f" % value
        token_string += '%' + sha256.hexdigest()
        token_string += '%' + t

        return token_string

    @property
    def hash_string(self):
        if self._hash_string is None:
            sha512 = hashlib.sha512()
            sha512.update(self._token_string)
            self._hash_string = sha512.hexdigest()
        return self._hash_string

    @property
    def token_string(self):
        return self._token_string;

    def __eq__(self, other):
        return other._token_string == self._token_string

    def __str__(self):
        return self._token_string

    def __repr__(self):
        return self._token_string

