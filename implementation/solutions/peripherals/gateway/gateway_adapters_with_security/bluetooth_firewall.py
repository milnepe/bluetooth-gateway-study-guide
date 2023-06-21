#!/usr/bin/python3
import json

# temporary
import sys
sys.path.insert(0, '../bluetooth')
import bluetooth_gap
import bluetooth_gatt

ENABLED = "enabled"
PAIRED_DEVICES_ONLY = "paired_devices_only"
DEVICE_ACCEPTLIST = "device_acceptlist"
SERVICE_UUID = "service_uuid"
CHARACTERISTIC_UUID = "characteristic_uuid"
DESCRIPTOR_UUID = "descriptor_uuid"
ALL_DEVICES = "*"


with open('config.json') as f:
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

def device_allowed(bdaddr, config):
    if not firewall_is_enabled():
        return True
    if DEVICE_ACCEPTLIST in config:
        acceptlist = config[DEVICE_ACCEPTLIST]
        if ALL_DEVICES in acceptlist:
            return True
        if bdaddr in acceptlist:
            return True
        else:
            return False
    else:
        return False

def service_blocked(service_uuid, rule):
    if not firewall_is_enabled():
        return False    
    if SERVICE_UUID in rule:
        if service_uuid.lower() == rule.get(SERVICE_UUID).lower():
            return True
    return False					
			
def service_allowed(bdaddr, service_uuid, config):
    if not firewall_is_enabled():
        return True
    if not device_allowed(bdaddr, config):
        # print(bdaddr + " " + service_uuid + " blocked because device " + bdaddr + " is not allowed")
        return False
    if ALL_DEVICES in config:
        all_devices_rejectlist = config[ALL_DEVICES]
        for rule in all_devices_rejectlist:
            # is service UUID included in the All Devices rule?
            if SERVICE_UUID in rule and CHARACTERISTIC_UUID not in rule:
                if service_blocked(service_uuid, rule):
                    # print(bdaddr + " " + service_uuid + " blocked by ALL DEVICES service rule " + str(rule))
                    return False
                    
    if bdaddr in config:
        device_uuid_rejectlist = config.get(bdaddr)
        for rule in device_uuid_rejectlist:
            # is service UUID included in the device-specific rule?
            if SERVICE_UUID in rule and CHARACTERISTIC_UUID not in rule:
                if service_blocked(service_uuid, rule):
                    # print(bdaddr + " " + service_uuid + " blocked by device-specific service rule " + str(rule))
                    return False
		
    return True

def characteristic_blocked(service_uuid, characteristic_uuid, rule):
    if not firewall_is_enabled():
        return False
  #  print("characteristic_blocked: " + service_uuid + " " +characteristic_uuid + " " + str(rule))
	# characteristic in this service
    if SERVICE_UUID in rule and CHARACTERISTIC_UUID in rule:
        if service_uuid.lower() == rule.get(SERVICE_UUID).lower() and characteristic_uuid.lower() == rule.get(CHARACTERISTIC_UUID).lower():
            return True
    # characteristic in any service        
    if SERVICE_UUID not in rule and CHARACTERISTIC_UUID in rule:
        if characteristic_uuid.lower() == rule.get(CHARACTERISTIC_UUID).lower():
            return True
    return False					

def characteristic_allowed(bdaddr, service_uuid, characteristic_uuid, config):
    if not firewall_is_enabled():
        return True
    if not device_allowed(bdaddr, config):
        # print(bdaddr + " " + service_uuid + " blocked because device " + bdaddr + " is not allowed")
        return False
	# if the service is not allowed then neither is any characteristic or descriptor which it contains
    if not service_allowed(bdaddr, service_uuid, config):
        # print(bdaddr + " " + service_uuid + "/"+ characteristic_uuid + " blocked because service not allowed")
        return False
		
    if ALL_DEVICES in config:
        all_devices_rejectlist = config[ALL_DEVICES]
        for rule in all_devices_rejectlist:
            if characteristic_blocked(service_uuid, characteristic_uuid, rule):
                return False
					
    if bdaddr in config:
        device_uuid_rejectlist = config[bdaddr]
        for rule in device_uuid_rejectlist:
            if characteristic_blocked(service_uuid, characteristic_uuid, rule):
                return False
					
    return True

def descriptor_blocked(service_uuid, characteristic_uuid, descriptor_uuid, rule):
    if not firewall_is_enabled():
        return False
	# descriptor attacted to this characteristic in this service
    if SERVICE_UUID in rule and CHARACTERISTIC_UUID in rule and DESCRIPTOR_UUID in rule:
        if service_uuid.lower() == rule.get(SERVICE_UUID).lower() and characteristic_uuid.lower() == rule.get(CHARACTERISTIC_UUID).lower() and descriptor_uuid.lower() == rule.get(DESCRIPTOR_UUID).lower():
            return True
            
	# descriptor attached to this characteristic in any service
    if SERVICE_UUID not in rule and CHARACTERISTIC_UUID in rule and DESCRIPTOR_UUID in rule:
        if characteristic_uuid.lower() == rule.get(CHARACTERISTIC_UUID).lower() and descriptor_uuid.lower() == rule.get(DESCRIPTOR_UUID).lower():
            return True

	# descriptor attached to any characteristic in any service
    if SERVICE_UUID not in rule and CHARACTERISTIC_UUID not in rule and DESCRIPTOR_UUID in rule:
        if descriptor_uuid.lower() == rule.get(DESCRIPTOR_UUID).lower():
            return True

    return False					
	
