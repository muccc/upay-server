import logging
import psycopg2
from decimal import Decimal
import threading
import select
import time

def _wait(connection, timeout = 5):
    t0 = time.time()
    while 1:
        state = connection.poll()
        if state == psycopg2.extensions.POLL_OK:
            break
        elif state == psycopg2.extensions.POLL_WRITE:
            select.select([], [connection.fileno()], [], 1)
        elif state == psycopg2.extensions.POLL_READ:
            select.select([connection.fileno()], [], [], 1)
        else:
            raise psycopg2.OperationalError("poll() returned %s" % state)
        
        if timeout > 0:
            if time.time() - t0 > timeout:
                raise TimeoutError("Database operation timed out")
 
allow_bootstrap = False
class SessionConnectionError(Exception):
    pass

class NotEnoughCreditError(Exception):
    pass

class RollbackError(Exception):
    pass

class TimeoutError(Exception):
    pass

class SessionManager(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        global allow_bootstrap
        allow_bootstrap = self.config.get('Database','allow_bootstrap') == 'True'
        try:
            _wait(self.open_connection())
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)
 
    def open_connection(self):
        try:
            return psycopg2.connect(
                database=self.config.get('Database', 'db'),
                host=self.config.get('Database', 'host'),
                port=self.config.getint('Database', 'port'),
                user=self.config.get('Database', 'user'),
                password=self.config.get('Database', 'password'),
                async = 1,
                sslmode='require')
        except Exception as e:
            self._logger.warning("Can not connect to the database", exc_info=True)
            raise SessionConnectionError(e)
 
    def create_session(self):
        return Session(self.open_connection())

class Session(object):
    def __init__(self, db):
        self._logger = logging.getLogger(__name__)
        self._db = db
        self._wait()
        self._db_cur = self._db.cursor()
        self._wait()
        self._tokens = []
        self._total = 0
        self._cashed_tokens = []
        self._token_value = Decimal('0.5')
   
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._db.close()
    
    def _wait(self, timeout = 5):
        _wait(self._db, timeout)
    
    def _begin(self):
        self._db_cur.execute("BEGIN")
        self._wait()

    def _commit(self):
        self._db_cur.execute("COMMIT")
        self._wait()

    def _rollback(self):
        self._db_cur.execute("ROLLBACK")
        self._wait()


    def bootstrap_db(self):
        if not allow_bootstrap:
            self._logger.error('Bootstrapping is disabled in the configuration')
            return

        self._logger.info('Bootstrapping')
        self._db_cur.execute('''
            DROP TABLE IF EXISTS tokens;
            CREATE TABLE tokens (
                hash VARCHAR PRIMARY KEY,
                used DATE NULL,
                created DATE
            )
        ''')
        self._wait()

    def _validate_token(self, token):
        self._db_cur.execute('SELECT hash FROM tokens WHERE used IS NULL AND hash=%s', (token.hash,))
        self._wait()
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.debug('%s is unused' % token)
            return True
        else:
            self._logger.debug('%s is used' % token)
            return False

    def _token_exists(self, token):
        self._db_cur.execute('SELECT hash FROM tokens WHERE hash=%s', (token.hash,))
        self._wait()
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.info('%s exists' % token)
            return True
        else:
            self._logger.info('%s does not exist' % token)
            return False

    def validate_tokens(self, tokens, callback = None):
        for token in tokens:
            if token not in self._tokens:
                if self._validate_token(token):
                    self._tokens.append(token)
                    if callback:
                        callback(self)
        return self.credit

    def _add_token(self, token):
        if not self._token_exists(token):
            self._db_cur.execute('INSERT INTO tokens VALUES (%s, NULL, NOW())', (token.hash,))
            self._wait()

    def add_tokens(self, tokens):
        self._begin()
        for token in tokens:
            self._add_token(token)
        self._commit()

    @property
    def credit(self):
        return len(self._tokens) * self._token_value

    def cash(self, amount):
        amount = Decimal(amount)
        self._cashed_tokens = []
        self._begin()
        for token in self._tokens:
            if amount <= 0:
                break
            self._logger.info('Marking %s as used' % token)
            self._db_cur.execute('UPDATE tokens SET used=NOW() WHERE hash=%s and used is NULL', (token.hash,))
            self._wait()
            #    raise TimeoutError("cash execute timed out")
            self._logger.debug('Done')
            if self._db_cur.rowcount == 1:
                amount -= self._token_value
                self._cashed_tokens.append(token)

        if amount <= 0:
            self._logger.debug('committing')
            self._commit()
            self._logger.debug('Done')
            self._total += len(self._cashed_tokens) * self._token_value
            map(self._tokens.remove, self._cashed_tokens)
        else:
            self._logger.debug('db rollback')
            self._rollback()
            self._cashed_tokens = []
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    @property
    def total(self):
        return self._total

    def rollback(self):
        if len(self._cashed_tokens) == 0:
            raise RollbackError('Nothing to roll back')

        self._begin()
        for token in self._cashed_tokens:
            self._logger.info('Marking %s unused' % token)
            self._db_cur.execute('UPDATE tokens SET used=NULL WHERE hash=%s', (token.hash,))
            self._wait()
            if self._db_cur.rowcount != 1:
                raise RollbackError('Unknown rollback error')
        self._total -= len(self._cashed_tokens) * self._token_value
        map(self._tokens.append, self._cashed_tokens)
        self._cashed_tokens = []
        self._commit()



