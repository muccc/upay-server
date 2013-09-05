import requests
import sys
import json
import logging
from decimal import Decimal

class SessionConnectionError(Exception):
    pass

class NotEnoughCreditError(Exception):
    pass

class RollbackError(Exception):
    pass

class TimeoutError(Exception):
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
        self.delete()
    
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
        r = requests.post(self._session_uri + '/transactions', verify=verify, timeout=timeout, auth=auth, headers=headers,
                data = json.dumps({"amount": amount}))
        
        self._update()
        if r.ok:
            return r.headers['Location']
        elif r.status_code == 402:
            amount = r.json()['error']['amount'] 
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    @property
    def total(self):
        return self._total

    def rollback(self, transaction_uri):
        r = requests.delete(transaction_uri, verify=verify, timeout=timeout, auth=auth, headers=headers)
        self._update()
        if not r.ok:
            raise RollbackError('Unknown rollback error')


