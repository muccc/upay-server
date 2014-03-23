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

    def test_transform(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {u"input_tokens": [t1, t2], "output_tokens": [t1, t2]}
        nupay.token_authority_schemas.validate_transform(request)

        request = {"input_tokens": [t1], "output_tokens": [t1, t2]}
        nupay.token_authority_schemas.validate_transform(request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1]}
        nupay.token_authority_schemas.validate_transform(request)

        request = {"input_tokens": [t1], "output_tokens": [t2]}
        nupay.token_authority_schemas.validate_transform(request)

    def test_bad_transform(self):
        t1 = str(nupay.Token(value = Decimal(1)))
        t2 = str(nupay.Token(value = Decimal(1)))

        request = {"input_tokens": [t1, t1], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t1]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

        request = {"input_token": [t1, t2], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_token": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t2 + '1']}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t2[:-1]]}
        self.assertRaises(jsonschema.ValidationError, nupay.token_authority_schemas.validate_transform, request)

if __name__ == '__main__':
    unittest.main()
