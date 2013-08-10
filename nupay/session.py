import logging
import psycopg2
from decimal import Decimal

class SessionConnectionError(Exception):
    pass

class NotEnoughCreditError(Exception):
    pass

class RollbackError(Exception):
    pass


class SessionManager(object):
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.open_connection()

    def open_connection(self):
        try:
            return psycopg2.connect(
                database=self.config.get('Database', 'db'),
                host=self.config.get('Database', 'host'),
                port=self.config.getint('Database', 'port'),
                user=self.config.get('Database', 'user'),
                password=self.config.get('Database', 'password'),
                sslmode='require')
        except Exception as e:
            self.logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)
 
    def create_session(self):
        return Session(self.open_connection())

    def bootstrap_db(self):
        if self.config.get('Database','allow_bootstrap') != 'True':
            self.logger.error('Bootstrapping is disabled in the configuration')
            return

        db = self.open_connection()
        db_cur = db.cursor()
        db_cur.execute('''
            DROP TABLE IF EXISTS tokens;
            CREATE TABLE tokens (
                hash VARCHAR PRIMARY KEY,
                used DATE NULL,
                created DATE
            )
        ''')
        db.commit()
        db.close()

class Session(object):
    def __init__(self, db):
        self._logger = logging.getLogger(__name__)
        self._db = db
        self._db_cur = self._db.cursor()
        self._tokens = []
        self._total = 0
        self._cashed_tokens = []
        self._token_value = Decimal('0.5')
   
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._db.close()

    def _validate_token(self, token):
        self._db_cur.execute('SELECT hash FROM tokens WHERE used IS NULL AND hash=%s', (token.hash,))
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.info('%s is unused' % token)
            # print "FOUND UNUSED TOKEN: %s" % token
            return True
        else:
            self._logger.info('%s is used' % token)
            return False

    def _token_exists(self, token):
        self._db_cur.execute('SELECT hash FROM tokens WHERE hash=%s', (token.hash,))
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.info('%s exists' % token)
            return True
        else:
            self._logger.info('%s does not exist' % token)
            return False

    def validate_tokens(self, tokens):
        for token in tokens:
            if token not in self._tokens:
                if self._validate_token(token):
                    self._tokens.append(token)
        return self.credit

    def _add_token(self, token):
        if not self._token_exists(token):
            self._db_cur.execute('INSERT INTO tokens VALUES (%s, NULL, NOW())', (token.hash,))

    def add_tokens(self, tokens):
        for token in tokens:
            self._add_token(token)
        self._db.commit()

    @property
    def credit(self):
        return len(self._tokens) * self._token_value

    def cash(self, amount):
        amount = Decimal(amount)
        self._cashed_tokens = []
        for token in self._tokens:
            if amount <= 0:
                break
            self._logger.info('Marking %s used' % token)
            self._db_cur.execute('UPDATE tokens SET used=NOW() WHERE hash=%s and used is NULL', (token.hash,))
            if self._db_cur.rowcount == 1:
                amount -= self._token_value
                self._cashed_tokens.append(token)

        if amount <= 0:
            self._db.commit()
            self._total += len(self._cashed_tokens) * self._token_value
            map(self._tokens.remove, self._cashed_tokens)
        else:
            self._cashed_tokens = []
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    @property
    def total(self):
        return self._total

    def rollback(self):
        if len(self._cashed_tokens) == 0:
            raise RollbackError('Nothing to roll back')
        for token in self._cashed_tokens:
            self._logger.info('Marking %s unused' % token)
            self._db_cur.execute('UPDATE tokens SET used=NULL WHERE hash=%s', (token.hash,))
            if self._db_cur.rowcount != 1:
                raise RollbackError('Unknown rollback error')
        self._total -= len(self._cashed_tokens) * self._token_value
        map(self._tokens.append, self._cashed_tokens)
        self._cashed_tokens = []
        self._db.commit()



