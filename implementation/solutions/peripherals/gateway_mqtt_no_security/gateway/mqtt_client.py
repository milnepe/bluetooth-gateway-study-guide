#!/usr/bin/env python
"""
MQTT / BLE gateway client supports remote commands:
Device discovery, device connection, reading & writing characteristic and notifications

Start the module with MQTT broker host and base topic parameters:
python -m mqtt_client 'localhost' 'test/gateway'

Example MQTT commands - issue these in a separate terminal session (change the paths addresses and handles to match your BLE devices:

Discover devices that are advertising:
mosquitto_pub -h localhost -t "test/gateway/in/discover_devices" -m '{"scantime":"3000"}'

Connect to device using its address:
mosquitto_pub -h localhost -t "test/gateway/in/connect_device" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'  # 02 Thunder Sense #46565
mosquitto_pub -h localhost -t "test/gateway/in/connect_device" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'  # 04 Thunder Sense #32540
mosquitto_pub -h localhost -t "test/gateway/in/connect_device" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'  # 05 Thunderboard #51376
mosquitto_pub -h localhost -t "test/gateway/in/connect_device" -m '{"bdaddr":"58:8E:81:A5:4B:10"}'  # 06 Thunderboard #19216

Discover services
mosquitto_pub -h localhost -t "test/gateway/in/discover_services" -m '{"bdaddr":"90:FD:9F:19:B5:E5"}'
mosquitto_pub -h localhost -t "test/gateway/in/discover_services" -m '{"bdaddr":"90:FD:9F:7B:7F:1C"}'
mosquitto_pub -h localhost -t "test/gateway/in/discover_services" -m '{"bdaddr":"84:2E:14:31:C8:B0"}'
mosquitto_pub -h localhost -t "test/gateway/in/discover_services" -m '{"bdaddr":"58:8E:81:A5:4B:10"}'

Write to LED characteristic - "UUID": "00001815-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0048", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0048", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034", "value":"01"}'
mosquitto_pub -h localhost -t "test/gateway/in/write_characteristic" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char0034", "value":"01"}'

Read temperature characteristic - "UUID": "00002a6e-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service001b/char0020"}'
mosquitto_pub -h localhost -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service001b/char0020"}'
mosquitto_pub -h localhost -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service001f/char0022"}'
mosquitto_pub -h localhost -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service001f/char0022"}'

Notifications
Enable button notifications "UUID": "00002a56-0000-1000-8000-00805f9b34fb"
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":1}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char002f", "command":1}'

Disable
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:19:B5:E5", "handle":"/org/bluez/hci0/dev_90_FD_9F_19_B5_E5/service0042/char0043", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"90:FD:9F:7B:7F:1C", "handle":"/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"84:2E:14:31:C8:B0", "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f", "command":0}'
mosquitto_pub -h localhost -t "test/gateway/in/notifications" -m '{"bdaddr":"58:8E:81:A5:4B:10", "handle":"/org/bluez/hci0/dev_58_8E_81_A5_4B_10/service002e/char002f", "command":0}'

Subscribe to outbound messages by running in a separate terminal:
mosquitto_sub -h localhost -t "test/gateway/out/#"
"""

import logging
import json
import sys
import argparse
from threading import Thread
import dbus
import dbus.mainloop.glib
import paho.mqtt.client as mqtt

sys.path.insert(0, "..")  # Aid location of bluetooth package
from bluetooth_api import bluetooth_constants

from commands import CmdDiscoverDevices
from commands import CmdConnectDevice
from commands import CmdWriteCharacteristic
from commands import CmdDiscoverServices
from commands import CmdReadCharacteristic
from commands import CmdNotifications
from bt_controller import BtController, Notifier
from invoker import Invoker

try:
    import gi.repository.GLib
except ImportError:
    # import gobject as GObject
    print("gi.repository.GLib import not found")

parser = argparse.ArgumentParser()
parser.add_argument("hostname")  # broker
parser.add_argument("topic_root")  # mqtt topic root

args = parser.parse_args()
hostname = args.hostname
topic_root = args.topic_root

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# must set main loop before acquiring SystemBus object
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
manager = dbus.Interface(
    bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, "/"),
    bluetooth_constants.DBUS_OM_IFACE,
)

bt_controller = BtController(hostname, topic_root)
invoker = Invoker()


def mainloop_task():
    """Run mainloop"""
    mainloop = gi.repository.GLib.MainLoop()
    mainloop.run()


def on_discover_devices(mosq, obj, msg):
    """Callback mapping "topic_root/in/discover_devices" topic to CmdDiscoverDevices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverDevices(bt_controller, payload["scantime"]))
    logging.info("Discover devices: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_connect_device(mosq, obj, msg):
    """Callback mapping "topic_root/in/connect_device" topic to CmdConnectDevice"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdConnectDevice(bt_controller, payload["bdaddr"]))
    logging.info("Connect device: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_write_characteristic(mosq, obj, msg):
    """Callback mapping "topic_root/in/write_characteristic" topic to CmdWriteCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(
        CmdWriteCharacteristic(
            bt_controller, payload["bdaddr"], payload["handle"], payload["value"]
        )
    )
    logging.info("Write Characteristic: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_discover_services(mosq, obj, msg):
    """Callback mapping "topic_root/in/discover_services" topic to CmdDiscoverServices"""
    payload = json.loads(msg.payload)
    invoker.set_command(CmdDiscoverServices(bt_controller, payload["bdaddr"]))
    logging.info("Discover Services: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_read_characteristic(mosq, obj, msg):
    """Callback mapping "topic_root/in/read_characteristic" topic to CmdReadCharacteristic"""
    payload = json.loads(msg.payload)
    invoker.set_command(
        CmdReadCharacteristic(bt_controller, payload["bdaddr"], payload["handle"])
    )
    logging.info("Read Characteristic: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_notifications(mosq, obj, msg):
    """Callback mapping "topic_root/in/notifications" topic to CmdNotifications"""
    payload = json.loads(msg.payload)
    invoker.set_command(
        CmdNotifications(
            Notifier(payload["bdaddr"], payload["handle"], payload["command"])
        )
    )
    logging.info("Notifications: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def on_message(mosq, obj, msg):
    """Callback mapping all other topic_root messages - no ops"""
    logging.info("Unexpected message: %s, %s", msg.topic, msg.payload.decode("utf-8"))


def main() -> None:
    """Run client"""

    mqttc = mqtt.Client()

    mqttc.message_callback_add(f"{topic_root}/in/discover_devices", on_discover_devices)
    mqttc.message_callback_add(f"{topic_root}/in/connect_device", on_connect_device)
    mqttc.message_callback_add(
        f"{topic_root}/in/write_characteristic",
        on_write_characteristic,
    )
    mqttc.message_callback_add(
        f"{topic_root}/in/discover_services", on_discover_services
    )
    mqttc.message_callback_add(
        f"{topic_root}/in/read_characteristic",
        on_read_characteristic,
    )
    mqttc.message_callback_add(f"{topic_root}/in/notifications", on_notifications)

    mqttc.on_message = on_message
    mqttc.connect(args.hostname, 1883, 60)
    mqttc.subscribe(f"{topic_root}/in/#", 0)

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
