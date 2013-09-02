#!/usr/bin/env python
import requests
import sys
import json

def print_session(session_uri):
    r = requests.get(session_uri, verify="test.crt", timeout=3, auth=("admin", "secret"))
    print r
    print r.text
    if not r.ok: sys.exit(1)

headers = {'content-type': 'application/json'}
r = requests.post("https://127.0.0.1:5000/v1.0/pay/sessions", verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"name": "some session"}))
print r
print r.text
if not r.ok: sys.exit(1)
session_uri = r.json()['session']['uri']

r = requests.post(session_uri + '/tokens', verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"tokens": ("foo", "bar", "baz")}))
print r
print r.text

print_session(session_uri)

r = requests.post(session_uri + '/transactions', verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"amount": 1}))
print r
print r.text

print_session(session_uri)
r = requests.post(session_uri + '/transactions', verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"amount": 1}))
print r
print r.text

print_session(session_uri)
r = requests.post(session_uri + '/transactions', verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"amount": '1'}))
print r
print r.text

print_session(session_uri)
r = requests.post(session_uri + '/transactions', verify="test.crt", timeout=3, auth=("admin", "secret"), headers=headers,
    data =json.dumps({"amount": 'a'}))
print r
print r.text



print_session(session_uri)
r = requests.delete(session_uri, verify="test.crt", timeout=3, auth=("admin", "secret"))
print r
print r.text
if not r.ok: sys.exit(1)


