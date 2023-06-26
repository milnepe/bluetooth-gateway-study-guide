#!/usr/bin/python
"""
Read characteristic test - get model number string UUID equal to 00002a24-0000-1000-8000-00805f9b34fb
Obtain the handle from do_service_discovery

Should pass:
curl --request GET "http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_read_characteristic.py?bdaddr=84:2E:14:31:C8:B0&handle=/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service000e/char0011"
"""
import os
import json
import sys
import cgi

sys.path.insert(0, '..')
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_constants
from bluetooth import bluetooth_utils

if 'REQUEST_METHOD' in os.environ:
    result = {}
    if os.environ['REQUEST_METHOD'] != 'GET':
        print('Status: 405 Method Not Allowed')
        print()
        print("Status-Line: HTTP/1.0 405 Method Not Allowed")
        print()
    else:
        print("Content-Type: application/json;charset=utf-8")
        print()
        querystring = cgi.FieldStorage()
        if "bdaddr" not in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        if "handle" not in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            bdaddr = querystring.getfirst("bdaddr")
            handle = querystring.getfirst("handle")
            result = {}
            result['bdaddr'] = bdaddr
            result['handle'] = handle
            try:
                value = bluetooth_gatt.read_characteristic(bdaddr, handle)
                result['value'] = bluetooth_utils.byteArrayToHexString(value)
                result['result'] = 0
                print(json.JSONEncoder().encode(result))
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
