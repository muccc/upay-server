import mosquitto
import threading
import Queue

class Collector(object):
    def __init__(self):
        pass

    def collect_tokens(self, tokens):
        print "collecting:", tokens
        pass

class MQTTCollector(Collector):
    def __init__(self, server, topic, client_id):
        self._client = mosquitto.Mosquitto(client_id)
        self._client.connect(server)
        self._mqtt_thread = threading.Thread(target = self._run)
        self._keep_running = True
        self._topic = topic
        self._token_queue = Queue.Queue()
        self._mqtt_thread.start()

    def stop(self):
        self._keep_running = False
        self._mqtt_thread.join()
        self._client.disconnect()

    def _run(self):
        while self._keep_running:
            self._client.loop()
            try:
                token = self._token_queue.get(block = False)
                self._client.publish(self._topic, str(token), 2)
            except Queue.Empty:
                pass

    def collect_tokens(self, tokens):
        Collector.collect_tokens(self, tokens)
        map(self._token_queue.put, tokens)
