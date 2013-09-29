#!/usr/bin/env python
from flask import Flask, jsonify, Response, request, abort, url_for
from flask import make_response
import flask
from OpenSSL import SSL
from functools import wraps
import time
import uuid
from decimal import Decimal
import nupay
import ConfigParser
import sys
import os

config_file_path = sys.argv[1]

config = ConfigParser.RawConfigParser()
config.read(config_file_path)

users_config_file_path = os.path.dirname(config_file_path) + \
        os.path.sep + config.get('Users', 'users_file')

users_config = ConfigParser.RawConfigParser()
users_config.read(users_config_file_path)

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('test.key')
context.use_certificate_file('test.crt')

upay_session_manager = nupay.ServerSessionManager(config)
user_manager = nupay.ServerUserManager(users_config)


def check_auth(username, password):
    if username in user_manager.users: 
        user = user_manager.users[username]
        return user_manager.check_password(user, password)
    return False

def request_authenticate():
    """Sends a 401 response that enables basic auth"""
    return make_response(jsonify({'error': 'Login required'}), 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in flask.session:
            auth = request.authorization
            if auth and check_auth(auth.username, auth.password):
                flask.session['username'] = auth.username
            else:
                return request_authenticate()
        return f(*args, **kwargs)
    return decorated

def check_session_id_and_transaction_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_id = kwargs['session_id']
        check_session_timeouts()

        if session_id not in sessions.keys():
            abort(404)
        if sessions[session_id]['owner'] != flask.session['username']:
            abort(403)
        
        if 'transaction_id' in kwargs:
            transaction_id = kwargs['transaction_id']
            if transaction_id not in sessions[session_id]['transactions']:
                abort(404)
        return f(*args, **kwargs)
    return decorated

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

sessions = {}
SESSION_TIMEOUT = 300

def remove_session(session_id):
    sessions[session_id]['database_session'].close()
    del sessions[session_id]

def get_uri_for_session(session):
    return url_for('get_session', session_id = session['id'], _external = True)

def get_uri_for_valid_tokens(session):
    return url_for('get_valid_tokens', session_id = session['id'], _external = True)

def get_uri_for_transaction(session, transaction_id):
    return url_for('get_transaction', session_id = session['id'],
            transaction_id = transaction_id, _external = True)

def make_public_session(session):
    public_fields = ('id', 'uri', 'name', 'owner', 'timeout')
    public_session = {field: session[field] for field in public_fields}
    public_session['timeout'] = int(session['timeout'] - time.time())
    
    database_session = session['database_session']
    public_session['total'] = database_session.total
    public_session['credit'] = database_session.credit

    return public_session

def make_public_transaction(transaction):
    public_fields = ('id', 'amount', 'tokens')
    public_transaction = \
            {field: transaction[field] for field in public_fields}

    public_transaction['tokens'] = \
            map(str, transaction['tokens'])

    return public_transaction

def is_token_unused(token):
    for session in sessions.values():
        if token in session['database_session'].valid_tokens:
            return False
    return True

def check_session_timeouts():
    timed_out = []
    for session_id in sessions:
        session = sessions[session_id]
        if session['timeout'] < time.time():
            timed_out.append(session_id)
    for session_id in timed_out:
        print session_id, "timed out. deleting it"
        remove_session(session_id)

def reset_session_timeout(session):
    session['timeout'] = time.time() + SESSION_TIMEOUT

@app.route('/v1.0/status', methods = ['GET'])
@get_global_lock
def get_status():
    return jsonify({'status': {'pay': {'sessions': len(sessions)}}})

@app.route('/v1.0/sessions', methods = ['POST'])
@get_global_lock
@requires_auth
def post_session():
    if not request.json or not 'name' in request.json:
        abort(400)

    session = { 'id': str(uuid.uuid4()),
                'name': request.json['name'],
                'owner': flask.session['username'],
                'database_session': 
                        upay_session_manager.create_session(),
                'transactions': {} }
    session['uri'] = get_uri_for_session(session)
    reset_session_timeout(session);
    sessions[session['id']] = session
    response = get_session(session_id=session['id'])
    response.headers['Location'] = session['uri']
    response.status_code = 201
    return response

@app.route('/v1.0/sessions/<session_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_session(session_id):
    return make_response(jsonify(
            {'session': make_public_session(sessions[session_id])}))

@app.route('/v1.0/sessions/<session_id>/keepalive', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_session_keepalive(session_id):
    session = sessions[session_id]
    reset_session_timeout(session)

    response = get_session(session_id=session_id)
    response.headers['Location'] = get_uri_for_session(session)

    return response

@app.route('/v1.0/sessions/<session_id>', methods = ['DELETE'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def delete_session(session_id):
    remove_session(session_id)
    return make_response(jsonify({}), 204)

@app.route('/v1.0/sessions/<session_id>/tokens', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_tokens(session_id):
    if not request.json or not 'tokens' in request.json:
        abort(400)
    if not type(request.json['tokens']) == type([]):
        abort(400)
    
    session = sessions[session_id]
    reset_session_timeout(session)
    tokens = map(nupay.Token,  request.json['tokens'])
    unsused_tokens = filter(is_token_unused, tokens)
    session['database_session'].validate_tokens(unsused_tokens)

    response = get_valid_tokens(session_id=session_id)
    response.headers['Location'] = get_uri_for_valid_tokens(session)
    response.status_code = 201
    return response

@app.route('/v1.0/sessions/<session_id>/valid_tokens', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_valid_tokens(session_id):
    session = sessions[session_id]
    return make_response(jsonify( { 'valid_tokens': map(str, session['database_session'].valid_tokens) } ))

@app.route('/v1.0/sessions/<session_id>/transactions', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_transaction(session_id):
    if not request.json or not 'amount' in request.json:
        abort(400)
    try:
        amount = Decimal(request.json['amount'])
    except:
        abort(400)
    
    if amount >= 0:
        if not user_manager.users[flask.session['username']].role == 'vending_machine':
            abort(403)
    else:
        if not user_manager.users[flask.session['username']].role == 'charging_station':
            abort(403)

    session = sessions[session_id]
    reset_session_timeout(session)
    transaction_id = str(uuid.uuid4())
    transaction = {'amount': amount, 'id': transaction_id}

    try:
        if amount >= 0:
            transaction['tokens'] = session['database_session'].cash(amount)
        else:
            transaction['tokens'] = session['database_session'].create_tokens(-amount)
            
        session['transactions'][transaction_id] = transaction
        
        response = get_transaction(session_id=session_id,
                transaction_id=transaction_id)
        response.headers['Location'] = get_uri_for_transaction(session,
                transaction_id)
        response.status_code = 201
        return response
    except nupay.NotEnoughCreditError as e:
        data = {'message': 'Balance too low'}
        data['info'] = e.message[0]
        data['amount'] = e.message[1]
        return make_response(jsonify({'error': data}), 402)

@app.route('/v1.0/sessions/<session_id>/transaction/<transaction_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_transaction(session_id, transaction_id):
    transaction = sessions[session_id]['transactions'][transaction_id]
    transaction = make_public_transaction(transaction)
    return make_response(jsonify({'transaction': transaction}))

@app.route('/v1.0/sessions/<session_id>/transaction/<transaction_id>', methods = ['DELETE'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def delete_transaction(session_id, transaction_id):
    session = sessions[session_id]
    reset_session_timeout(session)
    session['database_session'].rollback(
            session['transactions'][transaction_id]['tokens'])
    del session['transactions'][transaction_id]
    return make_response(jsonify({}), 204)

if __name__ == '__main__':
    app.run(debug = False, ssl_context=context)





