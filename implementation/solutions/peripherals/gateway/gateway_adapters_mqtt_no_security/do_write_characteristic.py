#!/usr/bin/python
"""
Write characteristic - write to the digital service which turns on the Thunderboard led
This has the handle "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034"
and takes a char value of "00" for off and "01" for on - see output from do_read_characteristics

"UUID": "00002a56-0000-1000-8000-00805f9b34fb",
"properties": ["read", "write"],
"handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034",
"service_handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e",
"descriptors": [{
    "UUID": "00002909-0000-1000-8000-00805f9b34fb",
    "handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034/desc0037",
    "characteristic_handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034"

Turn on led
curl --header "Content-Type: application/json" --data '{"bdaddr":"84:2E:14:31:C8:B0" , "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034" , "value":"01"}' --request PUT http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_write_characteristic.py
{"bdaddr": "84:2E:14:31:C8:B0", "handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034", "result": 0}

Turn off led
curl --header "Content-Type: application/json" --data '{"bdaddr":"84:2E:14:31:C8:B0" , "handle":"/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034" , "value":"00"}' --request PUT http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_write_characteristic.py
{"bdaddr": "84:2E:14:31:C8:B0", "handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char0034", "result": 0}
"""
import os
import json
import sys

sys.path.insert(0, '..')
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_constants
from bluetooth import bluetooth_utils

if 'REQUEST_METHOD' in os.environ:
    result = {}
    args = json.load(sys.stdin)
    if os.environ['REQUEST_METHOD'] != 'PUT':
        print('Status: 405 Method Not Allowed')
        print()
        print("Status-Line: HTTP/1.0 405 Method Not Allowed")
        print()
    else:
        print("Content-Type: application/json;charset=utf-8")
        print()
        if "bdaddr" not in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        elif "handle" not in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        elif "value" not in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            bdaddr = args["bdaddr"]
            handle = args["handle"]
            value = args["value"]
            result = {}
            result['bdaddr'] = bdaddr
            result['handle'] = handle
            try:
                rc = bluetooth_gatt.write_characteristic(bdaddr, handle, value)
                result['result'] = rc
                print(json.JSONEncoder().encode(result))
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
