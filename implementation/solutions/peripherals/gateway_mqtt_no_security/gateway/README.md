# bluetooth-gateway-study-guide/implementation/solutions/peripherals/gateway_mqtt_no_security/gateway

Solution - code which implements a gateway API, responding to MQTT messages and returning JSON objects.

Uses the Python Bluetooth API.

Does not use the bluetooth_firewall functions and so exercises no control over which devices and attributes are available.

Two Python clients are provided:

mqtt_client.py - runs on the gateway and listens for incoming MQTT messages containing BLE commands

remote_client.py - an example client that generates MQTT messages to send to the gateway and listens for resonses in a separate thread - illustrates reading sensors on Thunderboards attached to the gateway.
