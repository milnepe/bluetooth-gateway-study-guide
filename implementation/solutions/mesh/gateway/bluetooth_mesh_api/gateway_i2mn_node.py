#!/usr/bin/env python3
#
# Run from the command line to Join (make available for provisioning) with arg 'join'
# Edit and replace the token value in the getToken() function after provisioning
#
# Invoke over HTTP with a suitable JSON object containing args which select and inform the mesh message type to be sent
#
###################################################################

fo = open("i2mn_log.txt", "a")

def log(line):
	fo.write(line+"\n")
	fo.flush()

def byteArrayToHexString(bytes):
	hex_string = ""
	for byte in bytes:
		hex_byte = '%02X' % byte
		hex_string = hex_string + hex_byte
	return hex_string

import sys
sys.path.insert(0, '.')
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
import constants
import threading
from random import randrange

from threading import Timer
from threading import Event
import time
import uuid

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
AGENT_PATH = "/mesh/gateway/agent"

APP_COMPANY_ID = 0x05f1
APP_PRODUCT_ID = 0x0001
APP_VERSION_ID = 0x0001

VENDOR_ID_NONE = 0xffff

TRANSACTION_TIMEOUT = 6

RESULT_MISSING_PARAMETER = 1
RESULT_ATTACH_FAILED = 9

TIMEOUT = 5

I2MN_CONFIG = "i2mn_config.json"

app = None
bus = None
mainloop = None
node = None
node_mgr = None
mesh_net = None
exit = Event()

dst_addr = None
state = None
h_state = None
s_state = None
l_state = None
rc = None
app_idx = 0

# Node token housekeeping
token = None
token_inx = 0
tokens = None
next_action = None

# Remote device UUID
remote_uuid = None

# OOB provisioning
netkey = None
devkey = None
unicast_addr = 0x0000

result_callback_function = None

send_opts = dbus.Dictionary(signature='sv')
send_opts = {'ForceSegmented' : dbus.Boolean(True)}

PRIMARY = 0
GENERIC_ON_OFF_CLIENT = 0
LIGHT_HSL_CLIENT = 1
TEMPERATURE_ID = 0x004F

with open(I2MN_CONFIG) as f:
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
	log("sent - app_exit is finishing")
	fo.close()
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

def send_error_cb(error):
	global mainloop
	log("send_error_cb - ERROR "+str(error))
	log("send_error_cb - finishing")
	finished() 
	result_callback_function(constants.RESULT_SEND_FAILED)

def send_reply_cb():
	global mainloop
	log("send_reply_cb - OK")
	log("send_reply_cb - finising")
	finished() 
	result_callback_function(constants.RESULT_OK)

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
	log('interfaces removed')
	if not mesh_net:
		return

	log(object_path)
	if object_path == mesh_net[2]:
		print('Service was removed')
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
		log("Constructing Agent")
		self.path = AGENT_PATH
		self.bus = bus
		dbus.service.Object.__init__(self, bus, self.path)

	def get_properties(self):
		log("Agent: get_properties")
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
		log("Agent: get_path")
		return dbus.ObjectPath(self.path)

	@dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
	def Cancel(self):
		log("Agent: Cancel")
		print("Cancel")

	@dbus.service.method(AGENT_IFACE, in_signature="su", out_signature="")
	def DisplayNumeric(self, type, value):
		log("Agent: DisplayNumeric")
		print('DisplayNumeric (', type,') number =', value)

	@dbus.service.method(AGENT_IFACE, in_signature="s", out_signature="ay")
	def PromptStatic(self, type):
		log("Agent: PromptStatic")
		static_key = numpy.random.randint(0, 255, 16)
		key_str = array_to_string(static_key)
		print('PromptStatic (', type, ')')
		print('Enter 16 octet key on remote device: ',key_str);
		return dbus.Array(static_key, signature='y')

class Application(dbus.service.Object):

	def __init__(self, bus):
		log("Constructing Application")
		self.path = '/mesh/gateway'
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
		mainloop.quit()
  
	@dbus.service.method(MESH_APPLICATION_IFACE,
					in_signature="s", out_signature="")
	def JoinFailed(self, value):
		print('JoinFailed ', value)


