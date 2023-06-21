#!/usr/bin/env python3
#
# Run from the command line to Join (make available for provisioning) with arg 'join'
# Edit and replace the token value in the getToken() function after provisioning
#
# Invoke from websocketd after provisioning to start a loop which
# will receive sensor client status messages from the mesh network.
# Remember to subscribe this node to the address to which sensor server
# status messages are published!
#
###################################################################

fo = open("mn2i_log.txt", "a")

def log(line):
    fo.write(line+"\n")
    fo.flush()

import sys
import getopt
import struct
import fcntl
import os
import numpy
import random
import dbus
import dbus.service
import dbus.exceptions
import json
import time
import math
import os
import sys
import cgi
import threading
import time
import uuid
import constants
from random import randrange

try:
  from gi.repository import GLib
except ImportError:
  import glib as GLib
from dbus.mainloop.glib import DBusGMainLoop

MESH_SERVICE_NAME = 'org.bluez.mesh'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'

MESH_MGR_IFACE = 'org.bluez.mesh.Management1'
MESH_NETWORK_IFACE = 'org.bluez.mesh.Network1'
MESH_NODE_IFACE = 'org.bluez.mesh.Node1'
MESH_APPLICATION_IFACE = 'org.bluez.mesh.Application1'
MESH_ELEMENT_IFACE = 'org.bluez.mesh.Element1'

AGENT_IFACE = 'org.bluez.mesh.ProvisionAgent1'
AGENT_PATH = "/mesh/test/agent"

# company ID FFFF must not be used in shipping products - see https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers/
APP_COMPANY_ID = 0xffff
APP_PRODUCT_ID = 0x0001
APP_VERSION_ID = 0x0001

VENDOR_ID_NONE = 0xffff

TRANSACTION_TIMEOUT = 6

MN2I_CONFIG = "mn2i_config.json"

app = None
bus = None
mainloop = None
node = None
node_mgr = None
mesh_net = None
dst_addr = None
state = None
rc = None
app_idx = 0
result = {}
message_dispatcher = None
on_error = None

# Node token housekeeping
token = None
token_inx = 0
tokens = None

# Remote device UUID
remote_uuid = None

# OOB provisioning
netkey = None
devkey = None
unicast_addr = 0x0000

send_opts = dbus.Dictionary(signature='sv')
send_opts = {'ForceSegmented' : dbus.Boolean(True)}

PRIMARY = 0

with open(MN2I_CONFIG) as f:
	config = json.load(f)
	tokens = config["tokens"]

def raise_error(str_value):
	log(str_value)

def app_exit():
	global mainloop
	global app

	for el in app.elements:
		for model in el.models:
			if model.timer != None:
				model.timer.cancel()
	log("sent - app_exit is quitting mainloop")
	finished()

def set_token(str_value):
	global token

	if len(str_value) != 16:
		raise_error('Expected 16 digits')
		return

	try:
		input_number = int(str_value, 16)
	except ValueError:
		raise_error('Not a valid hexadecimal number')
		return

	token = numpy.uint64(input_number)

def set_uuid(str_value):
	global remote_uuid

	if len(str_value) != 32:
		raise_error('Expected 32 digits')
		return

	remote_uuid = bytearray.fromhex(str_value)

def set_netkey(str_value):
	global netkey

	if len(str_value) != 32:
		raise_error('Expected 32 hex digits')
		return

	netkey = bytearray.fromhex(str_value)

def set_appkey(str_value):
	global appkey

	if len(str_value) != 32:
		raise_error('Expected 32 hex digits')
		return

	appkey = bytearray.fromhex(str_value)

def set_devkey(str_value):
	global devkey

	if len(str_value) != 32:
		raise_error('Expected 32 hex digits')
		return

	devkey = bytearray.fromhex(str_value)

def array_to_string(b_array):
	str_value = ""
	for b in b_array:
		str_value += "%02x" % b
	return str_value

def generic_error_cb(error):
	log('D-Bus call failed: ' + str(error))

def generic_reply_cb():
	return

def unwrap(item):
	if isinstance(item, dbus.Boolean):
		return bool(item)
	if isinstance(item, (dbus.UInt16, dbus.Int16, dbus.UInt32, dbus.Int32,
						dbus.UInt64, dbus.Int64)):
		return int(item)
	if isinstance(item, dbus.Byte):
		return bytes([int(item)])
	if isinstance(item, dbus.String):
			return item
	if isinstance(item, (dbus.Array, list, tuple)):
		return [unwrap(x) for x in item]
	if isinstance(item, (dbus.Dictionary, dict)):
		return dict([(unwrap(x), unwrap(y)) for x, y in item.items()])

	log('Dictionary item not handled: ' + type(item))

	return item

