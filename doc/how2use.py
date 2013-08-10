import nupay

token_reader = nupay.USBTokenReader()
session_manager = nupay.SessionManager(config)

while not exit_daemon:
    try:
        tokens = token_reader.read_tokens()
        #tokens = ("blabla", "blubblub")
    except nupay.NoTokensAvailable:
        time.sleep(1)
        continue

    print "read %d tokens"%len(tokens)


    with session_manager.create_session() as session:
        session.validate(tokens)

        print "your credit is %f"%session.credit
        
        while True:
            price = get_price()
            #price = Decimal(1.50)
            if not token_reader.medium_valid() or ui.user_aborted()
                break
            
            print "cashing %f euro"%(price)
            
            try:
                session.cash(price)
                try:
                    do_stuff()
                except:
                    print "oops"
                    try:
                        session.rollback()
                        print "rolled back the transaction"
                    except nupay.RollBackError:
                        print "you lost"
                print "thx"
            except nupay.NotEnoughCreditError:
                print "you do not have enough credit"

                
        print "your total is %f"%session.total
        print "your credit is %f"%session.credit
        print "bye"

