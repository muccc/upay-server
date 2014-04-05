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
import base64

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
        'required': ['value', 'created'],
        'properties': {
            'token': {
                'type': 'string',
                'pattern': r'^[A-Fa-f0-9]{64}$'
            },
            'hash': {
                'type': 'string',
                'pattern': r'^[A-Fa-f0-9]{128}$'
            },
            'created': {
                'type': 'string'
            },
            'value': VALUE_SCHEMA
        }
    }

    def __init__(self, initial_value, cipher = None):
        self.logger = logging.getLogger(__name__)

        if type(initial_value) is Decimal:
            self._create_from_value(initial_value)
        else:
            try:
                token = json.loads(initial_value)
                #print token
            except ValueError as e:
                raise BadTokenFormatError(e)
            except TypeError:
                # Lets assume it is a already a dict
                token = initial_value

            try:
                jsonschema.validate(token, self.TOKEN_SCHEMA)
            except jsonschema.ValidationError as e:
                raise BadTokenFormatError(e)

            try:
                self._created = iso8601.parse_date(token['created'], default_timezone=None)
            except iso8601.ParseError as e:
                raise BadTokenFormatError(e)

            self._value = Decimal(token['value'])

            if ('token' in token) == ('hash' in token):
                raise BadTokenFormatError("A token must either specify a hash or a token")

            if 'encrypted_token' in token and 'hash' not in token:
                raise BadTokenFormatError("An encrypted token must also specify its hash")

            if 'encrypted_token' in token and 'token' in token:
                raise BadTokenFormatError("An encrypted token must not specify a token")

            if 'token' in token:
                self._token_string = str(token['token'])
            elif 'hash' in token:
                self._hash_string = str(token['hash'])
                if 'encrypted_token' in token:
                    self._encrypted_token = str(token['encrypted_token'])

        if cipher is not None and self._encrypted_token is not None:
            self._token_string = cipher.decrypt(base64.decodestring(self._encrypted_token))
            self._encrypted_token = None

        self.logger.debug("New token: %s" % self)

    def _create_from_value(self, value):
        if value < Token.MIN_VALUE or value > Token.MAX_VALUE:
            raise ValueError("Value is out of bounds")

        from Crypto import Random
        self._token_string = Random.get_random_bytes(32).encode('hex')

        # Use time.time() as it gets mocked in the unit tests
        self._created = datetime.datetime.utcfromtimestamp(time.time())
        #self._created = iso8601.parse_date(self._created.isoformat())
        self._value = value

    @property
    def hash_string(self):
        try:
            return self._hash_string
        except AttributeError:
            sha512 = hashlib.sha512()
            self.logger.debug("String to hash: " + '%'.join((self['value'], self['token'], self['created'])))
            sha512.update('%'.join((self['value'], self['token'], self['created'])))
            self._hash_string = sha512.hexdigest()
        return self._hash_string

    @property
    def token_string(self):
        return self._token_string;

    @property
    def json_string(self):
        return json.dumps(dict(self))

    @property
    def value(self):
        return self._value

    @property
    def created(self):
        return self._created

    def __eq__(self, other):
        return other.hash_string == self.hash_string

    def __hash__(self):
        try:
            return self._hash
        except AttributeError:
            self._hash = int(self.hash_string, 16)
        return self._hash

    def __str__(self):
        return self.json_string

    def __repr__(self):
        return self.json_string

    def __getitem__(self, item):
        try:
            if item == 'created':
                return self.created.isoformat()
            if item == 'token':
                return self._token_string
            if item == 'hash':
                return self.hash_string
            if item == 'value':
                return "%06.02f" % self._value
            if item == 'encrypted_token':
                return self._encrypted_token
        except AttributeError:
            raise KeyError()
        raise KeyError()

    def keys(self):
        if hasattr(self, '_token_string'):
            return ('created', 'token', 'value')
        if hasattr(self, '_encrypted_token'):
            return ('created', 'hash', 'encrypted_token', 'value')
        if hasattr(self, '_hash_string'):
            return ('created', 'hash', 'value')

    def encrypted(self, cipher):
        try:
            encrypted_token_string = base64.encodestring(cipher.encrypt(self._token_string)).strip()
        except AttributeError:
            raise BadTokenFormatError("This token does not define a token and can not be encrypted")
        return Token({'created': self['created'],
                      'value': self['value'],
                      'hash': self['hash'],
                      'encrypted_token': encrypted_token_string})

