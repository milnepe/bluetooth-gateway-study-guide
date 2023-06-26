import logging
import sys
import json

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions


class BtController:

    def discover_devices(self, scantime: str) -> None:
        """Discover devices in controller with optional timeout"""
        devices_discovered = bluetooth_gap.discover_devices(int(scantime))
        devices_discovered_json = json.JSONEncoder().encode(devices_discovered)
        logging.info("Discover devices: %s", devices_discovered_json)

    def connect_device(self, bdaddr: str) -> None:
        """Connect device using address"""
        result = {}
        rc = bluetooth_gap.connect(bdaddr)
        result['result'] = rc
        logging.info("Connect device: %s", result)

    def write_characteristic(self, bdaddr: str, handle: str, value: str) -> None:
        """Connect device using address"""
        result = {}
        result['bdaddr'] = bdaddr
        result['handle'] = handle
        try:
            rc = bluetooth_gatt.write_characteristic(bdaddr, handle, value)
            result['result'] = rc
        except bluetooth_exceptions.StateError as e:
            result['result'] = e.args[0]

        logging.info("Connect device: %s", result)
