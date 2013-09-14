import sys
import nupay

tokens = []
for i in range(int(sys.argv[1])):
    tokens.append(nupay.Token())

with nupay.SessionManager().create_session() as session:
    session.add_tokens(tokens)

for token in tokens:
    print token

