#!/usr/bin/python
"""
MQTT client for discovering BLE devices & connecting

Discover devices that are advertising:
mosquitto_pub -h localhost -t "test/gateway/discover_devices" -m '{"scantime":"3000"}'

Connect to device using its address:
mosquitto_pub -h localhost -t "test/gateway/connect_device" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'
mosquitto_pub -h localhost -t "test/gateway/connect_device" -m '{"bdaddr":"90:FD:9F:7B:7E:E0"}'
mosquitto_pub -h localhost -t "test/gateway/connect_device" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'
mosquitto_pub -h localhost -t "test/gateway/connect_device" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'

Discover services
mosquitto_pub -h localhost -t "test/gateway/discover_services" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'
mosquitto_pub -h localhost -t "test/gateway/discover_services" -m '{"bdaddr":"90:FD:9F:7B:7E:E0"}'
mosquitto_pub -h localhost -t "test/gateway/discover_services" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'
mosquitto_pub -h localhost -t "test/gateway/discover_services" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'

Write to LED characteristic - "UUID": "00001815-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/write_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0048", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/write_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service0042/char0048", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/write_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0048", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/write_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034", "value":"01"}'

Read temperature characteristic - "UUID": "00002a6e-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/read_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service001b/char0020"}'
mosquitto_pub -h localhost -t "test/gateway/read_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service001b/char0020"}'
mosquitto_pub -h localhost -t "test/gateway/read_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}'
mosquitto_pub -h localhost -t "test/gateway/read_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}'

Notifications
Enable button notifications "UUID": "00002a56-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service0042/char0043", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":1}'

Disable
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:7B:7E:E0", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7E_E0/service0042/char0043", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":0}'
"""

import paho.mqtt.client as mqtt
import logging
import json
import sys

from commands import CmdDiscoverDevices
from commands import CmdConnectDevice
from commands import CmdWriteCharacteristic
from commands import CmdDiscoverServices
from commands import CmdReadCharacteristic
from commands import CmdNotifications
from bt_controller import BtController
from invoker import Invoker

try:
    if sys.argv[1] is not null:
        BROKER = sys.argv[1]
except:
    BROKER = 'localhost'

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


def on_write_characteristic(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/write_characteristic" topic to CmdWriteCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdWriteCharacteristic(bt_controller, payload['bdaddr'], payload['handle'], payload['value']))
    logging.info("Write Characteristic: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_discover_services(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/discover_services" topic to CmdDiscoverServices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverServices(bt_controller, payload['bdaddr']))
    logging.info("Discover Services: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_read_characteristic(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/read_characteristic" topic to CmdReadCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdReadCharacteristic(bt_controller, payload['bdaddr'], payload['handle']))
    logging.info("Read Characteristic: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_notifications(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/gateway/notifications" topic to CmdNotifications"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdNotifications(bt_controller, payload['bdaddr'], payload['handle'], payload['command']))
    logging.info("Notifications: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_message(mosq, obj, msg):
    """Callback mapping all other TOPIC_ROOT messages - no ops"""
    logging.info("Unexpected message: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def main() -> None:

    mqttc = mqtt.Client()

    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/discover_devices", on_discover_devices)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/connect_device", on_connect_device)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/write_characteristic", on_write_characteristic)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/discover_services", on_discover_services)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/read_characteristic", on_read_characteristic)
    mqttc.message_callback_add(TOPIC_ROOT + "/gateway/notifications", on_notifications)

    mqttc.on_message = on_message
    mqttc.connect(BROKER, 1883, 60)
    mqttc.subscribe(TOPIC_ROOT + "/#", 0)

    mqttc.loop_start()

    logging.info("Client listening...")

    while True:
        invoker.invoke()


if __name__ == "__main__":
    main()
