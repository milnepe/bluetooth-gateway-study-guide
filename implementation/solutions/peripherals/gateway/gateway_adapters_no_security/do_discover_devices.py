#!/usr/bin/python
"""
Discover devices test

Should pass:
curl --request GET http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_discover_devices.py?scantime=3000
Or from remote browser
http://rock-3c/cgi-bin/gateway/gateway_adapters_no_security/do_discover_devices.py?scantime=3000
[{"bdaddr": "84:2E:14:31:C8:B0"...]

Should fail:
curl --header "Content-Type: application/json" --request PUT http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_discover_devices.py?scantime=3000
Status-Line: HTTP/1.0 405 Method Not Allowed

curl --request GET http://localhost/cgi-bin/gateway/gateway_adapters_no_security/do_discover_devices.py?xxxxxxxx=3000
{"result": 8}
"""
import os
import json
import sys
import cgi

sys.path.insert(0, '..')  # Aid apache to locate bluetooth package
from bluetooth import bluetooth_gap
from bluetooth import bluetooth_constants


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
        if "scantime" not in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            scantime = querystring.getfirst("scantime", "2000")
            devices_discovered = bluetooth_gap.discover_devices(int(scantime))
            devices_discovered_json = json.JSONEncoder().encode(devices_discovered)
            print(devices_discovered_json)
else:
    print("ERROR: Not called by HTTP")
