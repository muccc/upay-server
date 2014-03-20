#!/usr/bin/env python

import sys
import nupay
from decimal import Decimal
import logging
import ConfigParser

from nupay import Token

logging.basicConfig(level=logging.ERROR)

config = ConfigParser.RawConfigParser()
config_file = sys.argv[1]
config.read(config_file)

value = Decimal(sys.argv[2])
count = int(sys.argv[3])

ta = nupay.TokenAuthority(config)
ta.connect()

tokens = [Token(value = value) for x in xrange(count)]
map(ta.create_token, tokens)
ta.commit()

for token in tokens:
    print token

