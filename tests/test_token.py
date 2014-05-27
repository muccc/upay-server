import random
import unittest
import mock
import tempfile
import io
import logging
import shutil
from decimal import Decimal
import nupay
from mock import patch
import time
import datetime
import iso8601
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

class TokenTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        #self._t0 = int(time.time())
        self._key = RSA.generate(2048)
        self._encrypt = PKCS1_OAEP.new(self._key.publickey())
        self._decrypt = PKCS1_OAEP.new(self._key)
        self._t0 = time.time()

    def tearDown(self):
        pass

    def test_encrypted(self):
        token1 = nupay.Token({'value': '000.20',
                              'encrytped_token': 'jslkdjflkfj',
                              'hash': '00'*64,
                              'created': '2012-12-12 12:12:12'})

        token2 = nupay.Token('{"value": "002.00", "hash": "' + '00'*64 + '", "created": "2012-12-12 12:12:12"}')
        token3 = nupay.Token('{"value": "002.00", "token": "' + '00'*32 + '", "created": "2012-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,{'value': '000.20',
                              'encrytped_token': 'jslkdjflkfj',
                              'created': '2012-12-12 12:12:12'})

        encrypted = token3.encrypted(self._encrypt)

        self.assertRaises(nupay.BadTokenFormatError, token2.encrypted, self._encrypt)

        decrypted = nupay.Token(dict(encrypted), self._decrypt)

        self.assertEquals(token3, decrypted)

        decrypted = nupay.Token(str(encrypted), self._decrypt)

        self.assertEquals(token3, decrypted)

        encrypted2 = nupay.Token(str(encrypted))

        self.assertEquals(encrypted, encrypted2)

        self.assertTrue('token' not in encrypted)
        self.assertTrue('encrypted_token' in encrypted)

        self.assertTrue('\n' not in encrypted['encrypted_token'])

    def test_partial(self):
        token1 = nupay.Token({'value': '002.00', 'hash': '00'*64, 'created': '2012-12-12 12:12:12'})
        token2 = nupay.Token('{"value": "002.00", "hash": "' + '00'*64 + '", "created": "2012-12-12 12:12:12"}')

        self.assertEqual(token1, token2)
        self.assertEqual(token1['hash'], '00' * 64)

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, {'value': '002.00',
                              'token': '00'*32,
                              'hash': '00'*64,
                              'created': '2012-12-12 12:12:12'})

    def test_validation(self):
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "foobar")
        token = nupay.Token('{"value": "002.00", \
                            "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                            "created": "2014-12-12 12:12:12"}')

        self.assertEquals(token.created, iso8601.parse_date("2014-12-12 12:12:12", default_timezone=None))
        self.assertEquals(token['created'], "2014-12-12T12:12:12")

        self.assertEquals(token['value'], "002.00")
        self.assertEquals(token.value, Decimal("2"))

        self.assertEquals(token['token'], "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd")
        self.assertEquals(token.token_string, "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd")

        keys = []
        for key in token:
            keys.append(key)

        self.assertIn('created', keys)
        self.assertIn('token', keys)
        self.assertIn('value', keys)

        token = nupay.Token({"value": "002.00", \
                            "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                            "created": "2014-12-12 12:12:12"})

        self.assertEquals(token.created, iso8601.parse_date("2014-12-12 12:12:12", default_timezone=None))
        self.assertEquals(token['created'], "2014-12-12T12:12:12")

        self.assertEquals(token['value'], "002.00")
        self.assertEquals(token.value, Decimal("2"))

        self.assertEquals(token['token'], "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd")
        self.assertEquals(token.token_string, "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd")

        keys = []
        for key in token:
            keys.append(key)

        self.assertIn('created', keys)
        self.assertIn('token', keys)
        self.assertIn('value', keys)


        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "002.00", \
                          "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                          "created": "2014-12-32 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "002.00", \
                          "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054c", \
                          "created": "2014-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "002.00", \
                          "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054caaaaaa", \
                          "created": "2014-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "002.00", \
                          "token": "X45bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                          "created": "2014-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "02.00", \
                          "token": "X45bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                          "created": "2014-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "02.00", \
                          "token": "X45bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                          "created": "2014-12-12 12:12:12"}')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "02.00", \
                          "token": "X45bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                          "created": "2014-12-12 12:12:12"')

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token,
                          '{"value": "02.00", \
                          "token": "X45bfde3fde06aa76be565c84a8402c94b42dd", \
                          "created": "2014-12-12 12:12:12"')

        token = nupay.Token('{"value": "002.00", \
                            "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                            "created": "2014-12-12 12:12:12"}')


    def test_hash(self):
        token = nupay.Token('{"value": "002.00", \
                            "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                            "created": "2014-12-12 12:12:12"}')

        sha512 = hashlib.sha512()
        sha512.update('%'.join(("002.00", "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", "2014-12-12T12:12:12")))
        hash_string = sha512.hexdigest()
        self.assertEqual(token.hash_string, hash_string)

        token = nupay.Token(Decimal(20))
        self.assertNotEqual(token.hash_string, "b15772d0ed237646b769a568245bd7e791f549d38880f58b515be6d8e5eed73c6ff75c97744adc03def5c915f12d9374c28a33f8143a4a916db48149e0d72931")

    @patch('time.time')
    def test_create(self, time_mock):
        time_mock.return_value = self._t0
        token1 = nupay.Token(Decimal(20))
        token_string = str(token1)
        self.assertEquals(token1.created, datetime.datetime.utcfromtimestamp(self._t0))

        token2 = nupay.Token(token_string)
        self.assertEqual(token2, token1)

        token3 = nupay.Token(Decimal(20))

        self.assertNotEqual(token3, token1)

if __name__ == '__main__':
    unittest.main()
