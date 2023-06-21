#!/usr/bin/python
import json
from sys import stdin, stdout

import sys

sys.path.insert(0, '..')
from bluetooth import bluetooth_gatt
from bluetooth import bluetooth_exceptions
from bluetooth import bluetooth_constants
from bluetooth import bluetooth_utils

bdaddr = None
handle = None

def notification_received(path,value):
    result = {}
    result['bdaddr'] = bdaddr
    result['handle'] = path
    result['value'] =  bluetooth_utils.byteArrayToHexString(value)
    print(json.JSONEncoder().encode(result))
    stdout.flush()
    
keep_going = 1
bluetooth_utils.log("====== do_notifications ======\n")
while keep_going == 1:
    line = stdin.readline()
    bluetooth_utils.log(line+"\n")
    if len(line) == 0:
    # means websocket has closed
        keep_going = 0
    else:
        line = line.strip()
        notifications_control = json.loads(line)
        bluetooth_utils.log("command="+str(notifications_control['command'])+"\n");
        result = {}
        if notifications_control['command'] == 1:
            bdaddr = notifications_control['bdaddr']
            handle = notifications_control['handle']
            result['bdaddr'] = bdaddr
            result['handle'] = handle
            try:
                bluetooth_gatt.enable_notifications(bdaddr, handle, notification_received)
                result['result'] = bluetooth_constants.RESULT_OK;
                print(json.JSONEncoder().encode(result))
                stdout.flush()
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
                stdout.flush()
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
                stdout.flush()
            
        elif notifications_control['command'] == 0:
            bdaddr = notifications_control['bdaddr']
            handle = notifications_control['handle']
            result['bdaddr'] = bdaddr
            result['handle'] = handle
            try:
                bluetooth_utils.log("calling disable_notifications\n")
                rc = bluetooth_gatt.disable_notifications(bdaddr, handle)
                bluetooth_utils.log("done calling disable_notifications\n")
                result['result'] = bluetooth_constants.RESULT_OK;
                print(json.JSONEncoder().encode(result))
                stdout.flush()
                bluetooth_utils.log("finished\n")
            except bluetooth_exceptions.StateError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
                stdout.flush()
            except bluetooth_exceptions.UnsupportedError as e:
                result['result'] = e.args[0]
                print(json.JSONEncoder().encode(result))
                stdout.flush()

        elif notifications_control['command'] == 9:
            keep_going = 0
print("WebSocket handler has exited")
stdout.flush()
