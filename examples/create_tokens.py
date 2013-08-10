import ConfigParser
import sys
import nupay

config = ConfigParser.RawConfigParser()
config.read(sys.argv[1])

tokens = []
for i in range(int(sys.argv[2])):
    tokens.append(nupay.Token())

with nupay.SessionManager(config).create_session() as session:
    session.add_tokens(tokens)

for token in tokens:
    print token

