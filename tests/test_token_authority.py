import unittest
import logging
from decimal import Decimal
import sys
from functools import partial
from mock import patch
import time

import upay.common
import upay.server.token_authority
import sqlalchemy.exc


def db_config():
    config = {
        'DATABASE_URL': 'sqlite:///:memory:',
        'DATABASE_ALLOW_BOOTSTRAP': True
    }
    return config


class TokenAuthorityConnectionTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        self.config = db_config()

    def test_create_token_authority(self):
        ta = upay.server.token_authority.TokenAuthority(self.config)

        self.assertIsInstance(ta, upay.server.token_authority.TokenAuthority)

    def test_create_bad_database_uri(self):
        self.config['DATABASE_URL']='postgresql://testuser:fnord233@localhost:5432/testtokendb'
        self.assertRaises(RuntimeError, upay.server.token_authority.TokenAuthority, self.config)


class TokenAuthorityTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        self.config = db_config()
        self._ta = upay.server.token_authority.TokenAuthority(self.config)
        self._ta.bootstrap_db()
        self._ta.connect()
        self._t0 = time.time()

    def tearDown(self):
        pass

    def test_create_token(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.commit()

    def test_create_token_double_insert(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.commit()
        self.assertRaises(sqlalchemy.exc.IntegrityError, self._ta.create_token, t)
        self._ta.connect()
        self._ta.void_token(t)
        self._ta.commit()
        self._ta.create_token(t)

    def test_create_token_rollback(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.rollback()
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.void_token, t)

    @patch('time.time')
    def test_insert_outdated_token(self, time_mock):
        time_mock.return_value = self._t0
        t = upay.common.Token(Decimal(2))
        time_mock.return_value = self._t0 + 120
        self.assertRaises(upay.server.token_authority.TimeoutError, self._ta.create_token, t)

    def test_void_token(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.commit()
        self._ta.void_token(t)
        self._ta.commit()
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.void_token, t)

    def test_validate_token(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.validate_token(t)

        t = upay.common.Token(Decimal("5"))
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token, t)

    def test_validate_partial_token(self):
        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)

        t2 = upay.common.Token({'value': t['value'], 'hash': t['hash'], 'created': t['created']})
        self._ta.validate_token(t2)


    @patch('hashlib.sha512')
    def test_validate_token_collision(self, sha512_mock):
        class BadSha(object):
            def __init__(self):
                pass
            def update(self, data):
                pass
            def hexdigest(self):
                return '0' * 64
        sha512_mock.return_value = BadSha()

        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)
        self._ta.validate_token(t)

        time.sleep(1)
        t = upay.common.Token(Decimal(2))
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token, t)

    @patch('hashlib.sha512')
    def test_create_token_collision(self, sha512_mock):
        class BadSha(object):
            def __init__(self):
                pass
            def update(self, data):
                pass
            def hexdigest(self):
                return '0' * 64
        sha512_mock.return_value = BadSha()

        t = upay.common.Token(Decimal(2))
        self._ta.create_token(t)

        t = upay.common.Token(Decimal(2))
        self.assertRaises(sqlalchemy.exc.IntegrityError, self._ta.create_token, t)

    def test_split_token(self):
        t = upay.common.Token(Decimal(10))
        self._ta.create_token(t)
        self._ta.commit()

        tokens = map(upay.common.Token, map(Decimal, (1, 2, 3, 4)))
        self._ta.split_token(t, tokens)

        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token, t)

        self.assertEquals(len(tokens), 4)
        self.assertEquals(tokens[0].value, Decimal(1))
        self.assertEquals(tokens[1].value, Decimal(2))
        self.assertEquals(tokens[2].value, Decimal(3))
        self.assertEquals(tokens[3].value, Decimal(4))

        map(self._ta.validate_token, tokens)

    def test_split_token_bad(self):
        t = upay.common.Token(Decimal(10))
        self._ta.create_token(t)

        tokens = map(upay.common.Token, map(Decimal, (1, 2, 3)))
        self.assertRaises(ValueError, self._ta.split_token, t, tokens)

        tokens = map(upay.common.Token, map(Decimal, (1, 2, 3, 4)))
        t = upay.common.Token(Decimal(10))
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.split_token, t, tokens)

    def test_split_token_rollback(self):
        t = upay.common.Token(Decimal(10))
        self._ta.create_token(t)
        self._ta.commit()

        tokens = map(upay.common.Token, map(Decimal, (1, 2, 3, 4)))
        self._ta.split_token(t, tokens)
        self._ta.rollback()

        map(partial(self.assertRaises, upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token), tokens)
        self._ta.validate_token(t)


    def test_merge_tokens(self):
        tokens = map(upay.common.Token, map(Decimal, (1,2,3,4)))
        map(self._ta.create_token, tokens)

        t = self._ta.merge_tokens(tokens)
        self._ta.commit()

        map(partial(self.assertRaises, upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token), tokens)
        self._ta.validate_token(t)
        self.assertEquals(t.value, Decimal(10))


    def test_merge_tokens_bad(self):
        tokens = map(upay.common.Token, map(Decimal, (1,2,3,4)))
        map(self._ta.create_token, tokens[1:])

        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.merge_tokens, tokens)

        self.assertRaises(sqlalchemy.exc.InvalidRequestError, self._ta.commit)

        # The exception also rolled back the created tokens
        map(partial(self.assertRaises, upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token), tokens)


    def test_merge_tokens_rollback(self):
        tokens = map(upay.common.Token, map(Decimal, (1,2,3,4)))
        map(self._ta.create_token, tokens)
        self._ta.commit()

        t = self._ta.merge_tokens(tokens)
        self._ta.rollback()

        map(self._ta.validate_token, tokens)
        self.assertRaises(upay.server.token_authority.NoValidTokenFoundError, self._ta.validate_token, t)

    @patch('time.time')
    def test_restore_tokens(self, time_mock):
        time_mock.return_value = self._t0
        tokens = map(upay.common.Token, map(Decimal, (1,2,3,4)))
        map(self._ta.create_token, tokens)
        self._ta.commit()

        # Some time later we tansform our tokens
        time_mock.return_value = self._t0 + 3600 * 24
        token = self._ta.merge_tokens(tokens)
        tokens2 = map(upay.common.Token, map(Decimal, (1,2,3,4)))
        self._ta.split_token(token, tokens2)
        self._ta.commit()

        # And try to roll them back...
        token = self._ta.merge_tokens(tokens2)
        self._ta.split_token(token, tokens)
        self._ta.commit()

if __name__ == '__main__':
    unittest.main()
