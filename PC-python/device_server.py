#!/usr/bin/python3.4
"""This file will handle the device server."""
import os
import logging
import paho.mqtt.client as mqtt
from threading import Lock
from time import sleep
import tinydb  # import TinyDB, Query
from topic import TopicParser
logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
LOGGER = logging.getLogger('DeviceServer')
LOGGER.setLevel(logging.DEBUG)

class Database(tinydb.TinyDB):
    def __init__(self, database_file):
        self._query = tinydb.Query()
        super().__init__(database_file)

    def is_device(self, device_id, device_type):
        return self._database.search(self._query.device_id == str(device_id) &
                                     self._query.device_type == str(device_type))

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

        self._database = Database('/tmp/database.json')
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
            LOGGER.info('subscribe to device/#')
            self.subscribe('device/#', qos=2)

            # ping all devices to see if they are connected
            # # Every connected device should update there device ticket
            # # using the topic /device/<device_type>/<device_id>/update
            LOGGER.info('publish: pinging device')
            self.publish('pings', '', qos=2)

            with self._lock:
                self._connected = True

    def on_disconnect(self, client, userdata, rc):
        LOGGER.info('disconnected')

        with self._lock:
            self._connected = False

    def on_message(self, client, userdata, msg):
        _topic = TopicParser(msg.topic)
        print("New messages:", _topic._topic)
        if _topic.get_prefix() != "device":
            LOGGER.error("Unknown topic, the topic is:", _topic._topic)
        elif _topic.get_device_id() is None or\
            _topic.get_action() is None or\
            _topic.get_device_type() is None:
            LOGGER.error("not enoth field in the topic", _topic)
        else:
            # 1. /device/<device_type>/<device_id>/connect
            # 2. /device/<device_type>/<device_id>/disconnect
            # 3. /device/<device_type>/<device_id>/set - The client send set, #NOTE may be I need to dissable this option
            # 4. /device/<device_type>/<device_id>/get
            # 5. /device/<device_type>/<device_id>/update - The Device send update
            state = msg.payload
            print("****message:", state)
            LOGGER.info('the device id #{}` has been `{}`, device Type: {}'.format(_topic.get_device_id(),
                                                                                   _topic.get_action(),
                                                                                   _topic.get_device_type()))
            database_query = tinydb.Query()
            if self._database.is_device(_topic.get_device_id(), _topic.get_device_type()):
                # Found Device type and device id in the database
                # $.[connect, disconnect] Change the state if connect or disconnect
                # $.[set, update] change the condition
                # $.[get] return information to the user

                self._database.update({'state': str(state)}, database_query.device_id == str(_topic.get_device_id()))
                # print("Ticket is exists", self._database.search(database_query.device_id == str(_topic.get_device_id())))

            else:
                # $.[connect, disconnect] Create new ticket
                self._database.insert({'device_id': str(_topic.get_device_id()),
                                       'device_type': str(_topic.get_device_id()),
                                       'action': str(_topic.get_action())})  # Was state and changed to action
                # $.[set, update] Create new ticket
                # $.[get] return None or error



            # if (self._database.search(database_query.device_id == str(_topic.get_device_id()))):
                # # is exists
                # self._database.update({'state': str(state)}, database_query.device_id == str(_topic.get_device_id()))
                # print("Ticket is exists", self._database.search(database_query.device_id == str(_topic.get_device_id())))
            # else:
                # print("Ticket is not exists")

            # ... set new state for device with above device_id ...


def run():
    print("***************************")
    print("Running DeviceServer script")
    print("***************************")
    creation_time = os.stat(__file__).st_mtime
    state_server = DeviceServer()
    state_server.connect()

    while creation_time == os.stat(__file__).st_mtime:
        # ... replace sleeping below with doing some useful work ...
        # logger.info('sleeping for 1 sec')
        sleep(0.1)

    try:
        # Reopen the file on update
        os.execv(__file__, [''])
    except FileNotFoundError:
        print("ERROR: file not found", _file__)


if __name__ == '__main__':
    run()

