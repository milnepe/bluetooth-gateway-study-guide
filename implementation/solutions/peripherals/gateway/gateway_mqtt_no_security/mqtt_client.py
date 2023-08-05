#!/usr/bin/python
"""
MQTT / BLE gateway client supports remote commands:
Device discovery, device connection, reading & writing characteristic and notifications


Example MQTT commands:

Discover devices that are advertising:
mosquitto_pub -h rock-4se -t "test/gateway/in/discover_devices" -m '{"scantime":"3000"}'

Connect to device using its address:
mosquitto_pub -h rock-4se -t "test/gateway/in/connect_device" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'  # 02 Thunder Sense #46565
mosquitto_pub -h rock-4se -t "test/gateway/in/connect_device" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'  # 04 Thunder Sense #32540
mosquitto_pub -h rock-4se -t "test/gateway/in/connect_device" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'  # 05 Thunderboard #51376
mosquitto_pub -h rock-4se -t "test/gateway/in/connect_device" -m '{"bdaddr":"58:8E:81:A5:4B:10"}'  # 06 Thunderboard #19216

Discover services
mosquitto_pub -h rock-4se -t "test/gateway/in/discover_services" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/discover_services" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/discover_services" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/discover_services" -m '{"bdaddr":"58:8E:81:A5:4B:10"}'

Write to LED characteristic - "UUID": "00001815-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h rock-4se -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0048", "value":"01"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0048", "value":"01"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034", "value":"01"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char0034", "value":"01"}'

Read temperature characteristic - "UUID": "00002a6e-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h rock-4se -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service001b/char0020"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}'
mosquitto_pub -h rock-4se -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service001f/char0022"}'

Notifications
Enable button notifications "UUID": "00002a56-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":1}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":1}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":1}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char002f", "command":1}'

Disable
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":0}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":0}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":0}'
mosquitto_pub -h rock-4se -t "test/gateway/in/notifications" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char002f", "command":0}'

Subscribe to outbound messages
mosquitto_sub -h rock-4se -t "test/gateway/out/#"
"""

import paho.mqtt.client as mqtt
import logging
import json
import sys

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_constants

from commands import CmdDiscoverDevices
from commands import CmdConnectDevice
from commands import CmdWriteCharacteristic
from commands import CmdDiscoverServices
from commands import CmdReadCharacteristic
from commands import CmdNotifications
from bt_controller import BtController, Notifier
from invoker import Invoker


from bluetooth import bluetooth_utils
from bluetooth import bluetooth_general
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_constants
import dbus
import dbus.mainloop.glib
from dbus import ByteArray
from threading import Thread
from threading import local
from sys import stdin, stdout
import time
import codecs
from operator import itemgetter, attrgetter

try:
    # from gi.repository import GObject
    import gi.repository.GLib
except ImportError:
    # import gobject as GObject
    print("gi.repository.GLib import not found")

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# must set main loop before acquiring SystemBus object
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
manager = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, "/"), bluetooth_constants.DBUS_OM_IFACE)
petes_str = 'Pete'

bt_controller = BtController()
invoker = Invoker()

def mainloop_task():
    """Run mainloop"""
    mainloop = gi.repository.GLib.MainLoop()
    mainloop.run()

def on_discover_devices(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/discover_devices" topic to CmdDiscoverDevices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverDevices(bt_controller, payload['scantime']))
    logging.info("Discover devices: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_connect_device(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/connect_device" topic to CmdConnectDevice"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdConnectDevice(bt_controller, payload['bdaddr']))
    logging.info("Connect device: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_write_characteristic(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/write_characteristic" topic to CmdWriteCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdWriteCharacteristic(bt_controller, payload['bdaddr'], payload['handle'], payload['value']))
    logging.info("Write Characteristic: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_discover_services(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/discover_services" topic to CmdDiscoverServices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverServices(bt_controller, payload['bdaddr']))
    logging.info("Discover Services: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_read_characteristic(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/read_characteristic" topic to CmdReadCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdReadCharacteristic(bt_controller, payload['bdaddr'], payload['handle']))
    logging.info("Read Characteristic: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_notifications(mosq, obj, msg):
    """Callback mapping TOPIC_ROOT + "/in/notifications" topic to CmdNotifications"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdNotifications(Notifier( payload['bdaddr'], payload['handle'], payload['command'])))
    logging.info("Notifications: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def on_message(mosq, obj, msg):
    """Callback mapping all other TOPIC_ROOT messages - no ops"""
    logging.info("Unexpected message: %s, %s", msg.topic, msg.payload.decode('utf-8'))


def main() -> None:

    mqttc = mqtt.Client()

    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/discover_devices", on_discover_devices)
    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/connect_device", on_connect_device)
    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/write_characteristic", on_write_characteristic)
    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/discover_services", on_discover_services)
    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/read_characteristic", on_read_characteristic)
    mqttc.message_callback_add(bluetooth_constants.TOPIC_ROOT + "/in/notifications", on_notifications)

    mqttc.on_message = on_message
    mqttc.connect(bluetooth_constants.BROKER, 1883, 60)
    mqttc.subscribe(bluetooth_constants.TOPIC_ROOT + "/in/#", 0)

    mqttc.loop_start()

    # Put mainloop in its own thread
    thread = Thread(target=mainloop_task)
    thread.daemon = True
    thread.start()


    logging.info("Client listening...")

    while True:
        invoker.invoke()


if __name__ == "__main__":
    main()
