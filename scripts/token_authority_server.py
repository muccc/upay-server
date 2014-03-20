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

token_authority = nupay.TokenAuthority(config)
token_authority.connect()

global_lock = threading.RLock()

def get_global_lock(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with global_lock:
            return f(*args, **kwargs)
    return decorated


app = Flask(__name__)

app.secret_key = str(uuid.uuid4())

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/v1.0/validate', methods = ['POST'])
@get_global_lock
def validate_tokens():
    schemas.validate_validate(request.json)
    
    tokens = map(nupay.Token, request.json['tokens'])
    valid_tokens = []

    for token in tokens:
        try:
            token_authority.validate_token(token)
            valid_tokens.append(token)
        except nupay.NoValidTokenFoundError:
            pass

    return make_response(jsonify( { 'valid_tokens': map(str, valid_tokens) } ))

@app.route('/v1.0/merge', methods = ['POST'])
@get_global_lock
def merge_tokens():
    schemas.validate_merge(request.json)
    
    tokens = map(nupay.Token, request.json['tokens'])

    merged_token = token_authority.merge_tokens(tokens)

    return make_response(jsonify( { 'merged_token': str(merged_token) } ))


@app.route('/v1.0/split', methods = ['POST'])
@get_global_lock
def split_tokens():
    schemas.validate_split(request.json)

    token = nupay.Token(request.json['token'])
    values = map(Decimal, request.json['values'])

    split_tokens = map(lambda value: nupay.Token(value = value), values)
    token_authority.split_token(token, split_tokens)

    return make_response(jsonify( { 'split_tokens': map(str, split_tokens) } ))

if config.getboolean('WebService', 'use_ssl'):
    context = SSL.Context(SSL.SSLv23_METHOD)
    context.use_privatekey_file('test.key')
    context.use_certificate_file('test.crt')
else:
    conext = None

if __name__ == '__main__':
    app.run(debug = True, ssl_context=context)





