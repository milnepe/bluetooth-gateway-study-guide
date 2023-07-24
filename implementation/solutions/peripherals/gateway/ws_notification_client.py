#!/usr/bin/python
"""
Client to receive BLE notifications over websockets (Thunderboard)

1. Start websocketd
websocketd --port=8082 /usr/lib/cgi-bin/gateway/do_notifications.py

2. Connect device using bluetoothctl

3. Run script in another terminal
./ws_notification_client.py "ws://localhost:8082" "84:2E:14:31:C8:B0" "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f" "1"
./ws_notification_client.py "ws://localhost:8082" "90:FD:9F:7B:7F:1C" "/org/bluez/hci0/dev_90_FD_9F_7B_7F_1C/service0042/char0043" "1"

4. Press BTN0 to receive notifications
"""
import websocket
import json
import sys
from threading import Thread


endpoint = sys.argv[1]  # eg "ws://localhost:8082")
bdaddr = sys.argv[2]  # eg "84:2E:14:31:C8:B0"
handle = sys.argv[3]  # eg "/org/bluez/hci0/dev_84_2E_14_31_C8_B0/service002e/char002f"
cmd = sys.argv[4]  # eg "1"


def receiver():
    print(ws.recv())


if __name__ == '__main__':
    ws = websocket.WebSocket()
    ws.connect(endpoint)
    command = {}
    # enable button notifications
    command['command'] = int(cmd)
    command['bdaddr'] = bdaddr
    command['handle'] = handle
    ws.send(json.JSONEncoder().encode(command))

while True:
    thread = Thread(target=receiver)
    thread.start()
    # Wait for a response
    thread.join()
