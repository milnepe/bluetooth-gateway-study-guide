import logging
import sys
import json
import dbus
import central
from pprint import pprint
from time import sleep


sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_utils
from bluetooth import bluetooth_constants

dongle = central.BluezProxy(central.ADAPTER_PATH, central.BLUEZ_ADAPTER)


class BtController:

    def discover_devices(self, scantime: str) -> None:
        """Discover devices in controller with optional timeout"""
        print(f"Discovery Filters: {central.dbus_to_python(dongle.GetDiscoveryFilters())}")
        print(f"Powered: {dongle.get('Powered')}")
        pprint(dongle.get_all())
        # devices_discovered = bluetooth_gap.discover_devices(int(scantime))
        # devices_discovered_json = json.JSONEncoder().encode(devices_discovered)
        # logging.info("Discover devices: %s", devices_discovered_json)

    def connect_device(self, bdaddr: str) -> None:
        """Connect device using address"""
        DEVICE_ADDR = bdaddr
        DEVICE_PATH = f"{central.ADAPTER_PATH}/dev_{DEVICE_ADDR.replace(':', '_')}"
        device = central.BluezProxy(DEVICE_PATH, central.BLUEZ_DEVICE)
        device.Connect()
        while not device.get("ServicesResolved"):
            sleep(0.5)
        # result = {}
        # rc = bluetooth_gap.connect(bdaddr)
        # result['result'] = rc
        # logging.info("Connect device: %s", result)

    def write_characteristic(self, bdaddr: str, handle: str, value: str) -> None:
        """Write a value to the characteristic using device address"""
        result = {}
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        try:
            rc = bluetooth_gatt.write_characteristic(bdaddr, handle, value)
            result['result'] = rc
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]
        logging.info("Connect device: %s", result)

    def discover_services(self, bdaddr: str) -> None:
        """Discover services using device address"""
        result = {}
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
        logging.info("Discover services: %s", result)

    def read_characteristic(self, bdaddr: str, handle: str) -> None:
        """Read a characteristic using device address and handle"""
        result = {}
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        try:
            value = bluetooth_gatt.read_characteristic(bdaddr, handle)
            result['value'] = bluetooth_utils.byteArrayToHexString(value)
            result['result'] = 0
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]
        logging.info("Read characteristic: %s", json.JSONEncoder().encode(result))

    def notifications(self, bdaddr: str, handle: str, command: str) -> None:
        """Read a characteristic using device address and handle"""
        def notification_received(path, value):
            result = {}
            result['bdaddr'] = bdaddr
            result['handle'] = path
            result['value'] = bluetooth_utils.byteArrayToHexString(value)
            logging.info("Notification CB: %s", json.JSONEncoder().encode(result))

        result = {}
        if command == 0:
            result['bdaddr'] = bdaddr
            result['handle'] = handle
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
                bluetooth_gatt.enable_notifications(bdaddr, handle, notification_received)
                result['result'] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
            logging.info("Notifications enabled: %s", json.JSONEncoder().encode(result))
        else:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            logging.info("Bad command: %s", json.JSONEncoder().encode(result))