def interfaces_removed_cb(object_path, interfaces):
	log('Removed')
	if not mesh_net:
		return

	log(object_path)
	if object_path == mesh_net[2]:
		log('Service was removed')
		app_exit()

class ModTimer():
	def __init__(self):
		self.seconds = None
		self.func = None
		self.thread = None
		self.busy = False

	def _timeout_cb(self):
		self.func()
		self.busy = True
		self._schedule_timer()
		self.busy =False

	def _schedule_timer(self):
		self.thread = Timer(self.seconds, self._timeout_cb)
		self.thread.start()

	def start(self, seconds, func):
		self.func = func
		self.seconds = seconds
		if not self.busy:
			self._schedule_timer()

	def cancel(self):
		if self.thread is not None:
			self.thread.cancel()
			self.thread = None

class Agent(dbus.service.Object):
	def __init__(self, bus):
		self.path = AGENT_PATH
		self.bus = bus
		dbus.service.Object.__init__(self, bus, self.path)

	def get_properties(self):
		caps = []
		oob = []
		caps.append('out-numeric')
		caps.append('static-oob')
		oob.append('other')
		return {
			AGENT_IFACE: {
				'Capabilities': dbus.Array(caps, 's'),
				'OutOfBandInfo': dbus.Array(oob, 's')
			}
		}

	def get_path(self):
		return dbus.ObjectPath(self.path)

	@dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
	def Cancel(self):
		log("Cancel")

	@dbus.service.method(AGENT_IFACE, in_signature="su", out_signature="")
	def DisplayNumeric(self, type, value):
		print('DisplayNumeric (', type,') number =', value)

	@dbus.service.method(AGENT_IFACE, in_signature="s", out_signature="ay")
	def PromptStatic(self, type):
		static_key = numpy.random.randint(0, 255, 16)
		key_str = array_to_string(static_key)
		print('PromptStatic (', type, ')')
		print('Enter 16 octet key on remote device: ',key_str);
		return dbus.Array(static_key, signature='y')


# See https://dbus.freedesktop.org/doc/dbus-python/tutorial.html and Exporting Objects
# Application class is a subclass of dbus.service.Object

class Application(dbus.service.Object):

	def __init__(self, bus):
#               log("Constructing Application\n")
		self.path = '/meshsensor'
		self.agent = None
		self.elements = []
		dbus.service.Object.__init__(self, bus, self.path)

	def set_agent(self, agent):
		self.agent = agent

	def get_path(self):
		return dbus.ObjectPath(self.path)

	def add_element(self, element):
		self.elements.append(element)

	def get_element(self, idx):
		for ele in self.elements:
			if ele.get_index() == idx:
				return ele

	def get_properties(self):
		return {
			MESH_APPLICATION_IFACE: {
				'CompanyID': dbus.UInt16(APP_COMPANY_ID),
				'ProductID': dbus.UInt16(APP_PRODUCT_ID),
				'VersionID': dbus.UInt16(APP_VERSION_ID)
			}
		}
# exporting a method:

	@dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
	def GetManagedObjects(self):
		response = {}
		response[self.path] = self.get_properties()
		response[self.agent.get_path()] = self.agent.get_properties()
		for element in self.elements:
			response[element.get_path()] = element.get_properties()
		return response

	@dbus.service.method(MESH_APPLICATION_IFACE,
					in_signature="t", out_signature="")
	def JoinComplete(self, value):
		global token
		global mainloop
		token = value
		print("Node provisioned OK - token="+str(hex(token)))
		log("sent - JoinComplete is quitting mainloop")
		print("Quitting mainloop\n")
		finished()

	@dbus.service.method(MESH_APPLICATION_IFACE,
					in_signature="s", out_signature="")
	def JoinFailed(self, value):
		print('JoinFailed ', value)


class Element(dbus.service.Object):
	PATH_BASE = '/meshsensor/ele'

	def __init__(self, bus, index):
