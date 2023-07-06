from pprint import pprint
from time import sleep
import dbus

BLUEZ_SERVICE_NAME = "org.bluez"
BLUEZ_ADAPTER = "org.bluez.Adapter1"
BLUEZ_DEVICE = "org.bluez.Device1"
BLUEZ_GATT_CHRC = "org.bluez.GattCharacteristic1"
TMP_UUID = "e95d9250-251d-470a-a062-fa1922dfa9a8"
DSPLY_TXT = "e95d93ee-251d-470a-a062-fa1922dfa9a8"
SCRLL_DLY = "e95d0d2d-251d-470a-a062-fa1922dfa9a8"
ADAPTER_PATH = "/org/bluez/hci0"
DEVICE_ADDR = "E1:4B:6C:22:56:F0"
DEVICE_PATH = f"{ADAPTER_PATH}/dev_{DEVICE_ADDR.replace(':', '_')}"


bus = dbus.SystemBus()


def dbus_to_python(data):
    """convert D-Bus data types to python data types"""
    if isinstance(data, dbus.String):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Byte):
        data = int(data)
    elif isinstance(data, dbus.UInt16):
        data = int(data)
    elif isinstance(data, dbus.UInt32):
        data = int(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.ObjectPath):
        data = str(data)
    elif isinstance(data, dbus.Array):
        if data.signature == dbus.Signature('y'):
            data = bytearray(data)
        else:
            data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data:
            new_data[dbus_to_python(key)] = dbus_to_python(data[key])
        data = new_data
    return data


def get_managed_objects():
    """
    Return the objects currently managed by the D-Bus Object Manager for BlueZ.
    """
    manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, "/"),
        "org.freedesktop.DBus.ObjectManager"
    )
    return manager.GetManagedObjects()


def gatt_chrc_path(uuid, path_start="/"):
    """
    Find the D-Bus path for a GATT Characteristic of given uuid.
    Use `path_start` to ensure it is on the correct device or service
    """
    for path, info in get_managed_objects().items():
        found_uuid = info.get(BLUEZ_GATT_CHRC, {}).get("UUID", "")
        if all((uuid.casefold() == found_uuid.casefold(),
                path.startswith(path_start))):
            return path
    return None


class BluezProxy(dbus.proxies.Interface):
    """
        A proxy to the remote Object. A ProxyObject is provided so functions
        can be called like normal Python objects.
     """
    def __init__(self, dbus_path, interface):
        self.dbus_object = bus.get_object(BLUEZ_SERVICE_NAME, dbus_path)
        self.prop_iface = dbus.Interface(self.dbus_object,
                                         dbus.PROPERTIES_IFACE)
        super().__init__(self.dbus_object, interface)

    def get_all(self):
        """Return all properties on Interface"""
        return dbus_to_python(self.prop_iface.GetAll(self.dbus_interface))

    def get(self, prop_name, default=None):
        """Access properties on the interface"""
        try:
            value = self.prop_iface.Get(self.dbus_interface, prop_name)
        except dbus.exceptions.DBusException:
            return default
        return dbus_to_python(value)


def main():
    """
    Procedurally connect to remote device and interact with various
    BLE GATT characteristics, and then disconnect from device
    """
    # dongle - Get information from Bluetooth dongle on device
    dongle = BluezProxy(ADAPTER_PATH, BLUEZ_ADAPTER)
    print(f"Discovery Filters: {dbus_to_python(dongle.GetDiscoveryFilters())}")
    print(f"Powered: {dongle.get('Powered')}")
    pprint(dongle.get_all())

    # Device - Connect to device with given address
    device = BluezProxy(DEVICE_PATH, BLUEZ_DEVICE)
    device.Connect()
    while not device.get("ServicesResolved"):
        sleep(0.5)

    # GATT - Read Temperature characteristic from device
    tmp_val_path = gatt_chrc_path(TMP_UUID, device.object_path)
    tmp_chrc = BluezProxy(tmp_val_path, BLUEZ_GATT_CHRC)
    value = int.from_bytes(bytes(tmp_chrc.ReadValue({})), "little")
    print(f"Temperature is: {value}")

    # GATT - Change Scroll Delay characteristic value
    scrll_dly_path = gatt_chrc_path(SCRLL_DLY, device.object_path)
    scrll_dly = BluezProxy(scrll_dly_path, BLUEZ_GATT_CHRC)
    print(f"Scroll speed [raw bytes]: {dbus_to_python(scrll_dly.ReadValue({}))}")
    value = int.from_bytes(bytes(scrll_dly.ReadValue({})), "little")
    print(f"Scroll delay is: {value}")
    scrll_dly.WriteValue(int(value + 2).to_bytes(2, "little"), {})
    value = int.from_bytes(bytes(scrll_dly.ReadValue({})), "little")
    print(f"Scroll delay is: {value}")

    # GATT - Write to Text characteristic
    txt_path = gatt_chrc_path(DSPLY_TXT, device.object_path)
    txt_chrc = BluezProxy(txt_path, BLUEZ_GATT_CHRC)
    txt_chrc.WriteValue(b'Carpe diem', {})
    # Disconnect from device
    device.Disconnect()


if __name__ == "__main__":
    main()
