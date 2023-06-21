#!/usr/bin/python3
import os
import json
import sys
import cgi
sys.path.insert(0, '../bluetooth')
import bluetooth_gatt
import bluetooth_exceptions
import bluetooth_constants
import bluetooth_utils
import bluetooth_firewall

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
        if not "bdaddr" in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        elif not "handle" in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            bdaddr = querystring.getfirst("bdaddr")
            handle = querystring.getfirst("handle")
            if not bluetooth_firewall.characteristic_is_allowed(bdaddr, handle):
                print('Status-Line: HTTP/1.0 403 Forbidden')
            else:
                result = {}
                result['bdaddr'] = bdaddr
                result['handle'] = handle
                try:
                    value = bluetooth_gatt.read_characteristic(bdaddr,handle)
                    result['value'] = bluetooth_utils.byteArrayToHexString(value);
                    result['result'] = 0
                    print(json.JSONEncoder().encode(result))
                except bluetooth_exceptions.StateError as e:
                    result['result'] = e.args[0]
                    print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
