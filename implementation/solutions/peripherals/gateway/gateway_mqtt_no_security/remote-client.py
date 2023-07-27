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


temperature_sensors = ['{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}',
                       '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}']


def send_command():
    while True:
        for t in temperature_sensors:
            publish.single("test/gateway/in/read_characteristic", t, hostname="localhost")

        sleep(2)


def print_msg(client, userdata, msg):
    payload = json.loads(msg.payload)
    value = payload['value']
    handle = payload['handle']
    for t in temperature_sensors:
        if handle in t:
            value = int(bluetooth_utils.big_to_little(value), 16) / 100
            print("%s : %s: Temperature: %.2f" % (msg.topic, msg.payload.decode('utf-8'), value))


if __name__ == '__main__':
    print("Starting Main thread...")
    thread = Thread(target=send_command)
    thread.start()

    subscribe.callback(print_msg, "test/gateway/out/#", hostname="localhost")