class Element(dbus.service.Object):
	PATH_BASE = '/mesh/gateway/ele'

	def __init__(self, bus, index):
		log("Constructing Element")
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

		if isinstance(dest, dbus.Array):
			dst_str = array_to_string(dest)

		for model in self.models:
			model.process_message(source, dest, key, data)

	@dbus.service.method(MESH_ELEMENT_IFACE,
					in_signature="qa{sv}", out_signature="")

	def UpdateModelConfiguration(self, model_id, config):
		cfg = unwrap(config)
		self.update_model_config(model_id, cfg)

	def update_model_config(self, model_id, config):
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
		log("Constructing Model")
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

		node.Publish(self.path, self.model_id, pub_opts, data,
						reply_handler=generic_reply_cb,
						error_handler=generic_error_cb)

	def send_message(self, dest, key, data):
		global send_opts
		log("Model: send_message dest=" +str(dest)+" key="+str(key)+" data="+byteArrayToHexString(data))

		node.Send(self.path, dest, key, send_opts, data,
						reply_handler=send_reply_cb,
						error_handler=send_error_cb)

	def set_config(self, config):
		if 'Bindings' in config:
			self.bindings = config.get('Bindings')
			print('Bindings: ', end='')
			print(self.bindings)
		if 'PublicationPeriod' in config:
			self.set_publication(config.get('PublicationPeriod'))
			print('Model publication period ', end='')
			print(self.pub_period, end='')
			print(' ms')
		if 'Subscriptions' in config:
			print('Model subscriptions ', end='')
			self.print_subscriptions(config.get('Subscriptions'))
			print()

	def print_subscriptions(self, subscriptions):
		for sub in subscriptions:
			if isinstance(sub, int):
				print('%04x,' % sub, end=' ')

			if isinstance(sub, list):
				label = uuid.UUID(bytes=b''.join(sub))
				print(label, ',', end=' ')

########################
# On Off Client Model
########################
class OnOffClient(Model):
	def __init__(self, model_id):
		log("Constructing OnOffClient")
		Model.__init__(self, model_id)
		self.tid = 0
		self.data = None
		self.cmd_ops = { 0x8201,  # get
				 0x8202,  # set
				 0x8203,  # set unacknowledged
				 0x8204 } # status

	def _send_message(self, dest, key, data):
		self.send_message(dest, key, data)

	def get_state(self, dest, key):
		opcode = 0x8201
		self.data = struct.pack('>H', opcode)
		self._send_message(dest, key, self.data)

	def set_state(self, dest, key, state):
		log("set_state dest="+str(dest)+" state="+str(state)+"\n")
		opcode = 0x8203
		self.data = struct.pack('>HBB', opcode, state, self.tid)
		self.tid = (self.tid + 1) % 255
		self._send_message(dest, key, self.data)

	def repeat(self, dest, key):
		if self.data != None:
			self._send_message(dest, key, self.data)
		else:
			log('No previous command stored')

	def process_message(self, source, dest, key, data):
		datalen = len(data)

		if datalen != 3:
			# The opcode is not recognized by this model
			return

		opcode, state = struct.unpack('>HB',bytes(data))

		if opcode != 0x8204 :
			# The opcode is not recognized by this model
			return

		state_str = "ON"
		if state == 0:
			state_str = "OFF"

		log(state_str, 'from','%04x' % source)

########################
# Light HSL Client Model
# (incomplete implementation for demonstration and education  purposes only)
########################
class LightHslClient(Model):
	def __init__(self, model_id):
		log("Constructing LightHslClient")
		Model.__init__(self, model_id)
		self.tid = 0
		self.data = None
		self.cmd_ops = { 0x826D,  # get
				 0x8276,  # set
				 0x8277,  # set unacknowledged
				 0x8278 } # status

	def _send_message(self, dest, key, data):
		self.send_message(dest, key, data)

	def get_state(self, dest, key):
		print("Light HSL get messages are not supported")
		return

	def set_state(self, dest, key, h_state, s_state, l_state):
		log("set_state dest="+str(dest)+" state="+str(h_state)+" "+str(s_state)+" "+str(l_state) + "\n")
		# Light HSL Set Unacknowledged
		opcode = 0x8277
		# Opcode (16), L (16), H (16), S (16). NB H, S and L must be little endian.	
		# And YES! Order is L, H then S
		h_state_LE = struct.pack('<H', h_state) 
		s_state_LE = struct.pack('<H', s_state) 
		l_state_LE = struct.pack('<H', l_state) 
		self.data = struct.pack('>HBBBBBBB', opcode, l_state_LE[0], l_state_LE[1],h_state_LE[0], h_state_LE[1],s_state_LE[0],s_state_LE[1], self.tid)
		self.tid = (self.tid + 1) % 255
		log("Sending:")
		log(byteArrayToHexString(self.data))
		self._send_message(dest, key, self.data)

	def repeat(self, dest, key):
		if self.data != None:
			self._send_message(dest, key, self.data)
		else:
			log('No previous command stored')

	def process_message(self, source, dest, key, data):
		return

def attach_app_error_cb(error):
	tid = str(threading.current_thread().ident)
	log(tid+" attach_app_error_cb "+str(error))
	global mainloop
	global token_inx
	global next_action
	token_inx = token_inx + 1
	log(tid+' token_inx=' + str(token_inx))
	if (token_inx < len(tokens)):
		# token was already in use so retry with next in tokens list
		log(tid+' retrying')
		try_to_attach_and_then(next_action)
	else:
		log(tid+' Failed to register application: ' + str(error)+"")
		finished()
		result_callback_function(constants.RESULT_ATTACH_FAILED)
 
