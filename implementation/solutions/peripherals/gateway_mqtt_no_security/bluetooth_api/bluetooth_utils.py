"""Bluetooth LE API utils"""

import dbus


def byteArrayToHexString(bytes):
    """Convert byteArray to HEX string"""
    hex_string = ""
    for byte in bytes:
        hex_byte = "%02X" % byte
        hex_string = hex_string + hex_byte
    return hex_string


def dbus_to_python(data):
    """Convert dbus types to equivalent python types"""
    if isinstance(data, dbus.String):
        data = str(data)
    if isinstance(data, dbus.ObjectPath):
        data = str(data)
    elif isinstance(data, dbus.Boolean):
        data = bool(data)
    elif isinstance(data, dbus.Int64):
        data = int(data)
    elif isinstance(data, dbus.Int32):
        data = int(data)
    elif isinstance(data, dbus.Int16):
        data = int(data)
    elif isinstance(data, dbus.UInt16):
        data = int(data)
    elif isinstance(data, dbus.Byte):
        data = int(data)
    elif isinstance(data, dbus.Double):
        data = float(data)
    elif isinstance(data, dbus.Array):
        data = [dbus_to_python(value) for value in data]
    elif isinstance(data, dbus.Dictionary):
        new_data = dict()
        for key in data.keys():
            new_data[key] = dbus_to_python(data[key])
        data = new_data
    return data


def big_to_little(b_endian: str) -> str:
    """Convert big-endian to little-endian HEX values"""
    l_endian = bytearray.fromhex(b_endian)
    l_endian.reverse()
    return "".join(format(x, "02x") for x in l_endian)


def scale_hex_big_endian(value: str, scalar: int) -> int:
    """Scale big-endian HEX value"""
    return int(big_to_little(value), 16) / scalar
