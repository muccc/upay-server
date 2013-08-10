import ConfigParser
import sys
import nupay

config = ConfigParser.RawConfigParser()
config.read(sys.argv[1])

tokens = nupay.read_tokens_from_file(sys.argv[2])

with nupay.SessionManager(config).create_session() as session:
    session.validate_tokens(tokens)
    print("Your balance is %.02f Eur"%session.credit)

