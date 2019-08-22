"""This file will handle the device server."""

import logging
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep
import tinydb  # import TinyDB, Query
from topic import Topic

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
LOGGER = logging.getLogger('DeviceServer')
LOGGER.setLevel(logging.INFO)


class DeviceServer(mqtt.Client):
    """The device server will handle the tickets for every device that is connected to the system."""

    def __init__(self, server_ip="127.0.0.1", server_port=1883, user_settings=None):
        LOGGER.info('initializing...')
        self._ip = server_ip
        self._port = server_port
        self._user_settings = user_settings

        # This variable make sure that I am connected to server before continue
        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        self._database = tinydb.TinyDB('/tmp/database.json')
        super().__init__()

    def connect(self):
        """To connecect to the server run this commnad."""
        LOGGER.info('connecting...')
        if self._user_settings is not None:
            # TODO In the future the connection will work ONLY with user and password
            self.username_pw_set(self._user_settings['user'], self._user_settings['pass'])
        super().connect(self._ip, self._port)

        self.loop_start()

        while True:
            with self._lock:
                if self._connected:
                    break

            sleep(1)

    def disconnect(self):
        """When the device server will dissconnect this function will run."""
        LOGGER.info('disconnecting...')
        with self._lock:
            # if already disconnected, don't do anything
            if not self._connected:
                return

        super().disconnect()

    # BELOW WE OVERRIDE CALLBACK FUNCTIONS

    def on_connect(self, client, userdata, flags, rc):
        # successful connection
        if rc == 0:
            LOGGER.info('successful connection')
            # ... set all device states to 'disconnected' ...

            # subscribe to all state channels
            # # Optional topics:
            # # 1. /device/<device_type>/<device_id>/connect
            # # 2. /device/<device_type>/<device_id>/disconnect
            # # 3. /device/<device_type>/<device_id>/set
            # # 4. /device/<device_type>/<device_id>/get
            # # 5. /device/<device_type>/<device_id>/update
            self.subscribe('device/#', qos=2)

            # ping all devices to see if they are connected
            # # Every connected device should update there device ticket
            # # using the topic /device/<device_type>/<device_id>/update
            LOGGER.info('pinging device:')
            self.publish('pings', '', qos=2)

            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        LOGGER.info('disconnected')
        with self._lock:
            self._connected = False
        print("asddasD")
    def on_message(self, client, userdata, msg):

        _topic = Topic(msg.topic)

        if _topic.get_prefix() != "device":
            LOGGER.error("Unknown message")

        # # 1. /device/<device_type>/<device_id>/connect
        # # 2. /device/<device_type>/<device_id>/disconnect
        # # 3. /device/<device_type>/<device_id>/set
        # # 4. /device/<device_type>/<device_id>/get
        # # 5. /device/<device_type>/<device_id>/update
        else:
            state = msg.payload
            LOGGER.info('the device:{}` has been `{}`, device Type: {}'.format(_topic.get_device_id(),
                                                                               _topic.get_action(),
                                                                               _topic.device_type()))
            id = tinydb.Query()
            if (self._database.search(id.device_id == str(_topic.get_device_id()))):
                # is exists
                self._database.update({'state': str(state)}, id.device_id == str(_topic.get_device_id()))
            else:
                self._database.insert({'device_id': str(_topic.get_device_id()),
                                       'device_type': str(_topic.get_device_id()),
                                       'action': str(_topic.get_action())})  # Was state and changed to action

            # ... set new state for device with above device_id ...


if __name__ == '__main__':

    state_server = DeviceServer()
    state_server.connect()

    while True:
        # ... replace sleeping below with doing some useful work ...
        # logger.info('sleeping for 1 sec')
        sleep(10)
