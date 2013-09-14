import sys
import nupay

tokens = nupay.read_tokens_from_file(sys.argv[1])

with nupay.SessionManager().create_session() as session:
    session.validate_tokens(tokens)
    print("Your balance is %.02f Eur"%session.credit)

