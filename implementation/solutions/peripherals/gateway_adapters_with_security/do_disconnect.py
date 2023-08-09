#!/usr/bin/python3
import os
import json
import sys
sys.path.insert(0, '../bluetooth')
import bluetooth_gap
import bluetooth_constants
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
            if not "bdaddr" in args:
                print("Content-Type: application/json;charset=utf-8")
                print()
                result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
                print(json.JSONEncoder().encode(result))
            else:
                bdaddr = args["bdaddr"]
                if not bluetooth_firewall.device_is_allowed(bdaddr):
                    print('Status: 403 Forbidden')
                    print()
                    print('Status-Line: HTTP/1.0 403 Forbidden')
                    print()
                else:
                    rc = bluetooth_gap.disconnect(bdaddr)
                    result['result'] = rc
                    print("Content-Type: application/json;charset=utf-8")
                    print()
                    print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")

