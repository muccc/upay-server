import sys
import nupay

tokens = nupay.read_tokens_from_file(sys.argv[1])

token_client = nupay.TokenClient()

tokens = token_client.validate_tokens(tokens)

new_tokens = token_client.create_tokens([t.value for t in tokens])

token = token_client.transform_tokens(tokens, new_tokens)

for token in new_tokens:
    print token
