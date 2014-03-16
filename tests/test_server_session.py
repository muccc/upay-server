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
    config.set("Database", "db", "testtokendb")
    config.set("Database", "host", "localhost")
    config.set("Database", "port", "5432")
    config.set("Database", "user", "testuser")
    config.set("Database", "password", "fnord23")
    config.set("Database", "allow_bootstrap", "True")
    return config

class SessionManagerTest(unittest.TestCase):
    
    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()

    def test_create_session(self):
        self.session_manager = nupay.ServerSessionManager(self.config)
        session = self.session_manager.create_session()
        self.assertIsInstance(session, nupay.ServerSession)
        session.close()

    def test_create_session_manager(self):
        self.session_manager = nupay.ServerSessionManager(self.config)

    def test_create_bad_session_mamager(self):
        self.config.set("Database", "password", "fnord223")
        self.assertRaises(nupay.SessionConnectionError, nupay.ServerSessionManager, self.config)

class SessionTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        #logging.basicConfig(level=logging.ERROR)
        self.config = db_config()
        self.session_manager = nupay.ServerSessionManager(self.config)
        self.session_manager.bootstrap_db()
        session = self.session_manager.create_session()

    def tearDown(self):
        pass

    def test_bad_validation(self):
        session = self.session_manager.create_session()
        session.create_tokens(Decimal(5))
        session.close()
 
        tokens = [nupay.Token(), nupay.Token()]
        session = self.session_manager.create_session()
        credit = session.validate_tokens(tokens)
        self.assertEqual(credit, 0)
        session.close()
    
    def test_create_token(self):
        session = self.session_manager.create_session()
        session.create_tokens(Decimal(5))
        session.close()
 
    def test_good_validation(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(1))
        session.close()
        
        session = self.session_manager.create_session()
        credit = session.validate_tokens(tokens)
        self.assertEqual(credit, Decimal('1'))
        session.close()
 
    def test_double_validation(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(1))
        session.close()
        
        session = self.session_manager.create_session()
        credit = session.validate_tokens(tokens)
        self.assertEqual(credit, Decimal('1'))
        session.close()
 
        session = self.session_manager.create_session()
        credit = session.validate_tokens(tokens)
        self.assertEqual(credit, Decimal('1'))
        session.close()
       
    def test_bad_cash(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        session.close()

        session = self.session_manager.create_session()
        session.validate_tokens(tokens)
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(2.1))
        self.assertEqual(0, session.total)
        self.assertEqual(Decimal(2), session.credit)
        session.close()

    def test_good_cash(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        session.close()

        session = self.session_manager.create_session()
        session.validate_tokens(tokens)
        session.cash(Decimal(2.0))
        self.assertEqual(Decimal(2.0), session.total)
        self.assertEqual(Decimal(0), session.credit)
        session.close()

    def test_good_cash_split(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        session.close()

        session = self.session_manager.create_session()
        session.validate_tokens(tokens)
        session.cash(Decimal(1.0))
        session.cash(Decimal(0.25))
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
        self.assertEqual(Decimal(1.5), session.total)
        self.assertEqual(Decimal(0.5), session.credit)
        session.close()

    def test_rollback(self):
        session = self.session_manager.create_session()
        tokens = session.create_tokens(Decimal(2))
        session.close()

        session = self.session_manager.create_session()
        session.validate_tokens(tokens)
        session.cash(Decimal(1.0))
        tokens = (session.cash(Decimal(0.25)))
        session.rollback(tokens)
        self.assertRaises(nupay.RollbackError, session.rollback, tokens)
        session.cash(Decimal(1.0))
        self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
        self.assertEqual(Decimal(2.0), session.total)
        session.close()

if __name__ == '__main__':
    unittest.main()
