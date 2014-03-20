import re
import hashlib
import time
import os
import logging
from decimal import Decimal
import datetime

class BadTokenFormatError(Exception):
    pass

class Token(object):
    
    MIN_VALUE = Decimal("0.01")
    MAX_VALUE = Decimal("999.99")
    TOKEN_FORMAT = r'(\d{3}\.\d{2})\%([A-Za-z0-9]{64})\%([0-9]{10})$'
    TOKEN_FORMAT_RE = re.compile(TOKEN_FORMAT)

    HASH_STRING_LENGTH = 128

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
        self._value = None
        self._created = None

        self.logger.debug("New token: %s" % token_string)
    
    @staticmethod
    def _check_token_string_format(token_string):
        match = Token.TOKEN_FORMAT_RE.match(token_string)
        if match is None:
            logger = logging.getLogger(__name__)
            logger.warning("Token %s is badly formatted" % token_string)
            raise BadTokenFormatError()
        return Decimal(match.group(1))

    @staticmethod
    def _create_token_string(value):
        if type(value) != Decimal:
            raise TypeError("Value must be a Decimal type")
        
        if value < Token.MIN_VALUE or value > Token.MAX_VALUE:
            raise ValueError("Value is out of bounds")

        from Crypto import Random

        t = str(int(time.time()))
        token_string = "%06.02f" % value
        token_string += '%' + Random.get_random_bytes(32).encode('hex')
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

    @property
    def value(self):
        if self._value is None: 
            match = Token.TOKEN_FORMAT_RE.match(self.token_string)
            self._value = Decimal(match.group(1))
        return self._value

    @property
    def created(self):
        if self._created is None:
            match = Token.TOKEN_FORMAT_RE.match(self.token_string)
            self._created = datetime.datetime.utcfromtimestamp(int(match.group(3)))
        return self._created

    def __eq__(self, other):
        return other._token_string == self._token_string

    def __str__(self):
        return self._token_string

    def __repr__(self):
        return self._token_string

