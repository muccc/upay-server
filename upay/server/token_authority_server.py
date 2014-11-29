import ConfigParser
import threading
import logging
import logging.config
import argparse

from functools import wraps
from decimal import Decimal
from jsonschema import ValidationError
from flask import Flask, jsonify, request, make_response

import nupay
import nupay.token_authority_schemas as schemas


# Program name, version and date
PROGRAM_NAME = 'UPAY Token Authority Server'
PROGRAM_VERSION = '0.1'
PROGRAM_DATE = '2014-03-30'
PROGRAM_STRING = "%s %s (%s)" % (PROGRAM_NAME, PROGRAM_VERSION, PROGRAM_DATE)

# Configure arguments and set parsing options
parser = argparse.ArgumentParser(description=PROGRAM_STRING)
parser.add_argument('-c',
                    type=str,
                    dest='config_file_name',
                    default='/etc/upay/server.conf',
                    help='Location of the configuration file')

parser.add_argument('-l',
                    type=str,
                    dest='logging_file_name',
                    default='/etc/upay/logging.ini',
                    help='Location of the log configuration file')

# Parse the arguments as defined
args = parser.parse_args()

config_file_path = args.config_file_name

config = ConfigParser.RawConfigParser()
config.read(config_file_path)
global_lock = threading.RLock()

def get_global_lock(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with global_lock:
            return f(*args, **kwargs)
    return decorated


app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'} ), 404)

@app.route('/api/v1.0/validate', methods = ['POST'])
@get_global_lock
def validate_tokens():
    try:
        schemas.validate_validate(request.json)
    except ValidationError, e:
        return make_response(jsonify(
            {'validation-error': str(e) } ), 400)

    tokens = map(nupay.Token, request.json['tokens'])
    valid_tokens = []
    try:
        token_authority = nupay.TokenAuthority(config)
        token_authority.connect()
    except:
        # Log error here ;)
        return make_response(jsonify(
            {'internal-error': 'No connection to the database'}), 504)

    for token in tokens:
        try:
            token_authority.validate_token(token)
            valid_tokens.append(token)
        except nupay.NoValidTokenFoundError:
            pass

    token_authority.commit()
    return make_response(jsonify( { 'valid_tokens': map(str, valid_tokens) } ))

@app.route('/api/v1.0/transform', methods = ['POST'])
@get_global_lock
def transform_tokens():
    try:
        schemas.validate_transform(request.json)
    except ValidationError, e:
        return make_response(jsonify(
            {'validation-error': str(e)}), 400)

    input_tokens = map(nupay.Token, request.json['input_tokens'])
    output_tokens = map(nupay.Token, request.json['output_tokens'])

    try:
        token_authority = nupay.TokenAuthority(config)
        token_authority.connect()
    except:
        # Log error here ;)
        return make_response(jsonify(
            {'internal-error': 'No connection to the database'}), 504)

    token = token_authority.merge_tokens(input_tokens)
    token_authority.split_token(token, output_tokens)
    token_authority.commit()

    return make_response(jsonify( { 'transformed_tokens': map(str, output_tokens) } ))

@app.route('/api/v1.0/create', methods = ['POST'])
@get_global_lock
def create_tokens():
    try:
        schemas.validate_create(request.json)
    except ValidationError, e:
        return make_response(jsonify(
            {'validation-error': str(e)}), 400)

    created_tokens = map(lambda value: nupay.Token(Decimal(value)), request.json['values'])
    return make_response(jsonify( { 'created_tokens': map(str, created_tokens) } ))

@app.route('/api/v1.0/status', methods = ['GET'])
@get_global_lock
def status():
    database_ok = False
    try:
        token_authority = nupay.TokenAuthority(config)
        token_authority.connect()
        database_ok = True
    except:
        pass

    return make_response(jsonify( { 'database': 'OK' if database_ok else 'DOWN' } ))


if config.getboolean('WebService', 'use_ssl'):
    from OpenSSL import SSL
    context = SSL.Context(SSL.TLSv1_2_METHOD)
    context.use_privatekey_file('test.key')
    context.use_certificate_file('test.crt')
else:
    context = None


def run():
    logging.config.fileConfig(args.logging_file_name)
    logger = logging.getLogger("token-authority-server")
    logger.info("Starting token authority server")
    app.run(debug = False, ssl_context=context)

if __name__ == '__main__':
    run()
