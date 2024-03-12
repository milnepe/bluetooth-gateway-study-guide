"""Bluetooth LE device controller"""

import logging
import sys
import json
from dataclasses import dataclass
import dbus
import dbus.mainloop.glib
from paho.mqtt import publish

# sys.path.insert(0, "..")  # Aid location of bluetooth package
from bluetooth_api import bluetooth_gap
from bluetooth_api import bluetooth_gatt
from bluetooth_api import bluetooth_exceptions
from bluetooth_api import bluetooth_utils
from bluetooth_api import bluetooth_constants
from bluetooth_api import bluetooth_general

try:
    import gi.repository.GLib
except ImportError:
    # import gobject as GObject
    print("gi.repository.GLib import not found")


@dataclass
class BtController:
    """Bluetooth LE Controller"""

    hostname: str
    topic_root: str

    def publisher(self, topic: str, result: dict):
        """Publishing helper"""
        json_result = json.JSONEncoder().encode(result)
        # bluetooth_constants.TOPIC_ROOT + "/out/" + topic,
        publish.single(
            f"{self.topic_root}/out/{topic}",
            json_result,
            hostname=self.hostname,
        )

    def discover_devices(self, scantime: str) -> None:
        """Discover devices in controller with optional timeout"""
        devices_discovered = bluetooth_gap.discover_devices(int(scantime))
        json_devices_discovered = json.JSONEncoder().encode(devices_discovered)
        logging.info("Discover devices: %s", json_devices_discovered)
        self.publisher("devices", json_devices_discovered)  # Publish result

    def connect_device(self, bdaddr: str) -> None:
        """Connect device using address"""
        result = {}
        result_code = bluetooth_gap.connect(bdaddr)
        result["result"] = result_code
        result["bdaddr"] = bdaddr
        result["cmd"] = "connect_device"
        logging.info(json.JSONEncoder().encode(result))
        self.publisher("connection", result)  # Publish result

    def write_characteristic(self, bdaddr: str, handle: str, value: str) -> None:
        """Write a value to the characteristic using device address"""
        result = {}
        result["bdaddr"] = bdaddr
        result["handle"] = handle
        result["cmd"] = "write_characteristic"
        result["value"] = value
        try:
            result_code = bluetooth_gatt.write_characteristic(bdaddr, handle, value)
            result["result"] = result_code
        except bluetooth_exceptions.StateError as error:
            result["result"] = error.args[0]
        logging.info(json.JSONEncoder().encode(result))
        self.publisher("sensor", result)  # Publish result

    def discover_services(self, bdaddr: str) -> None:
        """Discover services using device address"""
        result = {}
        result["cmd"] = "discover_services"
        try:
            services_discovered = bluetooth_gatt.get_services(bdaddr)

            for service in services_discovered:
                # rename BlueZ-specific parameter name to the more abstract 'handle'
                service["handle"] = service.pop("path")
                characteristics_discovered = bluetooth_gatt.get_characteristics(
                    bdaddr, service["handle"]
                )

                service["characteristics"] = characteristics_discovered
                for characteristic in characteristics_discovered:
                    characteristic["handle"] = characteristic.pop("path")
                    characteristic["service_handle"] = characteristic.pop(
                        "service_path"
                    )
                    descriptors_discovered = bluetooth_gatt.get_descriptors(
                        bdaddr, characteristic["handle"]
                    )

                    characteristic["descriptors"] = descriptors_discovered
                    for descriptor in descriptors_discovered:
                        descriptor["handle"] = descriptor.pop("path")
                        descriptor["characteristic_handle"] = descriptor.pop(
                            "characteristic_path"
                        )

            result = json.JSONEncoder().encode(services_discovered)
        except bluetooth_exceptions.StateError as error:
            result["result"] = error.args[0]
        logging.info(json.JSONEncoder().encode(result))
        self.publisher("services", result)  # Publish result

    def read_characteristic(self, bdaddr: str, handle: str):
        """Read a characteristic using device address and handle"""
        result = {}
        result["bdaddr"] = bdaddr
        result["handle"] = handle
        result["cmd"] = "read_characteristic"
        try:
            value = bluetooth_gatt.read_characteristic(bdaddr, handle)
            print(value)
            # Converts 8, 16 or 32 bit values in little endian byte order to signed integers
            # as Telegraf can't do this - they just need scaling
            result["value"] = bluetooth_utils.byteListToInt(value, byteorder='little')
            result["result"] = 0
        except bluetooth_exceptions.StateError as error:
            result["result"] = error.args[0]
        logging.info(json.JSONEncoder().encode(result))
        self.publisher("sensor", result)