def node_attached_now_send_onoff(node_path, dict_array):  
	log("node_attached_now_send_onoff")
	global dst_addr
	global app_idx
	global state
  
	obj = bus.get_object(MESH_SERVICE_NAME, node_path)
	global node
	node = dbus.Interface(obj, MESH_NODE_IFACE)
	log("sending to "+str(dst_addr))
	app.elements[PRIMARY].models[GENERIC_ON_OFF_CLIENT].set_state(dst_addr, app_idx, state)

def node_attached_now_send_light_hsl_set(node_path, dict_array):  
	log("node_attached_now_send_light_hsl_set")
	global dst_addr
	global app_idx
	global h_state
	global s_state
	global l_state
  
	obj = bus.get_object(MESH_SERVICE_NAME, node_path)
	global node
	node = dbus.Interface(obj, MESH_NODE_IFACE)
	log("sending to "+str(dst_addr))
	app.elements[PRIMARY].models[LIGHT_HSL_CLIENT].set_state(dst_addr, app_idx, h_state, s_state, l_state)

def try_to_attach_and_then(next):
	global mesh_net
	global app
	global token_inx
	global next_action
	next_action = next
	token = getToken()
	tid = str(threading.current_thread().ident)
	log(tid+" attempting to attach with "+token)
	token_uint64 = numpy.uint64(int(token, 16))
	log(tid+" attempting to attach NOW: app="+str(app)+" mesh_net="+str(mesh_net))
	mesh_net.Attach(app.get_path(), token_uint64,
		reply_handler=next,
		error_handler=attach_app_error_cb)
	if (token_inx == 0):
		log(tid+" starting mainloop")
		mainloop.run()
		log(tid+" mainloop no longer running")

def initNode():
	global bus
	global mesh_net
	global app
	global mainloop
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus()
	mesh_net = dbus.Interface(bus.get_object(MESH_SERVICE_NAME,
						"/org/bluez/mesh"),
						MESH_NETWORK_IFACE)
	mesh_net.connect_to_signal('InterfacesRemoved', interfaces_removed_cb)
	app = Application(bus)
	app.set_agent(Agent(bus))

	first_ele = Element(bus, 0x00)
	first_ele.add_model(OnOffClient(0x1001))
	first_ele.add_model(LightHslClient(0x1309))
	app.add_element(first_ele)
	global mainloop
	mainloop = GLib.MainLoop()

def send_light_hsl_set(dst_addr_hex, h_hex, s_hex, l_hex, cb_function):
	t = threading.Thread(target=timeout)
	t.start()
	global result_callback_function
	global dst_addr
	global h_state
	global s_state
	global l_state
	log("send_light_hsl_set("+dst_addr_hex+","+h_hex+","+s_hex+","+l_hex+")")
	initNode()
	dst_addr_int = int(dst_addr_hex, 16)
	dst_addr = numpy.uint16(dst_addr_int)
	h_state = numpy.uint16(int(h_hex,16))
	s_state = numpy.uint16(int(s_hex,16))
	l_state = numpy.uint16(int(l_hex,16))
	result_callback_function = cb_function
	log(constants.ACTION_LIGHT_HSL_SET_UNACK+ " action starting")
	try_to_attach_and_then(node_attached_now_send_light_hsl_set)
	return constants.RESULT_OK

def send_onoff(dst_addr_str, state_str, cb_function):
	t = threading.Thread(target=timeout)
	t.start()
	global result_callback_function
	global dst_addr
	global state
	initNode()
	dst_addr_int = int(dst_addr_str, 16)
	dst_addr = numpy.uint16(dst_addr_int)
	state = numpy.uint8(int(state_str))
	result_callback_function = cb_function
	log(constants.ACTION_GENERIC_ON_OFF_SET_UNACK+ " action starting")
	try_to_attach_and_then(node_attached_now_send_onoff)
	return constants.RESULT_OK

def current_milli_time():
	return math.floor(time.time() * 1000)

def getToken():
	global tokens
	global token_inx
	tid = str(threading.current_thread().ident)
	token = tokens[token_inx]
	log(tid+" Selected token "+token)
	return token

def join_cb():
	print('.....')

def join_error_cb(reason):
	print('Join procedure failed: ', reason)

def join():
	initNode()
	global app
	global mesh_net
	global mainloop
	uuid_bytes = uuid.uuid4().bytes
	uuid_str = array_to_string(uuid_bytes)

	print("Requesting to join network with UUID "+uuid_str)
	mesh_net.Join(app.get_path(), uuid_bytes,
		reply_handler=join_cb,
		error_handler=join_error_cb) 
	mainloop = GLib.MainLoop()
	mainloop.run()

def finished():
	global exit
	log("finished")
	exit.set()

def timeout():
	global mainloop
	log("waiting for finish signal or timeout")
	exit.wait(TIMEOUT)
	log("quitting mainloop")
	mainloop.quit()
# ------------------------------------

if __name__ == '__main__':
	if (len(sys.argv) != 2):
		print("Error: incorrect number of arguments specified")
		sys.exit(1)

	cmd = sys.argv[1]
	if (cmd == 'join'):
		join()
	else:
		print("Unrecognised option - join is the only argument supported over the command line")