#               log("Constructing Element\n")
		self.path = self.PATH_BASE + format(index, '02x')
		self.models = []
		self.bus = bus
		self.index = index
		dbus.service.Object.__init__(self, bus, self.path)

	def _get_sig_models(self):
		mods = []
		for model in self.models:
			opts = []
			id = model.get_id()
			vendor = model.get_vendor()
			if vendor == VENDOR_ID_NONE:
				mod = (id, opts)
				mods.append(mod)
		return mods

	def _get_v_models(self):
		mods = []
		for model in self.models:
			opts = []
			id = model.get_id()
			v = model.get_vendor()
			if v != VENDOR_ID_NONE:
				mod = (v, id, opts)
				mods.append(mod)
		return mods

	def get_properties(self):
		vendor_models = self._get_v_models()
		sig_models = self._get_sig_models()

		props = {'Index' : dbus.Byte(self.index)}
		props['Models'] = dbus.Array(sig_models, signature='(qa{sv})')
		props['VendorModels'] = dbus.Array(vendor_models,
							signature='(qqa{sv})')
		#log(props)
		return { MESH_ELEMENT_IFACE: props }

	def add_model(self, model):
		model.set_path(self.path)
		self.models.append(model)

	def get_index(self):
		return self.index

	def set_model_config(self, configs):
		for config in configs:
			mod_id = config[0]
			self.update_model_config(mod_id, config[1])

	@dbus.service.method(MESH_ELEMENT_IFACE,
					in_signature="qqvay", out_signature="")
	def MessageReceived(self, source, key, dest, data):
		#log(('Message Received on Element %02x') % self.index, end='')
		#log(', src=', format(source, '04x'), end='')

		if isinstance(dest, dbus.Array):
			dst_str = array_to_string(dest)
			# log(', dst=' + dst_str)

		for model in self.models:
			model.process_message(source, dest, key, data)

	@dbus.service.method(MESH_ELEMENT_IFACE,
					in_signature="qa{sv}", out_signature="")

	def UpdateModelConfiguration(self, model_id, config):
		cfg = unwrap(config)
		log(cfg)
		self.update_model_config(model_id, cfg)

	def update_model_config(self, model_id, config):
		log(('Update Model Config '), end='')
		log(format(model_id, '04x'))
		for model in self.models:
			if model_id == model.get_id():
				model.set_config(config)
				return

	@dbus.service.method(MESH_ELEMENT_IFACE,
					in_signature="", out_signature="")

	def get_path(self):
		return dbus.ObjectPath(self.path)

class Model():
	def __init__(self, model_id):
#               log("Constructing Model\n")
		self.cmd_ops = []
		self.model_id = model_id
		self.vendor = VENDOR_ID_NONE
		self.bindings = []
		self.pub_period = 0
		self.pub_id = 0
		self.path = None
		self.timer = None

	def set_path(self, path):
		self.path = path

	def get_id(self):
		return self.model_id

	def get_vendor(self):
		return self.vendor

	def process_message(self, source, dest, key, data):
		return

	def set_publication(self, period):
		self.pub_period = period

	def send_publication(self, data):
		pub_opts = dbus.Dictionary(signature='sv')

		log('Send publication ', end='')
		log(data)
		node.Publish(self.path, self.model_id, pub_opts, data,
						reply_handler=generic_reply_cb,
						error_handler=generic_error_cb)

	def send_message(self, dest, key, data):
		global send_opts
		log("Model: send_message dest=" +str(dest)+" key="+str(key)+" data="+str(data))

		node.Send(self.path, dest, key, send_opts, data,
						reply_handler=send_reply_cb,
						error_handler=send_error_cb)

	def set_config(self, config):
		if 'Bindings' in config:
			self.bindings = config.get('Bindings')
			log('Bindings: ', end='')
			log(self.bindings)
		if 'PublicationPeriod' in config:
			self.set_publication(config.get('PublicationPeriod'))
			log('Model publication period ', end='')
			log(self.pub_period, end='')
			log(' ms')
		if 'Subscriptions' in config:
			log('Model subscriptions ', end='')
			self.print_subscriptions(config.get('Subscriptions'))
			log()

	def print_subscriptions(self, subscriptions):
		for sub in subscriptions:
			if isinstance(sub, int):
				print('%04x,' % sub, end=' ')

			if isinstance(sub, list):
				label = uuid.UUID(bytes=b''.join(sub))
				print(label, ',', end=' ')

########################
# Sensor Client Model
########################
class SensorClient(Model):
	def __init__(self, model_id):
