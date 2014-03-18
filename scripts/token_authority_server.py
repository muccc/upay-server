#!/usr/bin/env python
from flask import Flask, jsonify, Response, request, abort, url_for
from flask import make_response
import flask
from OpenSSL import SSL
from functools import wraps
import time
from decimal import Decimal
import nupay
import ConfigParser
import sys
import os
import uuid

config_file_path = sys.argv[1]

config = ConfigParser.RawConfigParser()
config.read(config_file_path)

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('test.key')
context.use_certificate_file('test.crt')

token_authority = nupay.TokenAuthority(config)

import threading
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
def validate_tokens(session_id):
    if not request.json or not 'tokens' in request.json:
        abort(400)
    if not type(request.json['tokens']) == type([]):
        abort(400)
    
    tokens = map(nupay.Token, request.json['tokens'])
    valid_tokens = []

    for token in tokens:
        try:
            token_authority.validate_token(token)
            valid_tokens.append(token)
        except:
            pass

    return make_response(jsonify( { 'valid_tokens': map(str, valid_tokens) } ))

@app.route('/v1.0/transfer', methods = ['POST'])
@get_global_lock
def transfer_tokens(session_id):
    if not request.json or not 'tokens' in request.json:
        abort(400)
    if not type(request.json['tokens']) == type([]):
        abort(400)
    
    tokens = map(nupay.Token, request.json['tokens'])
    transfered_tokens = []

    for token in tokens:
        try:
            t = token_authority.transact_token(token)
            transfered_tokens.append(t)
        except:
            pass

    return make_response(jsonify( { 'transfered_tokens': map(str, transfered_tokens) } ))


if __name__ == '__main__':
    app.run(debug = False, ssl_context=context)





