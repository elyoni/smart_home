# Smart Home
* I am using MQTT as communication protocol
* The hard devices will be based on ESP8266 and Arduino
* Programming language: Python, C and C++


## Explanation how the system work
* general MQTT template: /device/<device_type>/device_id/<action>
#### Describing every field in the MQTT template
* device_type:
	* Lamp: analog_lamp, digital_lamp, RGB_lamp.
	* Temperature: temperature
	* Amp_meter:Amp_meter
* device_id: should me singular for his own device type
* actions:
	set: that action will be send directly to the device. with set there is two options.
        1. Simple set (only one value)
        With simple set command we have an additional field that will describe the value to set
        general MQTT set template: /device/<device_type>/device_id/set/<value>
        Device type set options:
            * analog_lamp: off, low, middle, high
            * digital_lamp: off, on
            * RGB_lamp: off, <color list> #TODO, change_color #TBD
            Topic Example:/device/analog_lamp/+/set/low
              * that example will send to all of the analog devices to set there value to low
        2. Complex set
        With Complex set command you have to send a JSON that will describe the set attribute like the start time end time.
        * JSON Example for RGB lamp:
            ```JSON
                {
                "start_time": "1.1.2019 10:12:1",
                "r": 3,
                "g": 100,
                "b": 3
                }
            ```
            Device reaction: after receiving the set command the device will update his state in the device state.
            * Make sure the device is subscribe the set topic
    get: The get action will pull the data from the device ticket(database) that is found in the server state
        * every message has timeout, from this time the message will not be send to device, the server will send an update command to device and then send the update message to the device. you can set the timeout timestamps to null if you don't need one
    disconnect: On disconnect
        gracefully: the device will send disconnect message to inform the device server that he is disconnect.
        Ungracefully: the broker will send a disconnect message to the server vi will message, the will server is configure before the user has been connected
        * the message will be empty
    Connect: The device will send a full ticket
        * General Device Ticket:
            ```JSON
                {
                    "connection": "off/on",
                    "device_type": analog_lamp, digital_lamp, ... Amp_meter.
                    "device_id": # of the device, unique, number for his type
                    "location": the location if the device
                    "last condition": {
                            "condition": last value that has been send from the device
                            "timestamps": save the time that the last message has been sent
                            "timestamps timeout": after that time the data will not be valid anymore"
                        }
                }	
            ```


# System client
## Device Server
The device server will save in a database(using TinyDB) all off the data of the device, every device will have a ticket that store all of the last information about that device.
* General Device Ticket:
	```JSON
		{
		    "connection": "off/on",
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
## Device
1. First Connection
To connected a new device to the Device Server will will need to publish '/device/<device_type>/<device_id>/connect'
            # # 2. /device/<device_type>/<device_id>/disconnect
            # # 3. /device/<device_type>/<device_id>/set
            # # 4. /device/<device_type>/<device_id>/get
            # # 5. /device/<device_type>/<device_id>/update
* TBD

# How to install
## Python package
* pip3 install tinydb   # To created and read the tickets of the devices
* pip3 install paho-mqtt    # Communication protocol between the devices
* TBD
