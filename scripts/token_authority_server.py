#!/usr/bin/env python
from functools import wraps
import time
from decimal import Decimal
import ConfigParser
import sys
import os
import uuid
import threading

from flask import Flask, jsonify, Response, request, abort, url_for
from flask import make_response
import flask

from OpenSSL import SSL

import nupay
import nupay.token_authority_schemas as schemas

config_file_path = sys.argv[1]

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
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/v1.0/validate', methods = ['POST'])
@get_global_lock
def validate_tokens():
    schemas.validate_validate(request.json)
    
    tokens = map(nupay.Token, request.json['tokens'])
    valid_tokens = []

    token_authority = nupay.TokenAuthority(config)
    token_authority.connect()

    for token in tokens:
        try:
            token_authority.validate_token(token)
            valid_tokens.append(token)
        except nupay.NoValidTokenFoundError:
            pass

    token_authority.commit()
    return make_response(jsonify( { 'valid_tokens': map(str, valid_tokens) } ))

@app.route('/v1.0/transform', methods = ['POST'])
@get_global_lock
def transform_tokens():
    schemas.validate_transform(request.json)

    input_tokens = map(nupay.Token, request.json['input_tokens'])
    output_tokens = map(nupay.Token, request.json['output_tokens'])

    token_authority = nupay.TokenAuthority(config)
    token_authority.connect()

    token = token_authority.merge_tokens(input_tokens)
    token_authority.split_token(token, output_tokens)
    token_authority.commit()

    return make_response(jsonify( { 'transformed_tokens': map(str, output_tokens) } ))

@app.route('/v1.0/create', methods = ['POST'])
@get_global_lock
def create_tokens():
    schemas.validate_create(request.json)

    created_tokens = map(lambda value: nupay.Token(value = Decimal(value)), request.json['values'])
    return make_response(jsonify( { 'created_tokens': map(str, created_tokens) } ))

if config.getboolean('WebService', 'use_ssl'):
    context = SSL.Context(SSL.SSLv23_METHOD)
    context.use_privatekey_file('test.key')
    context.use_certificate_file('test.crt')
else:
    conext = None

if __name__ == '__main__':
    app.run(debug = True, ssl_context=context)





