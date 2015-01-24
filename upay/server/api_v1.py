from flask import make_response, jsonify, request
from jsonschema import ValidationError
from decimal import Decimal

from upay.common import Token

from . import app
from .utils import get_global_lock
from .token_authority import TokenAuthority, NoValidTokenFoundError
from . import schemas


@app.route('/api/v1.0/status', methods=['GET'])
@get_global_lock
def status():
    database_status = 'DOWN'
    return_code = 503
    try:
        token_authority = TokenAuthority(app.config)
        token_authority.connect()
        database_status = 'OK'
        return_code = 200
        token_authority.disconnect()
    except Exception as ex:
        app.log_exception(ex)

    return make_response(jsonify({'database': database_status}), return_code)


@app.route('/api/v1.0/validate', methods=['POST'])
@get_global_lock
def validate_tokens():
    try:
        schemas.validate_validate(request.json)
    except ValidationError as ex:
        app.log_exception(ex)
        return make_response(jsonify(
            {'validation-error': str(ex)}), 400)

    tokens = map(Token, request.json['tokens'])
    valid_tokens = []
    try:
        token_authority = TokenAuthority(app.config)
        token_authority.connect()
    except Exception as ex:
        app.log_exception(ex)
        return make_response(jsonify(
            {'internal-error': 'No connection to the database'}), 503)

    for token in tokens:
        try:
            token_authority.validate_token(token)
            valid_tokens.append(token)
        except NoValidTokenFoundError:
            pass

    token_authority.commit()
    return make_response(jsonify({'valid_tokens': map(str, valid_tokens)}))


@app.route('/api/v1.0/transform', methods=['POST'])
@get_global_lock
def transform_tokens():
    try:
        schemas.validate_transform(request.json)
    except ValidationError as ex:
        app.log_exception(ex)
        return make_response(jsonify(
            {'validation-error': str(ex)}), 400)

    input_tokens = map(Token, request.json['input_tokens'])
    output_tokens = map(Token, request.json['output_tokens'])

    try:
        token_authority = TokenAuthority(app.config)
        token_authority.connect()
    except Exception as ex:
        app.log_exception(ex)
        return make_response(jsonify(
            {'internal-error': 'No connection to the database'}), 503)

    token = token_authority.merge_tokens(input_tokens)
    token_authority.split_token(token, output_tokens)
    token_authority.commit()

    return make_response(jsonify({'transformed_tokens': map(str, output_tokens)}))


@app.route('/api/v1.0/create', methods=['POST'])
@get_global_lock
def create_tokens():
    try:
        schemas.validate_create(request.json)
    except ValidationError as ex:
        app.log_exception(ex)
        return make_response(jsonify(
            {'validation-error': str(ex)}), 400)

    created_tokens = map(lambda value: Token(Decimal(value)), request.json['values'])
    return make_response(jsonify({'created_tokens': map(str, created_tokens)}))
