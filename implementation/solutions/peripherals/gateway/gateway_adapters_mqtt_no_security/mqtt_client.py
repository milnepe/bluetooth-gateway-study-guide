#!/usr/bin/python
"""
MQTT client for discovering BLE devices & connecting

Discover devices that are advertising:
$ mosquitto_pub -h rock-4se -t "test/gateway/discover_devices" -m '{"scantime":"3000"}'
Connect to a discovered device using its address:
$ mosquitto_pub -h rock-4se -t "test/gateway/connect_device" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'
"""

import paho.mqtt.client as mqtt
import logging
import json
import sys

from commands import CmdDiscoverDevices
from commands import CmdConnectDevice
from bt_controller import BtController
from invoker import Invoker

BROKER = 'rock-4se'
TOPIC_ROOT = "test"

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

bt_controller = BtController()
invoker = Invoker()

# def plc_lookup(topic: str) -> Plcs:
#     """Return PLC in sub-topic"""
#     sub_topic = topic.split('/')
#     try:
#         return plcs[sub_topic[1]]
#     except KeyError:
#         return None


def on_discover_devices(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/discover_devices" topic to CmdDiscoverDevices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverDevices(bt_controller, payload['scantime']))
    logging.info("Discover devices: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_connect_device(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/connect_device" topic to CmdConnectDevice"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdConnectDevice(bt_controller, payload['bdaddr']))
    logging.info("Connect device: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_message(mosq, obj, msg):
    """Callback mapping all other TOPIC_ROOT messages - no ops"""
    logging.info("Unexpected message: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def main() -> None:

    mqttc = mqtt.Client()

    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/discover_devices", on_discover_devices)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/connect_device", on_connect_device)

    mqttc.on_message = on_message
    mqttc.connect(BROKER, 1883, 60)
    mqttc.subscribe(TOPIC_ROOT + "/#", 0)

    mqttc.loop_start()

    while True:
        invoker.invoke()


if __name__ == "__main__":
    main()
