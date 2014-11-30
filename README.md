upay-server
===========

Rewrite of upay as a Flask app.

dev setup
=========

1. prepare virtualenv with `python setup.py develop`
2. initialize dev DB with `UPAY_SERVER_CONFIG="$PWD/devserver.cfg" token-authority-bootstrap-db`
3. create a few tokens with `UPAY_SERVER_CONFIG="$PWD/devserver.cfg" token-authority-create-tokens 1 5`
4. run `devserver.py`
