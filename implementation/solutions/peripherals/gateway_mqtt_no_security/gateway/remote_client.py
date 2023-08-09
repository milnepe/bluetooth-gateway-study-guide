#!/usr/bin/env python
"""
Asynchronous remote client for testing MQTT / BLE gateway
Sends Read Characteristic commands to remote sensors and waits for responses

Note: BLE devices need to be connected using gateway commands or bluetoothctl
sensors dictionary needs populating with your sensor values

usage:
python -m remote_client "localhost" "test/gateway"
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
from bluetooth_api import bluetooth_constants

# Dictionary of command strings to read characteristics from BLE sensors
sensors = {
    "temperature_sensors": [
        '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service001b/char0020"}',
        '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}',
        '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}',
        '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service001f/char0022"}',
    ],
    "pressure_sensors": [
        '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service001b/char001e"}',
        '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char001e"}',
    ],
    "humidity_sensors": [
        '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service001b/char0022"}',
        '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0022"}',
        '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0024"}',
        '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service001f/char0024"}',
    ],
}


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
                        value = bluetooth_utils.scale_hex_big_endian(value, 100)
                        # print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Temperature: {value}\u2103\n")
                        print(
                            f"{msg.topic}, {payload['bdaddr']}, Temperature: {value}\u2103"
                        )
                        break
                    if sensor == "pressure_sensors":
                        value = bluetooth_utils.scale_hex_big_endian(value, 1000)
                        # print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Pressure: {value:.1f} mBar\n")
                        print(
                            f"{msg.topic}, {payload['bdaddr']}, Pressure: {value:.1f} mBar"
                        )
                        break
                    if sensor == "humidity_sensors":
                        value = bluetooth_utils.scale_hex_big_endian(value, 100)
                        # print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Humidity: {value}%\n")
                        print(f"{msg.topic}, {payload['bdaddr']}, Humidity: {value}%")
                        break
    except KeyError:
        print("Sensor reading error: ", msg.topic, msg.payload.decode("utf-8"), "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hostname")  # broker
    parser.add_argument("topic_root")  # mqtt topic root

    args = parser.parse_args()

    thread = Thread(target=send_command, args=(args.hostname, args.topic_root))
    thread.start()

    print("Starting callback...\n")
    # Subscribe to all gateways outging messges
    subscribe.callback(print_msg, f"{args.topic_root}/out/#", hostname=args.hostname)


if __name__ == "__main__":
    main()
