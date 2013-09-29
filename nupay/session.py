import requests
import sys
import json
import logging
import ssl
import time
import ConfigParser

from decimal import Decimal

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
    def __init__(self, config_location = '/etc/upay'):
        self._logger = logging.getLogger(__name__)
        self._config_location = config_location
        self._read_config()
        self.create_session().delete()
    
    def _read_config(self):
        self._config = ConfigParser.RawConfigParser()
        self._config.read(self._config_location + '/session.cfg')

    def create_session(self):
        try:
            s = requests.Session()
            s.auth = (self._config.get('API', 'username'), self._config.get('API', 'password'))
            s.verify = self._config_location + '/' + self._config.get('API', 'certificate')
            s.timeout = self._config.getint('API', 'timeout')
            s.headers = {'content-type': 'application/json'}

            r = s.post(self._config.get('API', 'URL') + self._config.get('API', 'pay_session_entry_point'),
                    data = json.dumps({"name": ""}),
                    timeout = s.timeout)

            if not r.ok:
                raise SessionConnectionError()
            session_uri = r.json()['session']['uri']
            return Session(s, session_uri)
        except Exception as e:
            self._logger.warning("Can not connect to the server", exc_info=True)
            raise SessionConnectionError(e)
 

class Session(object):
    def __init__(self, session, session_uri):
        self._logger = logging.getLogger(__name__)
        self._session = session
        self._session_uri = session_uri
        self._tokens = []
        self._total = 0
        self._cashed_tokens = []
   
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for i in range(5):
            try:
                self.delete()
                break
            except Exception as e:
                self._logger.warning("Exception while deleting the session", exc_info=True)
            time.sleep(1)
    
    def _update(self):
        r = self._session.get(self._session_uri,
                timeout = self._session.timeout)
        if r.ok:
            self._total = r.json()['session']['total']
            self._credit = r.json()['session']['credit']
    
    def delete(self):
        r = self._session.delete(self._session_uri,
                timeout = self._session.timeout)

    def validate_tokens(self, tokens, callback = None):
        self._session.post(self._session_uri + '/tokens',
                data = json.dumps({"tokens": map(str,tokens)}),
                timeout = self._session.timeout)
        self._update()
        return self._credit

    @property
    def credit(self):
        return self._credit

    def cash(self, amount):
        amount = str(amount)
        try:
            self._in_cash = True
            r = self._session.post(self._session_uri + '/transactions',
                    data = json.dumps({"amount": amount}),
                    timeout = self._session.timeout)

            self._in_cash = False
        except (requests.exceptions.SSLError, ssl.SSLError) as e:
            self._logger.warning("SSLError", exc_info=True)
            if str(e.message) == "The read operation timed out":
                raise CashTimeoutError("Network timed out while cashing. Timestamp: %f"%time.time()) 
            elif str(e.message) == "The handshake operation timed out":
                raise ConnectionError("Handshake failed before cashing") 
            else:
                self._logger.warning("Unknown SSL exception while cashing: %s" % str(e.message), exc_info=True)
                raise e
        except Exception as e:
            self._logger.warning("Unknown exception while cashing", exc_info=True)
            raise e
    
        self._update()

        if r.ok:
            if 'Location' not in r.headers:
                 raise SessionError("Missing field 'Location' in response")
            return r.headers['Location']
        elif r.status_code == 402:
            amount = r.json()['error']['amount'] 
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))
        elif r.status_code == 404:
            raise SessionError("Server reported 404: Not Found")
        else:
            self._logger.warning("Unknown error condition: %s %s", str(r), r.text)
            raise RuntimeError("Unknown error condition: %s %s", str(r), r.text)
            

    @property
    def total(self):
        return self._total

    def rollback(self, transaction_uri):
        r = self._session.delete(transaction_uri,
                timeout = self._session.timeout)
        self._update()
        if not r.ok:
            raise RollbackError('Unknown rollback error')


