#!/usr/bin/env python
from flask import Flask, jsonify, Response, request, abort, url_for
from flask import make_response
from OpenSSL import SSL
from functools import wraps
import time
import uuid
from decimal import Decimal

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('test.key')
context.use_certificate_file('test.crt')

def check_auth(username, password):
    if username == 'admin' and password == 'secret':
        return True
    return username == 'admin2' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(jsonify({'error': 'Login required'}), 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_session_id_and_transaction_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        print kwargs
        session_id = kwargs['session_id']
        check_session_timeouts()

        if session_id not in sessions.keys():
            abort(404)
        if sessions[session_id]['owner'] != request.authorization.username: 
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


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

sessions = {}
SESSION_TIMEOUT = 300

def remove_session(session_id):
    del sessions[session_id]

def get_uri_for_session(session):
    return url_for('get_session', session_id = session['id'], _external = True)

def get_uri_for_valid_tokens(session):
    return url_for('get_valid_tokens', session_id = session['id'], _external = True)

def get_uri_for_transaction(session, transaction_id):
    return url_for('get_transaction', session_id = session['id'],
            transaction_id = transaction_id, _external = True)

def make_public_session(session):
    public_fields = ('id', 'name', 'owner', 'timeout', 'balance', 'total')
    public_session = {}
    for field in session:
        if field in public_fields:
            public_session[field] = session[field]
        if field == 'id':
            public_session['uri'] = get_uri_for_session(session)
        elif field == 'timeout':
            public_session['timeout'] = int(public_session['timeout'] - time.time())
    return public_session

def is_token_unused(token):
    for session in sessions.values():
        if token in session['valid_tokens']:
            return False
        if token in session['used_tokens']:
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
            
@app.route('/v1.0/status', methods = ['GET'])
@get_global_lock
def get_status():
    return jsonify( { 'status': {'pay': {'sessions': len(sessions)}} } )

@app.route('/v1.0/pay/sessions', methods = ['POST'])
@get_global_lock
@requires_auth
def post_session():
    if not request.json or not 'name' in request.json:
        abort(400)

    id = str(uuid.uuid4())
    session = {'id': id, 'name': request.json['name'], 'owner': request.authorization.username,
                'timeout': time.time() + SESSION_TIMEOUT,
                'balance': Decimal(0), 'total': Decimal(0), 'valid_tokens': [], 'used_tokens': [], 'transactions': {}}
    sessions[id] = session
    location = get_uri_for_session(session)

    return jsonify( { 'session': make_public_session(session) } ), 201, {'Location': location}

@app.route('/v1.0/pay/sessions/<session_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_session(session_id):
    return jsonify({'session': make_public_session(sessions[session_id])})

@app.route('/v1.0/pay/sessions/<session_id>', methods = ['DELETE'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def delete_session(session_id):
    remove_session(session_id)
    return jsonify({}), 204

@app.route('/v1.0/pay/sessions/<session_id>/tokens', methods = ['POST'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def post_tokens(session_id):
    if not request.json or not 'tokens' in request.json:
        abort(400)
    if not type(request.json['tokens']) == type(list):
        abort(400)

    session = sessions[session_id]
    for token in request.json['tokens']:
        if is_token_unused(token):
            session['valid_tokens'].append(token)
            session['balance'] += Decimal(0.5)

    location = get_uri_for_valid_tokens(session)
    return jsonify( { 'valid_tokens': session['valid_tokens'] } ), 201, {'Location': location}

@app.route('/v1.0/pay/sessions/<session_id>/valid_tokens', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_valid_tokens(session_id):
    session = sessions[session_id]
    return jsonify({'valid_tokens': session['valid_tokens']})

@app.route('/v1.0/pay/sessions/<session_id>/used_tokens', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_used_tokens(session_id):
    session = sessions[session_id]
    return jsonify({'used_tokens': session['used_tokens']})


@app.route('/v1.0/pay/sessions/<session_id>/transactions', methods = ['POST'])
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

    session = sessions[session_id]
    if session['balance'] >= amount:
        transaction_id = str(uuid.uuid4())
        transaction = {'amount': amount, 'id': transaction_id}
        session['transactions'][transaction_id] = transaction
        session['balance'] -= amount
        session['total'] += amount
        location = get_uri_for_transaction(session, transaction_id)
        return jsonify( { 'transaction': transaction } ), 201, {'Location': location}
    else:
        return jsonify({'error': 'Balance too low'}), 402

@app.route('/v1.0/pay/sessions/<session_id>/transaction/<transaction_id>', methods = ['GET'])
@get_global_lock
@requires_auth
@check_session_id_and_transaction_id
def get_transaction(session_id, transaction_id):
    transaction = sessions[session_id]['transactions'][transaction_id]
    return jsonify({'transaction': transaction})

if __name__ == '__main__':
    app.run(debug = True, ssl_context=context)