#               log("Constructing SensorClient\n")
		Model.__init__(self, model_id)
		self.tid = 0
		self.data = None
		self.cmd_ops = { 0x52 } # status

	def process_message(self, source, dest, key, data):
		global message_dispatcher
		datalen = len(data)
		opcode = bytes(data[0:1])[0]
		if (opcode == 0x52):
			format_length_byte = bytes(data[1:2])[0]
			sensor_data_format = (format_length_byte >> 7)
			# only Format A is supported
			if (sensor_data_format == 0):
				sensor_value_length = ((format_length_byte & 0b01111000) >> 3)
				id1 = format_length_byte & 0b00000111
				id2 = bytes(data[2:3])[0]
				property_id = (id1 << 8) | id2
				# only temperature data is supported
				if (property_id == 0x004F):
					# Example: 52084f27 = opcode, format and length, property ID, value
					sensor_value = bytes(data[3:4])[0]
					sensor_value = sensor_value * 0.5
					tid = str(threading.current_thread().ident)
#                                       log(tid+' SensorClient opcode=' + str(hex(opcode)) + ' value=' + str(sensor_value))
					message_dispatcher(format(dest,"x"),str(sensor_value))

def attach_app_ok_cb(node_path, dict_array):
	tid = str(threading.current_thread().ident)
	log(tid+" attach_app_ok_cb "+str(node_path))
	log(tid+' Mesh app attached: '+ node_path)

def attach_app_error_cb(error):
	tid = str(threading.current_thread().ident)
	log(tid+" attach_app_error_cb "+str(error))
	global mainloop
	global token_inx
	token_inx = token_inx + 1
	log(tid+' token_inx=' + str(token_inx))
	if (token_inx < len(tokens)):
		# token was already in use so retry with next in tokens list
		log(tid+' retrying')
		try_to_attach()
	else:
		log(tid+' Failed to register application: ' + str(error)+"")
		global rc
		rc = constants.RESULT_ATTACH_FAILED
		on_error(rc,str(error))
		finished()

def getToken():
	global tokens
	global token_inx
	tid = str(threading.current_thread().ident)
	token = tokens[token_inx]
	log(tid+" Selected token "+token)
	return token

def join_cb():
	log('.....')

def join_error_cb(reason):
	log('Join procedure failed: ', reason)

def join():
	initNode()
	global app
	global mesh_net
	global mainloop
	uuid_bytes = uuid.uuid4().bytes
	uuid_str = array_to_string(uuid_bytes)

	log("Requesting to join network with UUID "+uuid_str)
	mesh_net.Join(app.get_path(), uuid_bytes,
		reply_handler=join_cb,
		error_handler=join_error_cb)
	mainloop = GLib.MainLoop()
	mainloop.run()

def current_milli_time():
	return math.floor(time.time() * 1000)

def try_to_attach():
	global mesh_net
	global app
	global token_inx
	global mainloop
	token = getToken()
	tid = str(threading.current_thread().ident)
	log(tid+" attempting to attach with "+token)
	token_uint64 = numpy.uint64(int(token, 16))
	log(tid+" attempting to attach NOW: app="+str(app)+" mesh_net="+str(mesh_net))
	mesh_net.Attach(app.get_path(), token_uint64,
		reply_handler=attach_app_ok_cb,
		error_handler=attach_app_error_cb)
	if (token_inx == 0):
		log(tid+" starting mainloop")
		mainloop.run()
		log(tid+" mainloop no longer running")

def receive():
	global mainloop
	mainloop = GLib.MainLoop()
	tid = str(threading.current_thread().ident)
	try:
		initNode()
		log(tid+" SENSOR CLIENT")
		log(tid+" -------------")
		log(tid+" receive starting")
		try_to_attach()
	except Exception as err:
		log(tid+" exception in receive(): "+str(err))
		finished()

def finished():
	global mainloop
	fo.close()
	mainloop.quit()

def set_message_dispatcher(dispatcher_fn):
	global message_dispatcher
	message_dispatcher = dispatcher_fn

def set_on_error(error_fn):
	global on_error
	on_error = error_fn

def initNode():
	global bus
	global mesh_net
	global app
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus()
	mesh_net = dbus.Interface(bus.get_object(MESH_SERVICE_NAME,
						"/org/bluez/mesh"),
						MESH_NETWORK_IFACE)
	mesh_net.connect_to_signal('InterfacesRemoved', interfaces_removed_cb)
	app = Application(bus)
	app.set_agent(Agent(bus))

	first_ele = Element(bus, 0x00)
	first_ele.add_model(SensorClient(0x1102))
	app.add_element(first_ele)

tid = str(threading.current_thread().ident)

if __name__ == '__main__':
	if (len(sys.argv) != 2):
		print("Error: incorrect number of arguments specified")
		sys.exit(1)

	cmd = sys.argv[1]
	if (cmd == 'join'):
		join()
	else:
		print("Unrecognised option - join is the only argument supported over the command line")