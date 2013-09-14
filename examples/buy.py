import sys
import nupay
from decimal import Decimal
import logging

tokens = nupay.read_tokens_from_file(sys.argv[1])

logging.basicConfig(level=logging.DEBUG)

with nupay.SessionManager().create_session() as session:
    session.validate_tokens(tokens)
    try:
        session.cash(Decimal(sys.argv[2]))
    except nupay.NotEnoughCreditError as e:
        print("You need %.02f Eur extra credit for this."%e[0][1])
    print("Your total is %.02f Eur"%session.total)
    print("Your new balance is %.02f Eur"%session.credit)

