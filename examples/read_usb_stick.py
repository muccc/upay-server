import nupay
import time
import logging

logging.basicConfig(level=logging.DEBUG)
token_reader = nupay.USBTokenReader()


while True:
    print("Waiting for purse")
    
    while True: 
        try:
            tokens = token_reader.read_tokens()
            break
        except nupay.NoTokensAvailableError:
            time.sleep(1)

    print("Read %d tokens"%len(tokens))

    print("Waiting for medium to vanish")

    while token_reader.medium_valid:
        pass

   
