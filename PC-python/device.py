#!/usr/bin/python3.4
import os
from enum import Enum
import logging
import paho.mqtt.client as mqtt
import datetime
from threading import Lock
from time import sleep
import sys
import json

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',)
logger = logging.getLogger('MDevice')
logger.setLevel(logging.INFO)


class StateTopic:
    """Build topic for the device."""

    def __init__(self, device_id, device_type):
        """Build the basic topic."""
        self._base_topic = 'device/{0}/{1}'.format(device_type, device_id)

    def connect(self):
        """Build connect topic."""
        return self._base_topic + "/connect"

    def disconnect(self):
        """Build disconnect topic."""
        return self._base_topic + "/disconnect"

    def set(self, value):
        """Build set topic, this topic receive value."""
        return self._base_topic + "/set/" + str(value)

    # def get(self):
        # # TODO: need to see if I need that topic
        # return self._base_topic + "/get"


class ETicketConnectionState(Enum):
    # Describe the connection of the device, if connected then it react to command
    CONNECTED = 1
    DISSCONNECTED = 2


class ECondition(Enum):
    # Describe the state of the device
    ON = 1
    OFF = 2


class Ticket:
    """To get the ticket you need to convert the object to json using dumps function."""

    """* Private variable: I am not using underline because I will create a json data."""
    """from the self variables."""
    def __init__(self, device_id, device_type, location):
        self.ticket = {
            'device_id': str(device_id),
            'device_type': str(device_type),
            'connection_status': ETicketConnectionState.CONNECTED.name,
            'location': str(location),
            'last_condition': {
                'condition': None,
                'timestamps': None,
                'timestamps_timeout': None
            }
        }

    def set_connection(self, connection):
        self.ticket['connection_status'] = connection

    def set_new_condition(self, condition, timeout=None):
        self.ticket['last_condition']['condition'] = condition.name
        self.ticket['last_condition']['timestamps'] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.ticket['last_condition']['timestamps_timeout'] = None  # TODO need to sum datetime.datetime.now()

    def get_ticket(self):
        return json.dumps(self.ticket)

    def get_will_ticket(self):
        ticket = self.ticket.copy()
        ticket['connection_status'] = ETicketConnectionState.DISSCONNECTED.name
        ticket['last_condition']['condition'] = ECondition.OFF.name
        ticket['last_condition']['timestamps'] = None
        ticket['last_condition']['timestamps_timeout'] = None
        return json.dumps(ticket)

    """
            ```JSON
                {
                    "connection_status": "off/on",
                    "type": analog_lamp, digital_lamp, ... Amp_meter.
                    "device_id": # of the device, unique, number for his type
                    "location": the location if the device
                    "last condition": {
                            "condition": last value that gas been send from the device
                            "timestamps": save the time that the last message has been sent
                            "timestamps timeout": after that time the data will not be valid anymore"
                        }
                }
            ```
    """


class MDevice(mqtt.Client):
    def __init__(self, device_id, device_type, location, ip="127.0.0.1", port=1883, user_settings=None):
        logger.info('initializing...')
        self._ip = ip
        self._port = port
        self._user_settings = user_settings
        self._device_type = device_type
        # self._keepalive = keepalive
        self._state_topic = StateTopic(device_id, device_type)  # 'device/{0}/{1}'.format(device_type, device_id)
        self._ticket = Ticket(device_id, device_type, location)
        self._ticket.set_new_condition(ECondition.ON)
        self._ping_topic = 'pings'

        self._connected = False
        # creating a lock for the above var for thread-safe reasons
        self._lock = Lock()

        super().__init__()

    def connect(self):
        logger.info('connecting...')
        if self._user_settings is not None:
            self.username_pw_set(self._user_settings['user'], self._user_settings['pass'])
        self.will_set(self._state_topic.connect(), self._ticket.get_will_ticket(), qos=2)

        # super(MDevice, self).connect(self._ip, self.port)
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
        self.publish(self._state_topic.disconnect(), 'graceful_disconnection', qos=2)
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
            print("Device is publish to {}, with the message {}".format(
                self._state_topic.connect(), self._ticket.get_ticket()))
            self.publish(self._state_topic.connect(), self._ticket.get_ticket(), qos=2)
            print("123")
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
            self.publish(self._state_topic.connect(), self._ticket.get_ticket(), qos=2)
        else:
            logger.error('unknown topic')


def run():
    print("***************************")
    print("Running Device script")
    print("***************************")
    creation_time = os.stat(__file__).st_mtime
    if (len(sys.argv) > 1):
        mdevice = MDevice(device_id=sys.argv[1], device_type="lamp", location="Living room")
    else:
        mdevice = MDevice(device_id=0, device_type="lamp", location="Living room")
    mdevice.connect()
    while creation_time == os.stat(__file__).st_mtime:
        # ... replace sleeping below with doing some useful work ...
        # logger.info('sleeping for 10 sec')
        sleep(0.1)

    try:
        # Reopen the file on update
        os.execv(__file__, [__file__] + sys.argv)
    except FileNotFoundError:
        print("ERROR: file not found", _file__)

if __name__ == '__main__':
    run()
