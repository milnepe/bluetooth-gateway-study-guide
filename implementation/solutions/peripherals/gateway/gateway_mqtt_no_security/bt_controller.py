import logging
import sys
import json
import dbus

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_utils
from bluetooth import bluetooth_constants

import paho.mqtt.publish as publish


class BtController:

    @staticmethod
    def publisher(topic: str, result: dict):
        json_result = json.JSONEncoder().encode(result)
        publish.single(bluetooth_constants.TOPIC_ROOT + "/out/" + topic, json_result, hostname=bluetooth_constants.BROKER)

    def discover_devices(self, scantime: str) -> None:
        """Discover devices in controller with optional timeout"""
        devices_discovered = bluetooth_gap.discover_devices(int(scantime))
        json_devices_discovered = json.JSONEncoder().encode(devices_discovered)
        logging.info("Discover devices: %s", json_devices_discovered)
        BtController.publisher("devices", json_devices_discovered)  # Publish result

    def connect_device(self, bdaddr: str) -> None:
        """Connect device using address"""
        result = {}
        rc = bluetooth_gap.connect(bdaddr)
        result['result'] = rc
        result['bdaddr'] = bdaddr
        result['cmd'] = "connect_device"
        logging.info(json.JSONEncoder().encode(result))
        BtController.publisher("connection", result)  # Publish result

    def write_characteristic(self, bdaddr: str, handle: str, value: str) -> None:
        """Write a value to the characteristic using device address"""
        result = {}
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        result['cmd'] = "write_characteristic"
        result['value'] = value
        try:
            rc = bluetooth_gatt.write_characteristic(bdaddr, handle, value)
            result['result'] = rc
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]
        logging.info(json.JSONEncoder().encode(result))
        BtController.publisher("sensor", result)  # Publish result

    def discover_services(self, bdaddr: str) -> None:
        """Discover services using device address"""
        result = {}
        result['cmd'] = "discover_services"
        try:
            services_discovered = bluetooth_gatt.get_services(bdaddr)

            for service in services_discovered:
                # rename BlueZ-specific parameter name to the more abstract 'handle'
                service['handle'] = service.pop('path')
                characteristics_discovered = bluetooth_gatt.get_characteristics(bdaddr, service['handle'])

                service['characteristics'] = characteristics_discovered
                for characteristic in characteristics_discovered:
                    characteristic['handle'] = characteristic.pop('path')
                    characteristic['service_handle'] = characteristic.pop('service_path')
                    descriptors_discovered = bluetooth_gatt.get_descriptors(bdaddr, characteristic['handle'])

                    characteristic['descriptors'] = descriptors_discovered
                    for descriptor in descriptors_discovered:
                        descriptor['handle'] = descriptor.pop('path')
                        descriptor['characteristic_handle'] = descriptor.pop('characteristic_path')

            result = json.JSONEncoder().encode(services_discovered)
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]
        logging.info(json.JSONEncoder().encode(result))
        BtController.publisher("services", result)  # Publish result

    def read_characteristic(self, bdaddr: str, handle: str):
        """Read a characteristic using device address and handle"""
        result = {}
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        result['cmd'] = "read_characteristic"
        try:
            value = bluetooth_gatt.read_characteristic(bdaddr, handle)
            result['value'] = bluetooth_utils.byteArrayToHexString(value)
            result['result'] = 0
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]
        logging.info(json.JSONEncoder().encode(result))
        BtController.publisher("sensor", result)

    @staticmethod
    def notification_received(handle, value):
        """Notifications callback"""
        result = {}
        bdaddr = handle.replace('_', ':')[20:37]  # Hack!
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        result['cmd'] = "notification_received"
        result['value'] = bluetooth_utils.byteArrayToHexString(value)
        logging.info(json.JSONEncoder().encode(result))

    def notifications(self, bdaddr: str, handle: str, command: str) -> None:
        """Handle notifications"""
        result = {}
        if command == 0:
            try:
                bluetooth_gatt.disable_notifications(bdaddr, handle)
                result['result'] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
            except dbus.exceptions.DBusException as e:
                result['result'] = e.args[0]
            logging.info("Notifications disabled: %s", json.JSONEncoder().encode(result))
        elif command == 1:
            try:
                bluetooth_gatt.enable_notifications(bdaddr, handle, BtController.notification_received)
                result['result'] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
            logging.info("Notifications enabled: %s", json.JSONEncoder().encode(result))
        else:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            logging.info("Bad command: %s", json.JSONEncoder().encode(result))