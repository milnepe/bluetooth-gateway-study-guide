#!/usr/bin/python3
import os
import json
import sys
import cgi

sys.path.insert(0, '../bluetooth')
import bluetooth_gap
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
        if not "scantime" in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            scantime = querystring.getfirst("scantime", "2000")
            devices_discovered = bluetooth_gap.discover_devices(int(scantime))
            devices_allowed = bluetooth_firewall.filter_devices(devices_discovered)
            devices_allowed_json = json.JSONEncoder().encode(devices_allowed)
            print(devices_allowed_json)
else:
    print("ERROR: Not called by HTTP")
