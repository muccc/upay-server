import sys
from decimal import Decimal

from upay.common import Token

from . import app
from .token_authority import TokenAuthority


def create_tokens():
    value = Decimal(sys.argv[1])
    count = int(sys.argv[2])

    ta = TokenAuthority(app.config)
    ta.connect()

    tokens = [Token(value) for x in xrange(count)]
    map(ta.create_token, tokens)

    for token in tokens:
        print token

    ta.commit()


def bootstrap_db():
    ta = TokenAuthority(app.config)
    ta.bootstrap_db()
