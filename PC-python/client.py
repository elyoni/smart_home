import logging
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep
import sys

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('MDevice')
logger.setLevel(logging.INFO)


class MDevice(mqtt.Client):

    def __init__(self, device_id, device_type, ip="127.0.0.1", port=1883, user_settings=None):
        logger.info('initializing...')
        self._ip = ip
        self._port = port
        self._user_settings = user_settings
        self._device_type = device_type
        # self._keepalive = keepalive
        self._state_topic = 'device/{0}/{1}'.format(device_type, device_id)
        self._ping_topic = 'pings'
        print("state_topic:", self._state_topic)
        print("ping_topic:", self._ping_topic)

        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        #super(MDevice, self).__init__()
        super().__init__()

    def connect(self):
        logger.info('connecting...')
        if self._user_settings is not None:
            self.username_pw_set(self._user_settings['user'], self._user_settings['pass'])
        #self.will_set(self._state_topic, 'ungraceful_disconnection', qos=2)
        self.will_set(self._state_topic, 'disconnected', qos=2)

        #super(MDevice, self).connect(self._ip, self.port)
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
        super(MDevice, self).disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, device, userdata, flags, rc):
        # successful connection
        if rc == 0:
            logger.info('successful connection')

            # inform the state server that the device is connected
            self.publish(self._state_topic, 'connected', qos=2)
            # subscribe to the ping topic so when the server pings the device can respond with a pong
            self.subscribe(self._ping_topic, qos=2)
            with self._lock:
                self._connected = True

    def on_disconnect(self, device, userdata, rc):
        logger.info('on_disconnect')
        with self._lock:
            self._connected = False

    def on_message(self, device, userdata, msg):
        # when message is received from the ping topic respond with pong ('connected' state)
        if msg.topic == self._ping_topic:
            logger.info('received ping. responding with state')
            self.publish(self._state_topic, 'connected', qos=2)


if __name__ == '__main__':
    if (len(sys.argv) > 1):
        mdevice = MDevice(device_id=sys.argv[1], device_type="lamp")
    else:
        mdevice = MDevice(device_id=0, device_type="lamp")
    mdevice.connect()

    while True:
        # ... replace sleeping below with doing some useful work ...
        logger.info('sleeping for 10 sec')
        sleep(10)
