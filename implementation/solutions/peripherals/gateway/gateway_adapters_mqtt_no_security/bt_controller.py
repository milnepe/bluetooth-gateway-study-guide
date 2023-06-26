import logging
import sys
import json

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_gap


class BtController:

    def discover_devices(self, scantime: str) -> None:
        """Discover devices in controller with optional timeout"""
        devices_discovered = bluetooth_gap.discover_devices(int(scantime))
        devices_discovered_json = json.JSONEncoder().encode(devices_discovered)
        logging.info("Discover devices: %s", devices_discovered_json)

    def connect_device(self, bdaddr: str) -> None:
        """Discover devices in controller with optional timeout"""
        result = {}
        rc = bluetooth_gap.connect(bdaddr)
        result['result'] = rc
        logging.info("Connect device: %s", result)