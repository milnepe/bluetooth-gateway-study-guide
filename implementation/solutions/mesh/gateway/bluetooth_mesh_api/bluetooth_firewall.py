#!/usr/bin/python3
import json

# temporary
import sys
sys.path.insert(0, '.')

ENABLED = "enabled"
I2MN_ADDRESS_ACCEPTLIST = "i2mn_address_acceptlist"
MN2I_ADDRESS_ACCEPTLIST = "mn2i_address_acceptlist"
ALL_ADDRESSES = "*"

with open('firewall_config.json') as f:
	config = json.load(f)

def firewall_is_enabled():
	if ENABLED in config:
		enabled = config[ENABLED]
		if (enabled):
			return True
		else:
			return False
	else:
		return True

def i2mn_address_allowed(addr):
	global config
	if not firewall_is_enabled():
		return True
	if I2MN_ADDRESS_ACCEPTLIST in config:
		acceptlist = config[I2MN_ADDRESS_ACCEPTLIST]
		if ALL_ADDRESSES in acceptlist:
			return True
		if addr.upper() in acceptlist:
			return True
		else:
			return False
	else:
		return False

def mn2i_address_allowed(addr):
	global config
	if not firewall_is_enabled():
		return True
	if MN2I_ADDRESS_ACCEPTLIST in config:
		acceptlist = config[MN2I_ADDRESS_ACCEPTLIST]
		if ALL_ADDRESSES in acceptlist:
			return True
		if addr.upper() in acceptlist:
			return True
		else:
			return False
	else:
		return False