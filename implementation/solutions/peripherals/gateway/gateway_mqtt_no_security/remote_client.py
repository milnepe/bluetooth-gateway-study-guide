#!/usr/bin/python

import sys
import json
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish

from threading import Thread
from time import sleep

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_utils
from bluetooth import bluetooth_constants


try:
    host = sys.argv[1]
except IndexError:
    host = "localhost"

sensors = {'temperature_sensors': [
            '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}',
            '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}'
          ],
          'pressure_sensors': [
            '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char001e"}'
          ],
          'humidity_sensors': [
            '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0024"}'
          ]}


def send_command():
    while True:
        for sensor, commands in sensors.items():
            for command in commands:
                publish.single("test/gateway/in/read_characteristic", command, hostname=host)
        break
        sleep(5)


def print_msg(client, userdata, msg):
    print("Callback waiting...")
    payload = json.loads(msg.payload)
    value = payload['value']
    handle = payload['handle']
    for sensor, commands in sensors.items():
        for command in commands:
            if handle in command:
                if sensor == 'temperature_sensors':
                    value = bluetooth_utils.scale_hex_big_endian(value, 100)
                    print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Temperature: {value}\u2103")
                    break
                if sensor == 'pressure_sensors':
                    print(handle)
                    value = bluetooth_utils.scale_hex_big_endian(value, 1000)
                    print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Pressure: {value:.1f} mBar")
                    break
                if sensor == 'humidity_sensors':
                    print(handle)
                    value = bluetooth_utils.scale_hex_big_endian(value, 100)
                    print(f"{msg.topic}, {msg.payload.decode('utf-8')}, Humidity: {value}%")
                    break


if __name__ == '__main__':
    print("Starting Main thread...")
    thread = Thread(target=send_command)
    thread.start()

    subscribe.callback(print_msg, "test/gateway/out/#", hostname="localhost")