def descriptor_allowed(bdaddr, service_uuid, characteristic_uuid, descriptor_uuid, config):
    if not firewall_is_enabled():
        return True
    if not device_allowed(bdaddr, config):
        # print(bdaddr + " " + descriptor_uuid + " blocked because device " + bdaddr + " is not allowed")
        return False
	# if the service is not allowed then neither is any characteristic or descriptor which it contains
    if not service_allowed(bdaddr, service_uuid, config):
        # print(bdaddr + " " + service_uuid + "/"+ characteristic_uuid + "/" + descriptor_uuid + " blocked because service not allowed")
        return False
	# if the characteristic is not allowed then neither is any descriptor which it contains
    if not characteristic_allowed(bdaddr, service_uuid, characteristic_uuid, config):
        # print(bdaddr + " " + service_uuid + "/"+ characteristic_uuid + "/" + descriptor_uuid + " blocked because characteristic not allowed")
        return False
		
    if ALL_DEVICES in config:
        all_devices_rejectlist = config[ALL_DEVICES]
        for rule in all_devices_rejectlist:
            if descriptor_blocked(service_uuid, characteristic_uuid, descriptor_uuid, rule):
                return False

    if bdaddr in config:
        # print("XXXX found device rules")
        device_uuid_rejectlist = config[bdaddr]
        for rule in device_uuid_rejectlist:
            if descriptor_blocked(service_uuid, characteristic_uuid, descriptor_uuid, rule):
                return False
					
    return True				
    
def descriptor_is_allowed(bdaddr, descriptor_handle):
    if not firewall_is_enabled():
        return True
    descriptor_uuid = bluetooth_gatt.get_descriptor_uuid(bdaddr, descriptor_handle)
    parent_uuids = bluetooth_gatt.get_owning_uuids(bdaddr, descriptor_handle)    
    return descriptor_allowed(bdaddr, parent_uuids[0], parent_uuids[1], descriptor_uuid, config)
    
def characteristic_is_allowed(bdaddr, characteristic_handle):
    if not firewall_is_enabled():
        return True
    characteristic_uuid = bluetooth_gatt.get_characteristic_uuid(bdaddr, characteristic_handle)
    service_uuid = bluetooth_gatt.get_owning_service_uuid(bdaddr, characteristic_handle)
    return characteristic_allowed(bdaddr, service_uuid, characteristic_uuid, config)
    
def device_is_allowed(bdaddr):
    if not firewall_is_enabled():
        return True
    return device_allowed(bdaddr, config)

def filter_devices(device_list):
    if not firewall_is_enabled():
        return device_list
    allowed = []
    for device in device_list:
        if device_allowed(device.get('bdaddr'),config):
          uuids = device.get("UUIDs")
          allowed_uuids = []
          for uuid in uuids:
              if service_allowed(device.get("bdaddr"), uuid,config):
                  allowed_uuids.append(uuid)
          device["UUIDs"] = allowed_uuids
          allowed.append(device)
    return allowed

def filter_services(bdaddr, service_list):
    if not firewall_is_enabled():
        return service_list
    allowed = []  
    for service in service_list:
        if service_allowed(bdaddr, service.get("UUID"), config):
          allowed.append(service)
    return allowed

def filter_characteristics(bdaddr, service_uuid, characteristics_list):
    if not firewall_is_enabled():
        return characteristics_list
    allowed = []  
    for characteristic in characteristics_list:
        if characteristic_allowed(bdaddr, service_uuid, characteristic.get("UUID"), config):
          allowed.append(characteristic)
    return allowed

def filter_descriptors(bdaddr, service_uuid, characteristic_uuid, descriptors_list):
    if not firewall_is_enabled():
        return descriptors_list
    allowed = []  
    for descriptor in descriptors_list:
        if descriptor_allowed(bdaddr, service_uuid, characteristic_uuid, descriptor.get("UUID"), config):
          allowed.append(descriptor)
    return allowed
  
def list_devices(device_list):
    for device in device_list:
        name = "no name"
        if "name" in device:
            name = device.get("name")
        print(device.get("bdaddr") + " " + name + " UUIDs: " + str(device.get("UUIDs")))

def list_attributes(attribute_list):
    for attribute in attribute_list:
        print(attribute.get("UUID"))

