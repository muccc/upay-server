import requests
import sys
import json
import logging
import ssl
import time
import ConfigParser
from decimal import Decimal

from token import Token

class ConnectionError(Exception):
    pass

class TokenClient(object):
    def __init__(self, config_location = '/etc/upay'):
        self._logger = logging.getLogger(__name__)
        self._config_location = config_location
        self._read_config()
        self.create_session()
    
    def _read_config(self):
        self._config = ConfigParser.RawConfigParser()
        self._config.read(self._config_location + '/client.cfg')
        self._timeout = 5

    def create_session(self):
        try:
            self._session = requests.Session()
            self._session.verify = self._config_location + '/' + self._config.get('API', 'certificate')
            self._session.headers = {'content-type': 'application/json'}
            self._session_uri = self._config.get('API', 'URL') + '/v1.0'
        except Exception as e:
            self._logger.warning("Can not connect to the server", exc_info=True)
            raise ConnectionError(e)

    def validate_tokens(self, tokens):
        r = self._session.post( self._session_uri+ '/validate',
                data = json.dumps({"tokens": map(str, tokens)}),
                timeout = self._timeout)

        tokens = []
        if r.ok:
            tokens = map(Token, r.json()['valid_tokens'])
        return tokens

    def merge_tokens(self, tokens):
        value = Decimal(sum([token.value for token in tokens]))
        token = Token(value = value)
        self.transform_tokens(tokens, [token])
        return token

    def split_token(self, token, values):
        tokens = map(lambda value: Token(value = value), values) 
        self.transform_tokens([token], tokens)
        return tokens

    def transform_tokens(self, input_tokens, output_tokens):
        r = self._session.post(self._session_uri + '/transform',
                data = json.dumps({"input_tokens": map(str, input_tokens),
                                    "output_tokens": map(str, output_tokens)}),
                timeout = self._timeout)

        if not r.ok:
            raise RuntimeError("Could not process request")

