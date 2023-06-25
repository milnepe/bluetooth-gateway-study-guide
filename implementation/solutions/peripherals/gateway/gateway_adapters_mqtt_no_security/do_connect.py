#!/usr/bin/python
"""
Connect device test
Device must be advertising and do_discover_devices ran before hand

Should pass:
rock@rock-3c:~$ curl --header "Content-Type: application/json" --data '{"bdaddr":"84:2E:14:31:C8:B0" }' --request PUT http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_connect.py
{"result": 0}

If connection fails run do_discover_devices again
Monitor the connection in bluetoothctl
"""
import os
import json
import sys

sys.path.insert(0, '..')  # Aid apache to locate bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_constants


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
        else:
            bdaddr = args["bdaddr"]
            rc = bluetooth_gap.connect(bdaddr)
            result['result'] = rc
            print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
