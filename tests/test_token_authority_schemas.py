import unittest
import logging
from decimal import Decimal

import upay.common
import upay.server.schemas
import jsonschema
import json


class TokenAuthorityTestsTest(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.ERROR)
        pass

    def tearDown(self):
        pass

    def test_validation(self):
        t1 = json.loads(str(upay.common.Token(Decimal(1))))
        t2 = json.loads(str(upay.common.Token(Decimal(1))))

        request = {"tokens": [t1, t2]}
        upay.server.schemas.validate_validate(request)

        request = {"tokens": [t1]}
        upay.server.schemas.validate_validate(request)

    def test_bad_validation(self):
        t1 = json.loads(str(upay.common.Token(Decimal(1))))
        t2 = json.loads(str(upay.common.Token(Decimal(1))))

        request = {"tokens": [t1, t1]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_validate, request)

        request = {"token": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_validate, request)

    def test_transform(self):
        t1 = json.loads(str(upay.common.Token(Decimal(1))))
        t2 = json.loads(str(upay.common.Token(Decimal(1))))

        request = {u"input_tokens": [t1, t2], "output_tokens": [t1, t2]}
        upay.server.schemas.validate_transform(request)

        request = {"input_tokens": [t1], "output_tokens": [t1, t2]}
        upay.server.schemas.validate_transform(request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1]}
        upay.server.schemas.validate_transform(request)

        request = {"input_tokens": [t1], "output_tokens": [t2]}
        upay.server.schemas.validate_transform(request)

    def test_bad_transform(self):
        t1 = json.loads(str(upay.common.Token(Decimal(1))))
        t2 = json.loads(str(upay.common.Token(Decimal(1))))

        request = {"input_tokens": [t1, t1], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t1]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)

        request = {"input_token": [t1, t2], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)

        request = {"input_tokens": [t1, t2], "output_token": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)
        
        t2['token'] += '1'
        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)
        
        t2['token'] = t2['token'][:-2]
        request = {"input_tokens": [t1, t2], "output_tokens": [t1, t2]}
        self.assertRaises(jsonschema.ValidationError, upay.server.schemas.validate_transform, request)

if __name__ == '__main__':
    unittest.main()
