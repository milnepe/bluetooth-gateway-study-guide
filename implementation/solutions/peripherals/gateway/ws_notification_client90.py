#!/usr/bin/python
"""
Client to receive BLE notifications over websockets

Start websocketd
websocketd --port=8082 /usr/lib/cgi-bin/gateway/do_notifications.py

Then run script in another terminal
./ws_notification_client.py
"""
import websocket
import json
from threading import Thread


def receiver():
    print(ws.recv())


if __name__ == '__main__':
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:8082")
    command = {}
    # enable button notifications
    command['command'] = 1
    command['bdaddr'] = "90:FD:9F:7B:7F:1C"
    command['handle'] = "/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043"
    ws.send(json.JSONEncoder().encode(command))

while True:
    thread = Thread(target=receiver)
    thread.start()
    # Wait for a response
    thread.join()
