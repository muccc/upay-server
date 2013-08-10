import re
import hashlib
import time
import os
import logging

token_format = re.compile(r'[A-Za-z0-9]{64}\%[0-9]{10}$')

class BadTokenFormatError(Exception):
    pass


class Token(object):
    def __init__(self, token = None):
        self.logger = logging.getLogger(__name__)
        if token is None:
            t = str(int(time.time()))
            sha256 = hashlib.sha256()
            sha256.update(os.urandom(256))
            token = sha256.hexdigest()
            token += '%' + t
        
        token = token.strip()
        if token_format.match(token) is not None:    
            self._token = token
        else:
            self.logger.warning("Token %s is badly formatted"%token)
            raise BadTokenFormatError()
        
        self.logger.debug("New token: %s"%token)
        self._hash = None

 
    @property
    def hash(self):
        if self._hash is None:
            sha512 = hashlib.sha512()
            sha512.update(self._token)
            self._hash = sha512.hexdigest()
        return self._hash

    @property
    def token(self):
        return self._token;

    def __eq__(self, other):
        return other.token == self.token

    def __str__(self):
        return self.token

    def __repr__(self):
        return self.token
