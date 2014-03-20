from jsonschema import validate
from token import Token

_token_schema = {
    "type": "string",
    "pattern": Token.TOKEN_FORMAT
}

_value_schema = {
    "type": "string",
    "pattern": r'^\d{3}\.\d{2}$'
}

_tokens_schema = {
    "type" : "array",
    "name" : "tokens",
    "items": 
        _token_schema
    ,
    "minItems": 1,
    "uniqueItems": True
}

_values_schema = {
    "type" : "array",
    "items":
        _value_schema
    ,
    "minItems": 1,
}

_validate_schema = {
     "type" : "object",
     "required": [ "tokens" ],
     "properties" : {
        "tokens" : _tokens_schema
     }
}

_transform_schema = {
     "type" : "object",
     "required": [ "input_tokens", "output_tokens"],
     "properties" : {
        "input_tokens" : _tokens_schema,
        "output_tokens" : _tokens_schema
     }
}

_create_schema = {
     "type" : "object",
     "required": [ "values"],
     "properties" : {
        "values" : _values_schema,
     }
}
def validate_validate(json):
    validate(json, _validate_schema)

def validate_transform(json):
    validate(json, _transform_schema)

def validate_create(json):
    validate(json, _create_schema)

