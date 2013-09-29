import sys
import nupay
from decimal import Decimal
#import logging

#logging.basicConfig(level=logging.DEBUG)
#tokens = []
#for i in range(int(sys.argv[1])):
#    tokens.append(nupay.Token())

amount = Decimal(sys.argv[1])

tokens = []
with nupay.SessionManager().create_session() as session:
    tokens = session.create_tokens(amount)[1]['transaction']['tokens']

for token in tokens:
    print token

