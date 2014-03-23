class Collector(object):
    def __init__(self):
        pass

    def collect_tokens(self, tokens):
        print "collecting:", tokens
        pass

class MQTTCollector(Collector):
    def __init__(self, server, topic):
        pass

