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
    command['bdaddr'] = "84:2E:14:31:C8:B0"
    command['handle'] = "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f"
    ws.send(json.JSONEncoder().encode(command))

while True:
    thread = Thread(target=receiver)
    thread.start()
    # Wait for a response
    thread.join()
