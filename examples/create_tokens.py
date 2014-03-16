#!/usr/bin/env python

import sys
import nupay
from decimal import Decimal
import logging

logging.basicConfig(level=logging.ERROR)

config_dir = sys.argv[1]
amount = Decimal(sys.argv[2])

with nupay.SessionManager(config_dir).create_session() as session:
    tokens = session.create_tokens(amount)[1]['transaction']['tokens']
    for token in tokens:
        print token

