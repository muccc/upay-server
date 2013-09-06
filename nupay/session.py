import requests
import sys
import json
import logging
import ssl
import time

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

headers = {'content-type': 'application/json'}
auth=("matemat", "secret")
timeout=3
verify="test.crt"

class SessionManager(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        self.create_session().delete()
 
    def create_session(self):
        try:
            r = requests.post(self.config.get('API', 'URL') + self.config.get('API', 'pay_session_entry_point'),
                    verify = verify, timeout = timeout, auth= auth, headers = headers, data = json.dumps({"name": ""}))
            if not r.ok:
                raise SessionConnectionError()
            session_uri = r.json()['session']['uri']
            return Session(session_uri)
        except Exception as e:
            self._logger.warning("Can not connect to the server", exc_info=True)
            raise SessionConnectionError(e)
 

class Session(object):
    def __init__(self, session_uri):
        self._logger = logging.getLogger(__name__)
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
        r = requests.get(self._session_uri, verify=verify, timeout=timeout, auth=auth)
        if r.ok:
            self._total = r.json()['session']['total']
            self._credit = r.json()['session']['credit']
    
    def delete(self):
        r = requests.delete(self._session_uri, verify=verify, timeout=timeout, auth=auth)

    def validate_tokens(self, tokens, callback = None):
        requests.post(self._session_uri + '/tokens', verify = verify, timeout = timeout, auth = auth, headers = headers,
            data = json.dumps({"tokens": map(str,tokens)}))
        self._update()
        return self._credit

    @property
    def credit(self):
        return self._credit

    def cash(self, amount):
        amount = str(amount)
        try:
            self._in_cash = True
            r = requests.post(self._session_uri + '/transactions', verify=verify, timeout=timeout, auth=auth, headers=headers,
                    data = json.dumps({"amount": amount}))
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
            return r.headers['Location']
        elif r.status_code == 402:
            amount = r.json()['error']['amount'] 
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))
        else:
            self._logger.warning("Unknown error condition: %s %s", str(r), r.text)
            raise RuntimeError("Unknown error condition: %s %s", str(r), r.text)
            

    @property
    def total(self):
        return self._total

    def rollback(self, transaction_uri):
        r = requests.delete(transaction_uri, verify=verify, timeout=timeout, auth=auth, headers=headers)
        self._update()
        if not r.ok:
            raise RollbackError('Unknown rollback error')


