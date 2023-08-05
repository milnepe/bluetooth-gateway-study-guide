import logging
import sys
import json
import dbus
from threading import Thread
from dataclasses import dataclass

sys.path.insert(0, '..')  # Aid location of bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_utils
from bluetooth import bluetooth_constants
from bluetooth import bluetooth_general

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


@dataclass
class Notifier:
    bdaddr: str
    handle: str
    command: str
    notifications_callback = None

    def properties_changed(self, interface, changed, invalidated, path):
        if interface != "org.bluez.GattCharacteristic1":
            return

        value = []
        value = changed.get('Value')
        if not value:
            return
        if self.notifications_callback:
            #print(f"PATH: {path}") 
            self.notifications_callback(path, value)
        # stdout.flush()

    def stop_handler(self):
        mainloop.quit()

    def start_notifications(self, characteristic_iface):
        bus = dbus.SystemBus()
        bus.add_signal_receiver(self.properties_changed, bus_name=bluetooth_constants.BLUEZ_SERVICE_NAME,
                                dbus_interface=bluetooth_constants.DBUS_PROPERTIES,
                                signal_name="PropertiesChanged",
                                path_keyword="path")

        bus.add_signal_receiver(self.stop_handler, "StopNotifications")

        characteristic_iface.StartNotify()

    def enable_notifications(self, bdaddr, characteristic_path, callback):
        self.notifications_callback = callback
        bus = dbus.SystemBus()
        device_proxy = bluetooth_general.getDeviceProxy(bus, bdaddr)
        logging.info(f"Proxy: {device_proxy}")
        if not device_proxy:
            raise bluetooth_exceptions.StateError(bluetooth_constants.RESULT_ERR_NOT_CONNECTED)
        device_path = device_proxy.object_path
        logging.info(f"Device path: {device_path}")

        if not bluetooth_general.is_connected(bus, device_path):
            raise bluetooth_exceptions.StateError(bluetooth_constants.RESULT_ERR_NOT_CONNECTED)

        if not device_proxy.ServicesResolved:
            raise bluetooth_exceptions.StateError(bluetooth_constants.RESULT_ERR_SERVICES_NOT_RESOLVED)

        characteristic_object = bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, characteristic_path)
        logging.info(f"CH_OBJECT: {characteristic_object}")
        characteristic_iface = dbus.Interface(characteristic_object, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE)
        logging.info(f"CH_INTERFACE: {characteristic_iface}")
        properties_iface = dbus.Interface(characteristic_object, bluetooth_constants.DBUS_PROPERTIES)
        logging.info(f"PROP_IFACE: {properties_iface}")
        characteristic_properties = properties_iface.Get(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Flags")
        logging.info(f"CHAR_PROPS: {characteristic_properties}")
        if 'notify' not in characteristic_properties and 'indicate' not in characteristic_properties:
            raise bluetooth_exceptions.UnsupportedError(bluetooth_constants.RESULT_ERR_NOT_SUPPORTED)

        # Returns dbus.Boolean!
        notifying = properties_iface.Get(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Notifying")
        notifying = bool(notifying)
        logging.info(f"NOTIFYING: {notifying=}")
        if notifying is True:
            raise bluetooth_exceptions.StateError(bluetooth_constants.RESULT_ERR_WRONG_STATE)
        logging.info("Starting notifications...")
        #start_notifications(characteristic_iface)

        thread = Thread(target=self.start_notifications, args=(characteristic_iface, ))
        thread.daemon = True
        thread.start()

    def notification_received(self, path, value):
        """Notifications callback"""
        result = {}
        bdaddr_from_path = path.replace('_', ':')[20:37]  # Hack!
        result['bdaddr'] = self.bdaddr
        result['handle'] = path
        result['cmd'] = "notification_received"
        result['value'] = bluetooth_utils.byteArrayToHexString(value)
        if bdaddr_from_path == self.bdaddr:
            logging.info(json.JSONEncoder().encode(result))


    #def notifications(self, bdaddr: str, handle: str, command: str) -> None:
    def notifications(self) -> None:
        """Handle notifications"""
        result = {}


        if self.command == 0:
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
        elif self.command == 1:
            try:
                self.enable_notifications(self.bdaddr, self.handle, self.notification_received)
                result['result'] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
            logging.info("Notifications enabled: %s", json.JSONEncoder().encode(result))
        else:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            logging.info("Bad command: %s", json.JSONEncoder().encode(result))
