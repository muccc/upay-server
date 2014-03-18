import random
import unittest
import mock
import tempfile
import io
import logging
import shutil
from decimal import Decimal

import nupay
import nupay.token_authority_schemas
import jsonschema

class TokenAuthorityTestsTest(unittest.TestCase):

    def setUp(self):
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.ERROR)
        pass

    def tearDown(self):
        pass
 
    def test_validation(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"tokens": [t1, t2]}
        nupay.token_authority_schemas.validate_validate(request)

        request = {"tokens": [t1]}
        nupay.token_authority_schemas.validate_validate(request)

    def test_bad_validation(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"tokens": [t1, t1]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_validate, request)

        request = {"token": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_validate, request)

    def test_merge(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"tokens": [t1, t2]}
        nupay.token_authority_schemas.validate_merge(request)

        request = {"tokens": [t1]}
        nupay.token_authority_schemas.validate_merge(request)

    def test_bad_merge(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"tokens": [t1, t1]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_merge, request)

        request = {"token": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_merge, request)

        request = {"token": [t1, t2 + '1']}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_merge, request)

        request = {"token": [t1, t2[:-1]]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_merge, request)

    def test_split(self):
        t1 = str(nupay.Token(value = Decimal(1)))

        request = {"token": t1, "values": ["001.02"]}
        nupay.token_authority_schemas.validate_split(request)

        request = {"token": t1, "values": ["001.02", "003.04"]}
        nupay.token_authority_schemas.validate_split(request)

    def test_bad_split(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"token": [t1, t2], "values": ["001.02", "003.04"]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": [1, 2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": [1.01, 2.04]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": ["x"]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": ["1.000"]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": ["99.99x"]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

        request = {"token": t1, "values": ["9999.99"]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_split, request)

if __name__ == '__main__':
    unittest.main()
