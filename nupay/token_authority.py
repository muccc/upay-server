import logging
import sqlalchemy
from sqlalchemy import Table, Column, DateTime, String, MetaData, select
from functools import partial

from datetime import datetime
from decimal import Decimal

from session import SessionConnectionError
from token import Token

class NoValidTokenFoundError(Exception):
    pass

class TokenAuthority(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        try:
            #self._engine = sqlalchemy.create_engine(config.get('Database', 'url'), echo = True)
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

    def transact_token(self, token):
        return self.split_token(token, (token.value, ))[0]

    def split_token(self, token, values):
        total_split_value = sum(values)
        if total_split_value != token.value:
            raise ValueError("Split value does not match token value")
        
        split_tokens = map(lambda value: Token(value = value), values)
        
        with self._connection.begin() as trans:
            self.validate_token(token)
            self.void_token(token)
            map(self.create_token, split_tokens)
            return split_tokens 
    
    def merge_tokens(self, tokens):
        total_value = sum([token.value for token in tokens])
        token = Token(value = total_value)

        with self._connection.begin() as trans:
            map(self.validate_token, tokens)
            map(self.void_token, tokens)
            self.create_token(token)
            return token

    def create_token(self, token):
        ins = self._tokens.insert().values(hash = token.hash_string, created = datetime.now())
        self._execute(ins)

    def void_token(self, token):
        with self._connection.begin() as trans:
            self.validate_token(token)
            statement = self._tokens.update().where(self._tokens.c.hash == token.hash_string).values(used = datetime.now())
            self._execute(statement)
    
    def validate_token(self, token):
        result = self._execute(select([self._tokens]).where(self._tokens.c.hash == token.hash_string).where(self._tokens.c.used == None)).fetchone()
        if result == None:
            raise NoValidTokenFoundError('Token not found')

    def _execute(self, statement):
        return self._connection.execute(statement)

