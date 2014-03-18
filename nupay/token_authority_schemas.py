from jsonschema import validate
from token import Token

_token_schema = {
    "type": "string",
    "pattern": Token.TOKEN_FORMAT
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

_validate_schema = {
     "type" : "object",
     "required": [ "tokens" ],
     "properties" : {
        "tokens" : _tokens_schema
     }
}

_split_schema = {
     "type" : "object",
     "required": [ "token", "values" ],
     "properties" : {
        "token" : _token_schema,
        "values" : {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": r'^\d{3}\.\d{2}$'
            }
        }
     }
}

_merge_schema = {
     "type" : "object",
     "required": ["tokens"],
     "properties" : {
        "tokens" : _tokens_schema
     }
}

def validate_validate(json):
    validate(json, _validate_schema)

def validate_split(json):
    validate(json, _split_schema)

def validate_merge(json):
    validate(json, _merge_schema)

