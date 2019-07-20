import logging
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep
import tinydb # import TinyDB, Query

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('DeviceServer')
logger.setLevel(logging.INFO)

class DeviceServer(mqtt.Client):

    def __init__(self, ip="127.0.0.1", port=1883, user_settings=None):
        logger.info('initializing...')
        self._ip = ip
        self._port = port
        self._user_settings = user_settings

        # ... set all device states to 'unknown' ...
        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        self._database = tinydb.TinyDB('/tmp/database.json')
        super().__init__()

    def connect(self):
        logger.info('connecting...')
        if self._user_settings is not None:
            self.username_pw_set(self._user_settings['user'], self._user_settings['pass'])
        #super(DeviceServer, self).connect(self._ip, self.port)
        super().connect(self._ip, self._port)

        self.loop_start()

        while True:
            with self._lock:
                if self._connected:
                    break

            sleep(1)

    def disconnect(self):
        logger.info('disconnecting...')
        with self._lock:
            # if already disconnected, don't do anything
            if not self._connected:
                return

        #super(DeviceServer, self).disconnect()
        super().disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, client, userdata, flags, rc):
        # successful connection
        if rc == 0:
            logger.info('successful connection')
            # ... set all device states to 'disconnected' ...

            # subscribe to all state channels
            self.subscribe('device/#', qos=2)

            # ping all devices to see if they are connected
            ## Every connected device should update there device ticket
            ## using the topic /device/<device_type>/<device_id>/update
            logger.info('pinging device:')
            self.publish('pings', '', qos=2)

            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        logger.info('disconnected')
        with self._lock:
            self._connected = False

    def on_message(self, client, userdata, msg):
        topic_prefix, device_type, device_id = msg.topic.split('/')

        if topic_prefix == 'device':
            state = msg.payload
            logger.info('the device:`{}` has been `{}`, device Type: {}'.format(device_id, state, device_type))
            id = tinydb.Query()
            res = self._database.search(id.device_id == str(device_id))
            if (res):
                #is exists
                self._database.update({'state' : str(state)}, id.device_id == str(device_id))
            else:
                self._database.insert({'device_id' : str(device_id),
                    'device_type': str(device_type),
                    'state': str(state)})

            # ... set new state for device with above device_id ...


if __name__ == '__main__':

    state_server = DeviceServer()
    state_server.connect()

    while True:
        # ... replace sleeping below with doing some useful work ...
        # logger.info('sleeping for 1 sec')
        sleep(10)
