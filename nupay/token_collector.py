import threading
import Queue
import time
import git
import tempfile
import os
import datetime
from decimal import Decimal
from token import Token

class Collector(object):
    def __init__(self):
        pass

    def collect_tokens(self, tokens):
        print "collecting:", tokens
        pass

import mosquitto
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
    def __init__(self, cipher, server, topic, client_id):
        self._client = mosquitto.Mosquitto(client_id)
        self._mqtt_thread = threading.Thread(target = self._run)
        self._keep_running = True
        self._topic = topic
        self._server = server
        self._token_queue = Queue.Queue()
        self._cipher = cipher
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
                encrypted = token.encrypted(self._cipher)
                self._client.publish(self._topic, str(encrypted), 2)
            except Queue.Empty:
                pass

    def collect_tokens(self, tokens):
        Collector.collect_tokens(self, tokens)
        map(self._token_queue.put, tokens)

    @property
    def connected(self):
        return self._connected

class MQTTTokenForwarder(object):
    def __init__(self, server, topic, client_id, collectors, timeout = None):
        self._client = mosquitto.Mosquitto(client_id, clean_session = False)
        self._mqtt_thread = threading.Thread(target = self._run)
        self._keep_running = True
        self._topic = topic
        self._server = server
        self._topic = topic
        self._timeout = None
        if timeout:
            self._timeout = time.time() + timeout
            self._tokens = []
        self._token_queue = Queue.Queue()
        self._collectors = collectors
        self._connect()
        self._mqtt_thread.start()
    
    def _on_message(self, mosq, obj, msg):
        token = Token(msg.payload)
        print token
        if self._timeout:
            self._tokens.append(token)
        else:
            for collector in self._collectors:
                collector.collect_tokens([token])

    def _connect(self):
        self._connected = False
        while self._connected == False:
            time.sleep(1)
            if self._timeout and time.time() > self._timeout:
                return
            try:
                rc = self._client.connect(self._server)
                if rc != 0:
                    print '_client.connect() = ', rc
                    continue

                rc = self._client.subscribe(self._topic, 2)
                if rc[0] != 0:
                    print '_client.subscribe() = ', rc
                    continue

                self._client.on_message = self._on_message
                self._connected = True

            except Exception as e:
                print e

    def stop(self):
        self._keep_running = False
        self._mqtt_thread.join()

    def _run(self):
        while self._keep_running:
            rc = self._client.loop()
            if rc != 0:
                self._connect()
            if self._timeout and time.time() > self._timeout:
                for collector in self._collectors:
                    collector.collect_tokens(self._tokens)
                self._keep_running = False
        self._client.disconnect()

    @property
    def connected(self):
        return self._connected

    def join(self):
        self._mqtt_thread.join()

import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MailCollector(Collector):
    def __init__(self, from_address, to_address, mail_server, mail_server_port = 0):
        self._from_address = from_address
        self._to_address = to_address
        self._mail_server = mail_server
        self._mail_server_port = mail_server_port

    def collect_tokens(self, tokens):
        if not tokens:
            return
        isodate = datetime.datetime.utcfromtimestamp(int(time.time())).isoformat()
        rfcdate = email.utils.formatdate(localtime = True)

        total_value = sum([token.value for token in tokens])

        text = \
'''%d Tokens collected at %s

Total value: %.02f Eur''' % (len(tokens), isodate, total_value)


        msg = MIMEMultipart()
        msg['Subject'] = 'Collected Tokens'
        msg['From'] = self._from_address
        msg['To'] = self._to_address
        msg['Date'] = rfcdate

        msg.attach(MIMEText(text))
        tokens = '\n'.join(map(str, tokens))

        tokens = MIMEText(tokens, _subtype = 'tokens')
        tokens.add_header('Content-Disposition', 'attachment', filename='tokens' + '-' + isodate)

        msg.attach(tokens)
        self._send(msg)

    def _send(self, message):
        s = smtplib.SMTP(self._mail_server, self._mail_server_port)
        s.ehlo()
        s.starttls()
        s.ehlo()
        #s.login('USERNAME@DOMAIN', 'PASSWORD')

        s.sendmail(self._from_address, [self._to_address], message.as_string())
        s.quit()

