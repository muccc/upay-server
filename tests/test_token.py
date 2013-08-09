import random
import unittest
import mock
import tempfile
import io
import logging
import shutil

import nupay

class TokenTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        pass

    def tearDown(self):
        pass
 
    def test_validation(self):
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "foobar")
        nupay.Token("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e3300%1375901686")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e33%1375901686")
        self.assertRaises(nupay.BadTokenFormatError, nupay.Token, "23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%13759016868")

    def test_hash(self):
        token = nupay.Token("23fff2f231992957ecf7180d3490ead21b5da8d489b71dd6e59b02a0f563e330%1375901686")
        self.assertEqual(token.hash, "db891851322ff6b04b993af03fda984f3356f64e34abaf73faf7919cae02c1f38c4cd172f6e71414cc25e7f2c331c2cdc4e176e604a2b16686eb7d528671b513")

    def test_create(self):
        token1 = nupay.Token()
        token_string = token1.token

        token2 = nupay.Token(token_string)
        self.assertEqual(token2, token1)
        
        token3 = nupay.Token()
        
        self.assertNotEqual(token3, token1)
 
if __name__ == '__main__':
    unittest.main()
