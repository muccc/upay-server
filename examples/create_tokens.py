import ConfigParser
import sys
import nupay

config = ConfigParser.RawConfigParser()
config_file = sys.argv[1]
config.read(config_file)

with nupay.SessionManager(config).create_session() as session:
    tokens = []
    for i in range(int(sys.argv[2])):
        tokens.append(nupay.Token())
        session.add_tokens(tokens)

for token in tokens:
    print token

