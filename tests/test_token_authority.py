import unittest
import mock
import logging
import ConfigParser
from  decimal import Decimal
import sys

import nupay

def db_config():
    config = ConfigParser.RawConfigParser()
    config.add_section("Database")
    config.set("Database", "url", "sqlite:///:memory:")
    #config.set("Database", "url", "postgresql://testuser:fnord23@localhost:5432/testtokendb")
    config.set("Database", "allow_bootstrap", "True")
    return config

class TokenAuthorityConnectionTest(unittest.TestCase):
    
    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()

    def test_create_token_authority(self):
        ta = nupay.TokenAuthority(self.config)

        self.assertIsInstance(ta, nupay.TokenAuthority)

    def test_create_bad_database_uri(self):
        self.config.set("Database", "url", "postgresql://testuser:fnord233@localhost:5432/testtokendb")
        self.assertRaises(nupay.SessionConnectionError, nupay.TokenAuthority, self.config)

class TokenAuthorityTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        #logging.basicConfig(level=logging.ERROR)
        self.config = db_config()
        self._ta = nupay.TokenAuthority(self.config)
        self._ta.bootstrap_db()
        self._ta.connect()

    def tearDown(self):
        pass

    def test_create_token(self):
        t = nupay.Token(value = Decimal(2))
        self._ta.create_token(t)

    def test_void_token(self):
        t = nupay.Token(value = Decimal(2))
        self._ta.create_token(t)
        self._ta.void_token(t)
        self.assertRaises(nupay.NoValidTokenFoundError, self._ta.void_token, t)

    def test_validate_token(self):
        t = nupay.Token(value = Decimal(2))
        self._ta.create_token(t)
        self._ta.validate_token(t)
        
        t = nupay.Token(value = Decimal("5"))
        self.assertRaises(nupay.NoValidTokenFoundError, self._ta.void_token, t)
    
    def test_transact_token(self):
        t1 = nupay.Token(value = Decimal(2))
        self._ta.create_token(t1)
        t2 = self._ta.transact_token(t1)

        self.assertRaises(nupay.NoValidTokenFoundError, self._ta.void_token, t1)
        self._ta.validate_token(t2)

        self.assertEquals(t1.value, t2.value)
        self.assertNotEquals(t1, t2)

    def test_split_token(self):
        t = nupay.Token(value = Decimal(10))
        self._ta.create_token(t)

        tokens = self._ta.split_token(t, map(Decimal, (1,2,3,4)))
        
        self.assertRaises(nupay.NoValidTokenFoundError, self._ta.void_token, t)

        self.assertEquals(len(tokens), 4)
        self.assertEquals(tokens[0].value, Decimal(1))
        self.assertEquals(tokens[1].value, Decimal(2))
        self.assertEquals(tokens[2].value, Decimal(3))
        self.assertEquals(tokens[3].value, Decimal(4))

        map(self._ta.validate_token, tokens)
        
if __name__ == '__main__':
    unittest.main()
