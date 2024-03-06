# bluetooth-gateway-study-guide
Debugged version of the Python Bluetooth Internet Gateways Study Guide from Bluetooth SIG V2_0_1

A web BLE gateway based on an embedded HTTP server (Apache2) and WS (Websocketd) with my added MQTT adapter

Tested with ROCK-3C and Silicon Labs Thunderboard Sense (SLTB001A) & Thunderboard EFR32BG22 (SLTB010A)

##OS Installation.

Get latest Debian XFCE image - CLI not working - tested with rock-3c_debian_bullseye_xfce_b42.img.xz

Set systemd default target to CLI:
sudo systemctrl set-default multi-user.target

Update system:
```sudo apt update
sudo apt upgrade
```

Reboot
sudo reboot

**************************************************
##Software.

Install Paho-mqtt in venv:
```sudo apt install python3-dev pkg-config cmake python3-venv
sudo apt install libdbus-1-dev libglib2.0-dev libcairo2-dev libgirepository1.0-dev
```

Install Mosquitto:
```sudo apt install mosquitto mosquitto-clients
```

Setup listeners:
```sudo vi /etc/mosquitto/conf.d/broker.conf

# Enable settings by listener
per_listener_settings true
# Allow anonymous access on port 1883
listener 1883
allow_anonymous true
```
Restart:
```sudo systemctl restart mosquitto.service
```

Copy gateway code:
```git clone https://github.com/milnepe/bluetooth-gateway-study-guide.git
cd bluetooth-gateway-study-guide/implementation/solutions/peripherals/gateway_mqtt_no_security
```

Create virtual env:
```python -m venv venv

source venv/bin/activate
```

Install packages into venv:
```pip install wheel

pip install dbus-python

pip install PyGObject

pip install paho-mqtt
```

******************************************
##Using Bluetoothctl to connect and identify characteristic path.

Open a separate Terminal and start Bluettotctl:
```bluetoothctl


[bluetooth]# scan on
Discovery started
[CHG] Controller 50:5A:65:27:45:D8 Discovering: yes
...
[NEW] Device 9A:61:DA:87:D2:C4 Nano33BLESENSE

[bluetooth]# connect 9A:61:DA:87:D2:C4 
Attempting to connect to 9A:61:DA:87:D2:C4
[CHG] Device 9A:61:DA:87:D2:C4 Connected: yes
Connection successful
[NEW] Primary Service (Handle 0xa504)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service0006
	00001801-0000-1000-8000-00805f9b34fb
	Generic Attribute Profile
...

[Nano33BLESENSE]# menu gatt
Menu gatt:
Available commands:
...

[Nano33BLESENSE]# list-attributes 
Primary Service (Handle 0x17f0)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service0006
	00001801-0000-1000-8000-00805f9b34fb
	Generic Attribute Profile
Characteristic (Handle 0x0001)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service0006/char0007
	00002a05-0000-1000-8000-00805f9b34fb
	Service Changed
Descriptor (Handle 0x0000)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service0006/char0007/desc0009
	00002902-0000-1000-8000-00805f9b34fb
	Client Characteristic Configuration
Primary Service (Handle 0x819c)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a
	0000181a-0000-1000-8000-00805f9b34fb
	Environmental Sensing
Characteristic (Handle 0x7c60)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b
	00002a6e-0000-1000-8000-00805f9b34fb
	Temperature
Descriptor (Handle 0x0000)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b/desc000d
	00002902-0000-1000-8000-00805f9b34fb
	Client Characteristic Configuration
Characteristic (Handle 0x9070)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000e
	00002a6f-0000-1000-8000-00805f9b34fb
	Humidity
Descriptor (Handle 0x0000)
	/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000e/desc0010
	00002902-0000-1000-8000-00805f9b34fb
	Client Characteristic Configuration
```

******************************************************
##Testing.

Start mqtt_client in venv:
```cd gateway
python -m mqtt_client 'localhost' 'test/gateway'
```

Open another Terminal:
Make sure you have scanned and connected your peripheral using Bluetoothctl
Issue mqtt command to get temperature according to characteristic handle for your device - the output shows in the other terminal:

```mosquitto_pub -h localhost -t "test/gateway/in/read_characteristic" -m '{"bdaddr":"9A:61:DA:87:D2:C4", "handle":"/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b"}'
```

Result:
```2024-03-06 11:51:15,249 - Read Characteristic: test/gateway/in/read_characteristic, {"bdaddr":"9A:61:DA:87:D2:C4", "handle":"/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b"}
2024-03-06 11:51:15,357 - {"bdaddr": "9A:61:DA:87:D2:C4", "handle": "/org/bluez/hci0/dev_9A_61_DA_87_D2_C4/service000a/char000b", "cmd": "read_characteristic", "value": "48080000", "result": 0}
```


Convert result:
48080000 -> 0848 = 2120 = 21.20 C

