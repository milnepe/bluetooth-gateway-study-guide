#!/usr/bin/python3
import os
import json
import sys
sys.path.insert(0, '../bluetooth')
import bluetooth_gatt
import bluetooth_exceptions
import bluetooth_constants
import bluetooth_utils
import bluetooth_firewall

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
        if not "bdaddr" in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        elif not "handle" in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        elif not "value" in args:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            bdaddr = args["bdaddr"]
            handle = args["handle"]
            value = args["value"]
            result = {}
            result['bdaddr'] = bdaddr
            result['handle'] = handle
            if not bluetooth_firewall.characteristic_is_allowed(bdaddr, handle):
                print('Status-Line: HTTP/1.0 403 Forbidden')
            else:    
                try:
                    rc = bluetooth_gatt.write_characteristic(bdaddr,handle,value)
                    result['result'] = rc
                    print(json.JSONEncoder().encode(result))
                except bluetooth_exceptions.StateError as e:
                    result['result'] = e.args[0]
                    print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
