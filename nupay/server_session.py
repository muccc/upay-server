import logging
import sqlalchemy
from sqlalchemy import orm
from datetime import datetime

from session import SessionConnectionError, NotEnoughCreditError, RollbackError

from decimal import Decimal
from token import Token
import server_declarative
from server_declarative import Token

class ServerSessionManager(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        try:
            self.engine = sqlalchemy.create_engine(config.get('Database', 'url'), echo = False)
            self.SessionMaker = orm.sessionmaker(bind=self.engine)
            self.SessionMaker()
            self.create_session().close()
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)

    def create_session(self):
        try:
            self.engine.connect()
            session = self.SessionMaker()
            return ServerSession(session)
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)

    def bootstrap_db(self):
        if self.config.get('Database','allow_bootstrap') != 'True':
            self.logger.error('Bootstrapping is disabled in the configuration')
            return
        server_declarative.Base.metadata.drop_all(self.engine)
        server_declarative.Base.metadata.create_all(self.engine)

class ServerSession(object):
    def __init__(self, db_session):
        self._logger = logging.getLogger(__name__)
        self._db_session = db_session
        self._valid_tokens = set()
        self._total = Decimal('0')
        self._token_value = Decimal('0.5')

    def close(self):
        self._db_session.close()

    @property
    def valid_tokens(self):
        return self._valid_tokens

    def validate_hashes(self, hashes):
        for hash in hashes:
            try:
                token = self._db_session.query(Token).filter_by(hash = hash).filter_by(used = None).one()
                self._valid_tokens.add(token)
            except:
                pass
        return self.credit

    @property
    def credit(self):
        return len(self._valid_tokens) * self._token_value

    def cash(self, amount):
        amount = Decimal(amount)
        cashed_tokens = []
        for token in self._valid_tokens:
            if amount <= 0:
                break
            self._logger.info('Marking %s as used' % token)
            if token.used == None:
                token.used = datetime.now()
                amount -= self._token_value
                cashed_tokens.append(token)

        self._total += len(cashed_tokens) * self._token_value
        map(self._valid_tokens.remove, cashed_tokens)

        if amount <= 0:
            self._db_session.commit()
            self._logger.debug('Done')
            return cashed_tokens
        else:
            self.rollback(cashed_tokens)
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    @property
    def total(self):
        return self._total

    def rollback(self, cashed_tokens):
        self._logger.debug('rollback')
        if len(cashed_tokens) == 0:
            return

        for token in cashed_tokens:
            self._logger.info('Marking %s unused' % token)
            if token.used is not None:
                token.used = None
            else:
                raise RollbackError('Unknown rollback error')

        self._total -= len(cashed_tokens) * self._token_value
        map(self._valid_tokens.add, cashed_tokens)
        self._db_session.commit()

    def create_tokens(self, amount):
        amount = Decimal(amount)
        self._logger.info("creating tokens for %s Eur", str(amount))

        tokens = []
        while amount >= (len(tokens) + 1) * self._token_value:
            token = Token()
            self._db_session.add(token)
            tokens.append(token)
        self._db_session.commit()

        return tokens

