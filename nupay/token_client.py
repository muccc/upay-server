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
                data = json.dumps({"tokens": [dict(t) for t in tokens]}),
                timeout = self._timeout)

        tokens = []
        if r.ok:
            tokens = map(Token, r.json()['valid_tokens'])
        return tokens

    def merge_tokens(self, tokens):
        value = Decimal(sum([token.value for token in tokens]))
        token = Token(value)
        self.transform_tokens(tokens, [token])
        return token

    def split_token(self, token, values):
        tokens = map(Token, values)
        self.transform_tokens([token], tokens)
        return tokens

    def create_tokens(self, values):
        if len(values) == 0:
            return []

        r = self._session.post(self._session_uri + '/create',
                data = json.dumps({"values": map(lambda value: "%06.02f" % value, values)}),
                timeout = self._timeout)

        if not r.ok:
            if r.status_code == 400:
                raise SessionError("Server reported bad request: ", r.json())
            if r.status_code == 504:
                raise SessionError("Server reported no connection to the database: ", r.json())

        return map(Token, r.json()['created_tokens'])

    def transform_tokens(self, input_tokens, output_tokens):
        if input_tokens == [] and output_tokens == []:
            return []

        if input_tokens == [] or output_tokens == []:
            raise ValueError("Both lists must have at least one token in them")
        try:
            r = self._session.post(self._session_uri + '/transform',
                data = json.dumps({"input_tokens": map(str, input_tokens),
                                    "output_tokens": map(str, output_tokens)}),
                timeout = self._timeout)
        except (requests.exceptions.SSLError, ssl.SSLError) as e:
            self._logger.warning("SSLError", exc_info=True)
            if str(e.message) == "The read operation timed out":
                raise TimeoutError("Network timed out while transforming. Timestamp: %f"%time.time())
            elif str(e.message) == "The handshake operation timed out":
                raise ConnectionError("Handshake failed before cashing")
            else:
                self._logger.warning("Unknown SSL exception while cashing: %s" % str(e.message), exc_info=True)
                raise e

        if not r.ok:
            if r.status_code == 402:
                amount = r.json()['error']['amount']
                raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))
            elif r.status_code == 404:
                raise SessionError("Server reported 404: Not Found")
            elif r.status_code == 504:
                raise SessionError("Server reported no connection to the database: ", r.json())
            else:
                self._logger.warning("Unknown error condition: %s %s", str(r), r.text)
                raise RuntimeError("Unknown error condition: %s %s", str(r), r.text)

