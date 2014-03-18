import sys
import nupay

tokens = nupay.read_tokens_from_file(sys.argv[1])

token_client = nupay.TokenClient()

tokens = token_client.validate_tokens(tokens)

values = [token.value for token in tokens]

token = token_client.merge_tokens(tokens)

tokens = token_client.split_token(token, values)

for token in tokens:
    print token
