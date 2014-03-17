import logging
import sqlalchemy
from sqlalchemy import Table, Column, DateTime, String, MetaData

from datetime import datetime
from decimal import Decimal

from session import SessionConnectionError
from token import Token

class TokenAuthority(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        try:
            self._engine = sqlalchemy.create_engine(config.get('Database', 'url'), echo = False)
            self.connect()
            self.disconnect()
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)
        self._init_metadata()
    
    def _init_metadata(self):
        self._metadata = MetaData()
        self._tokens = Table('tokens', self._metadata,
            Column('hash', String(Token.HASH_STRING_LENGTH), primary_key=True),
            Column('created', DateTime),
            Column('used', DateTime)
        )

    def connect(self):
        self._connection = self._engine.connect()

    def disconnect(self):
        self._connection.close()
        self._connection = None

    def bootstrap_db(self):
        if self.config.get('Database','allow_bootstrap') != 'True':
            self.logger.error('Bootstrapping is disabled in the configuration')
            return

        self._metadata.drop_all(self._engine)
        self._metadata.create_all(self._engine)

    def create_token(self, value):
        token = Token(value = value)

        self._add_token(token)
        return token

    def void_token(self, token):
        if type(token) != Token:
            raise TypeError('token must be of type <Token>')

        self._void_token(token)

    def validate_token(self, token):
        if type(token) != Token:
            raise TypeError('token must be of type <Token>')

        return self._validate_token(token)

    def _add_token(self, token):
        ins = self._tokens.insert().values(hash = token.hash_string, created = datetime.now())
        self._execute(ins)

    def _execute(self, statement):
        if self._connection is None:
            self.connect()
        return self._connection.execute(statement)