def test1():
    devices_discovered = bluetooth_gap.discover_devices(3)
    print("DISCOVERED")
    print("----------")
    list_devices(devices_discovered)
    allowed = filter_devices(devices_discovered)
    print("ALLOWED")
    print("-------")
    list_devices(allowed)

def test2():
    bdaddr = "D9:64:36:0E:87:01"
    bluetooth_gap.connect(bdaddr)
    services_discovered = bluetooth_gatt.get_services(bdaddr)
    print("DISCOVERED")
    print("----------")
    list_attributes(services_discovered)
    # filter services through the firewall rules
    allowed_services = filter_services(bdaddr, services_discovered)
    print("ALLOWED")
    print("-------")
    list_attributes(allowed_services)

def test3():
    bdaddr = "D9:64:36:0E:87:01"
    bluetooth_gap.connect(bdaddr)
    services_discovered = bluetooth_gatt.get_services(bdaddr)
    # filter services through the firewall rules
    allowed_services = filter_services(bdaddr, services_discovered)
    for service in allowed_services:
        # rename BlueZ-specific parameter name to the more abstract 'handle'
        service['handle'] = service.pop('path')
        characteristics_discovered = bluetooth_gatt.get_characteristics(bdaddr, service['handle'])
        print()
        print("DISCOVERED for service " + service['UUID'])
        print("----------")
        list_attributes(characteristics_discovered)
        # filter characteristics through the firewall rules
        allowed_characteristics = filter_characteristics(bdaddr, service['UUID'], characteristics_discovered)
        print()
        print("ALLOWED for service " + service['UUID'])
        print("-------")
        list_attributes(allowed_characteristics)
        service['characteristics'] = allowed_characteristics

def test4():
    bdaddr = "D9:64:36:0E:87:01"
    bluetooth_gap.connect(bdaddr)
    services_discovered = bluetooth_gatt.get_services(bdaddr)
    # filter services through the firewall rules
    allowed_services = filter_services(bdaddr, services_discovered)
    for service in allowed_services:
        # rename BlueZ-specific parameter name to the more abstract 'handle'
        service['handle'] = service.pop('path')
        characteristics_discovered = bluetooth_gatt.get_characteristics(bdaddr, service['handle'])
        # filter characteristics through the firewall rules
        allowed_characteristics = filter_characteristics(bdaddr, service['UUID'], characteristics_discovered)
        service['characteristics'] = allowed_characteristics
        for characteristic in allowed_characteristics:
          # rename BlueZ-specific parameter name to the more abstract 'handle'
          characteristic['handle'] = characteristic.pop('path')
          descriptors_discovered = bluetooth_gatt.get_descriptors(bdaddr, characteristic['handle'])
          print()
          print("DISCOVERED for characteristic " + characteristic['UUID'])
          print("----------")
          list_attributes(descriptors_discovered)
          # filter descriptors through the firewall rules
          allowed_descriptors = filter_descriptors(bdaddr, service['UUID'], characteristic['UUID'], descriptors_discovered)
          print()
          print("ALLOWED for characteristic " + characteristic['UUID'])
          print("-------")
          list_attributes(allowed_descriptors)
          characteristic['descriptors'] = allowed_descriptors
            

def test5():
    bdaddr = "D9:64:36:0E:87:01"
    bluetooth_gap.connect(bdaddr)
    # service is blocked so characteristic will be as well
    char_path = "/org/bluez/hci0/dev_D9_64_36_0E_87_01/service0008/char0009"
    allowed = characteristic_is_allowed(bdaddr, char_path)
    print("Access to characteristic " + bluetooth_gatt.get_characteristic_uuid(bdaddr,char_path) + " is allowed? " + str(allowed))
    # characteristic is blocked
    char_path = "/org/bluez/hci0/dev_D9_64_36_0E_87_01/service002c/char0030"
    allowed = characteristic_is_allowed(bdaddr, char_path)
    print("Access to characteristic " + bluetooth_gatt.get_characteristic_uuid(bdaddr,char_path) + " is allowed? " + str(allowed))
    # characteristic is allowed
    char_path = "/org/bluez/hci0/dev_D9_64_36_0E_87_01/service0032/char0036"
    allowed = characteristic_is_allowed(bdaddr, char_path)
    print("Access to characteristic " + bluetooth_gatt.get_characteristic_uuid(bdaddr,char_path) + " is allowed? " + str(allowed))
    
  
def test6():
    bdaddr = "D9:64:36:0E:87:01"
    bluetooth_gap.connect(bdaddr)
    desc_path = "/org/bluez/hci0/dev_D9_64_36_0E_87_01/service0008/char0009/desc000b"
    allowed = descriptor_is_allowed(bdaddr, desc_path)
    print("Access to descriptor " + bluetooth_gatt.get_descriptor_uuid(bdaddr,desc_path) + " is allowed? " + str(allowed))
    
def test7():
    if firewall_is_enabled():
        print("FIREWALL IS ENABLED")
    else:
        print("FIREWALL IS DISABLED")