# -*- coding: utf-8 -*-
import re
import hashlib
import time
import os
import logging
from decimal import Decimal
import datetime
import jsonschema
import json
import iso8601
import UserDict

class BadTokenFormatError(Exception):
    pass

class Token(UserDict.DictMixin):

    MIN_VALUE = Decimal("0.01")
    MAX_VALUE = Decimal("999.99")
    TOKEN_FORMAT = r'(\d{3}\.\d{2})\%([A-Za-z0-9]{64})\%([0-9]{10})$'
    TOKEN_FORMAT_RE = re.compile(TOKEN_FORMAT)

    HASH_STRING_LENGTH = 128
    VALUE_SCHEMA = {
        'type': 'string',
        'pattern': r'^\d{3}\.\d{2}$'
    }

    TOKEN_SCHEMA = {
        'type': 'object',
        'required': ['value', 'token', 'created'],
        'properties': {
            'token': {
                'type': 'string',
                'pattern': r'^[A-Fa-f0-9]{64}$'
                #'pattern': r'[A-Fa-f0-9]{10}'
            },
            'created': {
                'type': 'string'
            },
            'value': VALUE_SCHEMA
        }
    }

    def __init__(self, initial_value):
        self.logger = logging.getLogger(__name__)

        if type(initial_value) is Decimal:
            self._create_from_value(initial_value)
        else:
            try:
                token = json.loads(initial_value)
                #print token
            except ValueError as e:
                raise BadTokenFormatError(e)

            try:
                jsonschema.validate(token, self.TOKEN_SCHEMA)
            except jsonschema.ValidationError as e:
                raise BadTokenFormatError(e)

            self._token_string = token['token']
            try:
                self._created = iso8601.parse_date(token['created'])
            except iso8601.ParseError as e:
                raise BadTokenFormatError(e)

            self._value = Decimal(token['value'])

        self._hash_string = None
        self.logger.debug("New token: %s" % self)

    def _create_from_value(self, value):
        if value < Token.MIN_VALUE or value > Token.MAX_VALUE:
            raise ValueError("Value is out of bounds")

        from Crypto import Random
        self._token_string = Random.get_random_bytes(32).encode('hex')
        
        # Use time.time() as it gets mocked in the unit tests
        self._created = datetime.datetime.utcfromtimestamp(time.time())
        self._value = value

    @property
    def hash_string(self):
        if self._hash_string is None:
            sha512 = hashlib.sha512()
            self.logger.debug("String to hash: " + '%'.join((self._token_string, self.created.isoformat())))
            sha512.update('%'.join((self._token_string, self.created.isoformat())))
            self._hash_string = sha512.hexdigest()
        return self._hash_string

    @property
    def token_string(self):
        return self._token_string;

    @property
    def json_string(self):
        value = "%06.02f" % self._value
        return json.dumps({'value': value, 'token': self.token_string, 'created': self.created.isoformat()})

    @property
    def value(self):
        return self._value

    @property
    def created(self):
        return self._created

    def __eq__(self, other):
        return other._token_string == self._token_string

    def __str__(self):
        return self.json_string

    def __repr__(self):
        return self.json_string

    def __getitem__(self, item):
        if item == 'created':
            return self.created.isoformat()
        if item == 'token':
            return self._token_string
        if item == 'value':
            return "%06.02f" % self._value

        return None

    def keys(self):
        return ('created', 'token', 'value')
