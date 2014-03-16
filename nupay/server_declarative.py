from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import re
import hashlib
import time
import os
import logging
from datetime import datetime

Base = declarative_base()

class Token(Base):
    __tablename__ = 'tokens'

    hash = Column(String, primary_key=True)
    used = Column(DateTime)
    created = Column(DateTime)

    def __repr__(self):
        return "<Token(hash='%s', used='%s', created='%s')>" % (self.hash, self.used, self.created)

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        t = str(int(time.time()))
        sha256 = hashlib.sha256()
        sha256.update(os.urandom(256))
        token = sha256.hexdigest()
        token += '%' + t
        self.token = token.strip()
        self.logger.debug("New token: %s"%self.token)

        sha512 = hashlib.sha512()
        sha512.update(self.token)
        self.hash = sha512.hexdigest()

        self.created = datetime.now()

