#!/usr/bin/env python
"""
Asynchronous remote client for testing MQTT / BLE gateway with Arduino Nano 33 Sense
with on board HTS221 Temp & humidity sensor

Sends Read Characteristic commands to remote sensors and waits for responses

Note:   BLE devices need to be connected using gateway commands or bluetoothctl
        Sensors dictionary needs populating with your sensor values

usage:
python -m remote_client_nano "localhost" "test/gateway"
"""

import sys
import json
import argparse
from threading import Thread
from time import sleep
from paho.mqtt import subscribe
from paho.mqtt import publish

sys.path.insert(0, "..")  # Aid location of bluetooth package
from bluetooth_api import bluetooth_utils

# Dictionary of command strings to read characteristics from BLE sensors
sensors = {
    "temperature_sensors": [
        '{"bdaddr":"9A:61:DA:87:D2:C4", "handle":"/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b"}',
    ],
    "humidity_sensors": [
        '{"bdaddr":"9A:61:DA:87:D2:C4", "handle":"/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000e"}',
    ],
}

parser = argparse.ArgumentParser()
parser.add_argument("hostname")  # broker
parser.add_argument("topic_root")  # mqtt topic root

args = parser.parse_args()
hostname = args.hostname
topic_root = args.topic_root


def send_command(host, topic_root):
    """Send each command as an MQTT message to BLE gateway"""
    while True:
        for sensor, commands in sensors.items():
            for command in commands:
                publish.single(
                    f"{topic_root}/in/read_characteristic", command, hostname=host
                )
        sleep(10)


def print_msg(client, userdata, msg):
    """Callback to print received messages from BLE gateway"""
    payload = json.loads(msg.payload)
    try:
        value = payload["value"]
        handle = payload["handle"]
        for sensor, commands in sensors.items():
            for command in commands:
                if handle in command:
                    if sensor == "temperature_sensors":
                        value = value / 100
                        print(f"{msg.topic}, {payload['bdaddr']}, Temperature: {value}\u2103")
                        break
                    if sensor == "humidity_sensors":
                        value = value / 100
                        print(f"{msg.topic}, {payload['bdaddr']}, Humidity: {value}%")
                        break
    except KeyError:
        print("Sensor reading error: ", msg.topic, msg.payload.decode("utf-8"), "\n")


def main():
    # Send commands in a separate thread
    thread = Thread(target=send_command, args=(hostname, topic_root))
    thread.start()

    print("Starting callback...\n")
    # Subscribe to all outging messges on gateway
    subscribe.callback(print_msg, f"{topic_root}/out/#", hostname=hostname)


if __name__ == "__main__":
    main()
