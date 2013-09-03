import logging
import psycopg2
from session import SessionConnectionError, NotEnoughCreditError, RollbackError

from decimal import Decimal

class ServerSessionManager(object):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self.config = config
        try:
            self.open_connection()
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
        self._db_cur = self._db.cursor()
        self._token_hashes = []
        self._total = 0
        self._cashed_token_hashes = []
        self._token_value = Decimal('0.5')
   
    def close(self):
        self._db.close()
    
    @property
    def valid_token_hashes(self):
        return self._token_hashes

    @property
    def used_token_hashes(self):
        return self._cashed_token_hashes

    def _validate_token(self, token_hash):
        self._db_cur.execute('SELECT hash FROM tokens WHERE used IS NULL AND hash=%s', (token_hash,))
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.debug('%s is unused' % token_hash)
            return True
        else:
            self._logger.debug('%s is used' % token_hash)
            return False

    def _token_exists(self, token_hash):
        self._db_cur.execute('SELECT hash FROM tokens WHERE hash=%s', (token_hash))
        ret = self._db_cur.fetchone()
        self._logger.debug('fetch returned %s' % str(ret))
        if ret:
            self._logger.info('%s exists' % token_hash)
            return True
        else:
            self._logger.info('%s does not exist' % token_hash)
            return False

    def validate_token_hashes(self, token_hashes):
        for token_hash in token_hashes:
            if token_hash not in self._token_hashes:
                if self._validate_token(token_hash):
                    self._token_hashes.append(token_hash)
        return self.credit

    @property
    def credit(self):
        return len(self._token_hashes) * self._token_value

    def cash(self, amount):
        amount = Decimal(amount)
        self._cashed_token_hashes = []
        for token_hash in self._token_hashes:
            if amount <= 0:
                break
            self._logger.info('Marking %s as used' % token_hash)
            self._db_cur.execute('UPDATE tokens SET used=NOW() WHERE hash=%s and used is NULL', (token_hash,))
            self._logger.debug('Done')
            if self._db_cur.rowcount == 1:
                amount -= self._token_value
                self._cashed_token_hashes.append(token_hash)

        self._total += len(self._cashed_token_hashes) * self._token_value
        map(self._token_hashes.remove, self._cashed_token_hashes)
        
        if amount <= 0:
            self._logger.debug('committing')
            self._db.commit()
            self._logger.debug('Done')
        else:
            self._logger.debug('db rollback')
            self._rollback()
            self._cashed_token_hashes = []
            raise NotEnoughCreditError(("Missing amount: %.02f Eur"%amount, amount))

    @property
    def total(self):
        return self._total

    def _rollback(self):
        if len(self._cashed_token_hashes) == 0:
            return

        for token_hash in self._cashed_token_hashes:
            self._logger.info('Marking %s unused' % token_hash)
            self._db_cur.execute('UPDATE tokens SET used=NULL WHERE hash=%s', (token_hash,))
            if self._db_cur.rowcount != 1:
                raise RollbackError('Unknown rollback error')
        self._total -= len(self._cashed_token_hashes) * self._token_value
        map(self._token_hashes.append, self._cashed_token_hashes)
        self._cashed_token_hashes = []
        self._db.commit()


    #def _add_token(self, token_hash):
    #    if not self._token_exists(token_hash):
    #        self._db_cur.execute('INSERT INTO tokens VALUES (%s, NULL, NOW())', (token_hash,))
    #        self._wait()

    #def add_token_hashes(self, token_hashes):
    #    for token_hash in token_hashes:
    #        self._add_token(token_hash)
    #    self._db.commit() 


