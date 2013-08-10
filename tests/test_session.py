import unittest
import mock
import logging
import ConfigParser
from  decimal import Decimal

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
        self.session_manager = nupay.SessionManager(self.config)
        with self.session_manager.create_session() as session:
            self.assertIsInstance(session, nupay.Session)

    def test_create_session_manager(self):
        self.session_manager = nupay.SessionManager(self.config)

    def test_create_bad_session_mamager(self):
        self.config.set("Database", "password", "fnord223")
        self.assertRaises(nupay.SessionConnectionError, nupay.SessionManager, self.config)

class SessionTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()
        self.session_manager = nupay.SessionManager(self.config)
        self.session_manager.bootstrap_db()

    def tearDown(self):
        pass

    def test_bad_validation(self):
        tokens = [nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)
 
        tokens = [nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            credit = session.validate_tokens(tokens)
            self.assertEqual(credit, 0)
    
    def test_add_token(self):
        tokens = [nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)
 
    def test_good_validation(self):
        tokens = [nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)
        
        with self.session_manager.create_session() as session:
            credit = session.validate_tokens(tokens)
            self.assertEqual(credit, Decimal('1'))
 
    def test_double_validation(self):
        tokens = [nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)
        
        with self.session_manager.create_session() as session:
            credit = session.validate_tokens(tokens)
            self.assertEqual(credit, Decimal('1'))
 
        with self.session_manager.create_session() as session:
            credit = session.validate_tokens(tokens)
            self.assertEqual(credit, Decimal('1'))
       
    def test_bad_cash(self):
        tokens = [nupay.Token(), nupay.Token(), nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)

        with self.session_manager.create_session() as session:
            session.validate_tokens(tokens)
            self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(2.1))
            self.assertEqual(0, session.total)
            self.assertEqual(Decimal(2), session.credit)

    def test_good_cash(self):
        tokens = [nupay.Token(), nupay.Token(), nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)

        with self.session_manager.create_session() as session:
            session.validate_tokens(tokens)
            session.cash(Decimal(2.0))
            self.assertEqual(Decimal(2.0), session.total)
            self.assertEqual(Decimal(0), session.credit)

    def test_good_cash_split(self):
        tokens = [nupay.Token(), nupay.Token(), nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)

        with self.session_manager.create_session() as session:
            session.validate_tokens(tokens)
            session.cash(Decimal(1.0))
            session.cash(Decimal(0.25))
            self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
            self.assertEqual(Decimal(1.5), session.total)
            self.assertEqual(Decimal(0.5), session.credit)

    def test_rollback(self):
        tokens = [nupay.Token(), nupay.Token(), nupay.Token(), nupay.Token()]
        with self.session_manager.create_session() as session:
            session.add_tokens(tokens)

        with self.session_manager.create_session() as session:
            session.validate_tokens(tokens)
            session.cash(Decimal(1.0))
            session.cash(Decimal(0.25))
            session.rollback()
            self.assertRaises(nupay.RollbackError, session.rollback)
            session.cash(Decimal(1.0))
            self.assertRaises(nupay.NotEnoughCreditError, session.cash, Decimal(1.0))
            self.assertEqual(Decimal(2.0), session.total)

if __name__ == '__main__':
    unittest.main()
