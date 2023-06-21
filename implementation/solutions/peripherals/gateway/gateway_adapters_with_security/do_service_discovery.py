#!/usr/bin/python3
import os
import json
from sys import stdin, stdout
import cgi

import sys
sys.path.insert(0, '../bluetooth')
import bluetooth_gatt
import bluetooth_exceptions
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
        else:
            bdaddr = querystring.getfirst("bdaddr")
            try:
                services_discovered = bluetooth_gatt.get_services(bdaddr)
                # firewall service filtering
                allowed_services = bluetooth_firewall.filter_services(bdaddr, services_discovered)

                for service in allowed_services:
                    # rename BlueZ-specific parameter name to the more abstract 'handle'
                    service['handle'] = service.pop('path')
                    characteristics_discovered = bluetooth_gatt.get_characteristics(bdaddr, service['handle'])
                    
                    # firewall characteristic filtering
                    allowed_characteristics = bluetooth_firewall.filter_characteristics(bdaddr, service['UUID'], characteristics_discovered)
                    service['characteristics'] = allowed_characteristics
                    for characteristic in allowed_characteristics:
                        characteristic['handle'] = characteristic.pop('path')
                        characteristic['service_handle'] = characteristic.pop('service_path')
                        descriptors_discovered = bluetooth_gatt.get_descriptors(bdaddr, characteristic['handle'])
                        
                        # firewall descriptor filtering
                        allowed_descriptors = bluetooth_firewall.filter_descriptors(bdaddr, service['UUID'], characteristic['UUID'], descriptors_discovered)
                        characteristic['descriptors'] = allowed_descriptors
                        for descriptor in allowed_descriptors:
                            descriptor['handle'] = descriptor.pop('path')
                            descriptor['characteristic_handle'] = descriptor.pop('characteristic_path')

                attributes_discovered_json = json.JSONEncoder().encode(allowed_services)
                print(attributes_discovered_json)
            except bluetooth_exceptions.StateError as e:
                result = {}
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
else:
    print("ERROR: Not called by HTTP")