@dataclass
class Notifier:
    """Notification class allowing each device to have its own event handler
    [Todo: fix stop notifications]"""

    bdaddr: str
    handle: str
    command: str
    notifications_callback = None

    def properties_changed(self, interface, changed, invalidated, path):
        """Properties changed"""
        if interface != "org.bluez.GattCharacteristic1":
            return

        value = []
        value = changed.get("Value")
        if not value:
            return
        if self.notifications_callback:
            self.notifications_callback(path, value)

    @staticmethod
    def stop_handler():
        mainloop = gi.repository.GLib.MainLoop()
        mainloop.quit()

    def start_notifications(self, characteristic_iface):
        """Start notifications helper"""
        bus = dbus.SystemBus()
        bus.add_signal_receiver(
            self.properties_changed,
            bus_name=bluetooth_constants.BLUEZ_SERVICE_NAME,
            dbus_interface=bluetooth_constants.DBUS_PROPERTIES,
            signal_name="PropertiesChanged",
            path_keyword="path",
        )

        bus.add_signal_receiver(Notifier.stop_handler, "StopNotifications")

        characteristic_iface.StartNotify()

    def enable_notifications(self, bdaddr, characteristic_path, callback):
        """Enable notification with callback"""
        self.notifications_callback = callback
        bus = dbus.SystemBus()
        device_proxy = bluetooth_general.getDeviceProxy(bus, bdaddr)
        if not device_proxy:
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_NOT_CONNECTED
            )
        device_path = device_proxy.object_path

        if not bluetooth_general.is_connected(bus, device_path):
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_NOT_CONNECTED
            )

        if not device_proxy.ServicesResolved:
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_SERVICES_NOT_RESOLVED
            )

        characteristic_object = bus.get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, characteristic_path
        )
        characteristic_iface = dbus.Interface(
            characteristic_object, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE
        )
        properties_iface = dbus.Interface(
            characteristic_object, bluetooth_constants.DBUS_PROPERTIES
        )
        characteristic_properties = properties_iface.Get(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Flags"
        )

        if (
            "notify" not in characteristic_properties
            and "indicate" not in characteristic_properties
        ):
            raise bluetooth_exceptions.UnsupportedError(
                bluetooth_constants.RESULT_ERR_NOT_SUPPORTED
            )

        # Returns dbus.Boolean!
        notifying = properties_iface.Get(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Notifying"
        )
        notifying = bool(notifying)
        if notifying is True:
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_WRONG_STATE
            )
        self.start_notifications(characteristic_iface)

    def notification_received(self, path, value):
        """Notifications callback"""
        result = {}
        bdaddr_from_path = path.replace("_", ":")[20:37]  # Hack!
        result["bdaddr"] = self.bdaddr
        result["handle"] = path
        result["cmd"] = "notification_received"
        # Converts 8, 16 or 32 bit values in little endian byte order to signed integers
        # as Telegraf can't do this - they just need scaling
        result["value"] = bluetooth_utils.byteListToInt(value, byteorder='little')
        if bdaddr_from_path == self.bdaddr:
            logging.info(json.JSONEncoder().encode(result))

    def disable_notifications(self, bdaddr, characteristic_path):
        """Disable characteristic notifications"""
        logging.info("disable_notifications")
        bus = dbus.SystemBus()
        device_proxy = bluetooth_general.getDeviceProxy(bus, bdaddr)
        device_path = device_proxy.object_path

        if not bluetooth_general.is_connected(bus, device_path):
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_NOT_CONNECTED
            )

        if not device_proxy.ServicesResolved:
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_SERVICES_NOT_RESOLVED
            )

        characteristic_object = bus.get_object(
            bluetooth_constants.BLUEZ_SERVICE_NAME, characteristic_path
        )
        characteristic_iface = dbus.Interface(
            characteristic_object, bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE
        )
        properties_iface = dbus.Interface(
            characteristic_object, bluetooth_constants.DBUS_PROPERTIES
        )

        characteristic_properties = properties_iface.Get(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Flags"
        )

        if (
            "notify" not in characteristic_properties
            and "indicate" not in characteristic_properties
        ):
            raise bluetooth_exceptions.UnsupportedError(
                bluetooth_constants.RESULT_ERR_NOT_SUPPORTED
            )

        notifying = properties_iface.Get(
            bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, "Notifying"
        )
        notifying = bool(notifying)
        if notifying is False:
            raise bluetooth_exceptions.StateError(
                bluetooth_constants.RESULT_ERR_WRONG_STATE
            )

        logging.info("calling StopNotify")
        characteristic_iface.StopNotify()

    def notifications(self) -> None:
        """Handle notifications"""
        result = {}
        if self.command == 0:
            try:
                self.disable_notifications(self.bdaddr, self.handle)
                result["result"] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as error:
                result["result"] = error.args[0]
            except bluetooth_exceptions.UnsupportedError as error:
                result["result"] = error.args[0]
            except dbus.exceptions.DBusException as error:
                result["result"] = error.args[0]
            logging.info(
                "Notifications disabled: %s", json.JSONEncoder().encode(result)
            )
        elif self.command == 1:
            try:
                self.enable_notifications(
                    self.bdaddr, self.handle, self.notification_received
                )
                result["result"] = bluetooth_constants.RESULT_OK
            except bluetooth_exceptions.StateError as error:
                result["result"] = error.args[0]
            except bluetooth_exceptions.UnsupportedError as error:
                result["result"] = error.args[0]
            logging.info("Notifications enabled: %s", json.JSONEncoder().encode(result))
        else:
            result["result"] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            logging.info("Bad command: %s", json.JSONEncoder().encode(result))
