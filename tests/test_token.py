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

class TokenTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        self._t0 = int(time.time())

    def tearDown(self):
        pass

    def test_validation(self):
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "foobar")
        token = nupay.Token("020.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%1395088098")
        self.assertEquals(token.created, datetime.datetime.utcfromtimestamp(1395088098))

        nupay.Token("000.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%1395088099")

        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "020.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%139508809")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "1000.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%139508809")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "100.00%745bfde3fde:6aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%139508809")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "00.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%139508809")

    def test_hash(self):
        token = nupay.Token("020.00%745bfde3fde06aa76be565c84a8402c94b42ddcbd86897077072910f2a3054cd%1395088098")
        self.assertEqual(token.hash_string, "b15772d0ed237646b769a568245bd7e791f549d38880f58b515be6d8e5eed73c6ff75c97744adc03def5c915f12d9374c28a33f8143a4a916db48149e0d72931")
        token = nupay.Token(value = Decimal(20))
        self.assertNotEqual(token.hash_string, "b15772d0ed237646b769a568245bd7e791f549d38880f58b515be6d8e5eed73c6ff75c97744adc03def5c915f12d9374c28a33f8143a4a916db48149e0d72931")

    @patch('time.time')
    def test_create(self, time_mock):
        time_mock.return_value = self._t0
        token1 = nupay.Token(value = Decimal(20))
        token_string = token1.token_string
        self.assertEquals(token1.created, datetime.datetime.utcfromtimestamp(self._t0))

        token2 = nupay.Token(token_string)
        self.assertEqual(token2, token1)

        token3 = nupay.Token(value = Decimal(5))

        self.assertNotEqual(token3, token1)

if __name__ == '__main__':
    unittest.main()
