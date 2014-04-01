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

class TokenTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        #self._t0 = int(time.time())
        self._t0 = time.time()

    def tearDown(self):
        pass

    def test_validation(self):
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "foobar")
        token = nupay.Token('{"value": "002.00", \
                            "token": "745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd", \
                            "created": "2014-12-12 12:12:12"}')
        self.assertEquals(token.created, iso8601.parse_date("2014-12-12 12:12:12"))

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

        self.assertEqual(token.hash_string, '9cca6757159543f8a6e7a36d5b6ed0cc7eb35320e248834ad70c2e3a3df0f92b0342013b9510a56521ffa980efb426b85c86e70826a5bdd1668cee733ffffa49')

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
