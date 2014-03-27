import mosquitto
import threading
import Queue
import time
import git
import tempfile
import os

class Collector(object):
    def __init__(self):
        pass

    def collect_tokens(self, tokens):
        print "collecting:", tokens
        pass

class GITCollector(Collector):
    def __init__(self, url):
        self._path = tempfile.mkdtemp()
        self._repo = git.Repo.clone_from(url, self._path)
        print self._path
        self._token_file_name = 'collected_tokens'
        self._token_file = open(os.path.join(self._path, self._token_file_name), 'a')

    def collect_tokens(self, tokens):
        for token in tokens:
            self._token_file.write(str(token) + '\n')
        self._token_file.flush()
        self._repo.index.add([self._token_file_name])
        self._repo.index.commit("New tokens")
        self._repo.remotes.origin.push()

class MQTTCollector(Collector):
    def __init__(self, server, topic, client_id):
        self._client = mosquitto.Mosquitto(client_id)
        self._mqtt_thread = threading.Thread(target = self._run)
        self._keep_running = True
        self._topic = topic
        self._server = server
        self._token_queue = Queue.Queue()
        self._connect()
        self._mqtt_thread.start()

    def _connect(self):
        self._connected = False
        while self._connected == False:
            try:
                rc = self._client.connect(self._server)
                if rc == 0:
                    self._connected = True
            except Exception as e:
                print e
            time.sleep(1)

    def stop(self):
        self._keep_running = False
        self._mqtt_thread.join()
        self._client.disconnect()

    def _run(self):
        while self._keep_running:
            rc = self._client.loop()
            if rc != 0:
                self._connect()
            try:
                token = self._token_queue.get(block = False)
                self._client.publish(self._topic, str(token), 2)
            except Queue.Empty:
                pass

    def collect_tokens(self, tokens):
        Collector.collect_tokens(self, tokens)
        map(self._token_queue.put, tokens)

    @property
    def connected(self):
        return self._connected

