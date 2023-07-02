#!/usr/bin/python
"""
Service discovery test
Discover and connect to device before running:

Should pass:
curl --request GET http://localhost/cgi-bin/gateway/do_service_discovery.py?bdaddr=84:2E:14:31:C8:B0
[{"UUID": "00001801-0000-1000-8000-00805f9b34fb", "handle": "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service0001"...]
"""
import os
import json
from sys import stdin, stdout
import cgi
import sys

sys.path.insert(0, '..')
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
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
        if "bdaddr" not in querystring:
            result['result'] = bluetooth_constants.RESULT_ERR_BAD_ARGS
            print(json.JSONEncoder().encode(result))
        else:
            bdaddr = querystring.getfirst("bdaddr")
            try:
                services_discovered = bluetooth_gatt.get_services(bdaddr)

                for service in services_discovered:
                    # rename BlueZ-specific parameter name to the more abstract 'handle'
                    service['handle'] = service.pop('path')
                    characteristics_discovered = bluetooth_gatt.get_characteristics(bdaddr, service['handle'])

                    service['characteristics'] = characteristics_discovered
                    for characteristic in characteristics_discovered:
                        characteristic['handle'] = characteristic.pop('path')
                        characteristic['service_handle'] = characteristic.pop('service_path')
                        descriptors_discovered = bluetooth_gatt.get_descriptors(bdaddr, characteristic['handle'])

                        characteristic['descriptors'] = descriptors_discovered
                        for descriptor in descriptors_discovered:
                            descriptor['handle'] = descriptor.pop('path')
                            descriptor['characteristic_handle'] = descriptor.pop('characteristic_path')

                attributes_discovered_json = json.JSONEncoder().encode(services_discovered)
                print(attributes_discovered_json)
            except bluetooth_exceptions.StateError as e:
                result = {}
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
