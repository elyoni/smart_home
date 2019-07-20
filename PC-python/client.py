import logging
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep
import sys

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('MClient')
logger.setLevel(logging.INFO)


class MClient(mqtt.Client):

    def __init__(self, client_id, client_type, ip="127.0.0.1", port=1883, user_settings=None):
        logger.info('initializing...')
        self._ip = ip
        self._port = port
        self._user_settings = user_settings
        self._client_type = client_type
        #self._keepalive = keepalive
        self._state_topic = 'states/{1}/{0}'.format(client_id, client_type)
        self._ping_topic = 'pings'
        print("state_topic:", self._state_topic)
        print("ping_topic:", self._ping_topic)

        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        #super(MClient, self).__init__()
        super().__init__()

    def connect(self):
        logger.info('connecting...')
        if self._user_settings is not None:
            self.username_pw_set(self._user_settings['user'], self._user_settings['pass'])
        #self.will_set(self._state_topic, 'ungraceful_disconnection', qos=2)
        self.will_set(self._state_topic, 'disconnected', qos=2)

        #super(MClient, self).connect(self._ip, self.port)
        super().connect(self._ip, self._port)
        self.loop_start()

        while True:
            with self._lock:
                if self._connected:
                    logger.info('connected')
                    break

            sleep(1)

    def disconnect(self):
        logger.info('disconnecting...')
        with self._lock:
            # if already disconnected, don't do anything
            if not self._connected:
                return

        # inform the state server that the device will disconnect
        self.publish(self._state_topic, 'graceful_disconnection', qos=2)
        logger.info('publishing graceful_disconnection')
        # sleep for 3 secs so we receive TCP acknowledgement for the above message
        sleep(3)
        super(MClient, self).disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, client, userdata, flags, rc):
        # successful connection
        if rc == 0:
            logger.info('successful connection')

            # inform the state server that the device is connected
            self.publish(self._state_topic, 'connected', qos=2)
            # subscribe to the ping topic so when the server pings the device can respond with a pong
            self.subscribe(self._ping_topic, qos=2)
            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        logger.info('on_disconnect')
        with self._lock:
            self._connected = False

    def on_message(self, client, userdata, msg):
        # when message is received from the ping topic respond with pong ('connected' state)
        if msg.topic == self._ping_topic:
            logger.info('received ping. responding with state')
            self.publish(self._state_topic, 'connected', qos=2)


if __name__ == '__main__':
    if (len(sys.argv) > 1):
        mclient = MClient(client_id=sys.argv[1], client_type="lamp")
    else:
        mclient = MClient(client_id=0, client_type="lamp")
    mclient.connect()

    while True:
        # ... replace sleeping below with doing some useful work ...
        logger.info('sleeping for 10 sec')
        sleep(10)
