#!/usr/bin/env python3
#
# Invoke over HTTP with a suitable JSON object containing args which select and inform the mesh message type to be sent
# by the gateway_i2mn_node script.
#
###################################################################
import sys
sys.path.insert(0, '.')
import json
import os
import sys
import cgi
import constants
import gateway_i2mn_node
import bluetooth_firewall

fo = open("http_log.txt", "a")

def log(line):
	fo.write(line+"\n")
	fo.flush()

dst_addr = None
state = None
rc = None
result = {}

def json_content_type():
	print("Content-Type: application/json;charset=utf-8")
	print()

def result_cb(rc):
	result['result'] = rc
	json_content_type()
	print(json.JSONEncoder().encode(result))

def firewall_allows(addr):
	if not bluetooth_firewall.i2mn_address_allowed(addr):
		print('Status: 403 Forbidden')
		print()
		print('Status-Line: HTTP/1.0 403 Forbidden')
		print()
		return False
	else:
		return True

log("------------------")
if 'REQUEST_METHOD' in os.environ:
	args = json.load(sys.stdin)
	if (os.environ['REQUEST_METHOD'] != 'PUT'):
		print('Status: 405 Method Not Allowed')
		print()
		print("Status-Line: HTTP/1.0 405 Method Not Allowed")
	else:
		log("PUT")
		if (not "action" in args):
			json_content_type()
			result['result'] = constants.RESULT_ERR_BAD_ARGS
			print(json.JSONEncoder().encode(result))
		elif (args["action"] != constants.ACTION_GENERIC_ON_OFF_SET_UNACK and args["action"] != constants.ACTION_LIGHT_HSL_SET_UNACK):
			json_content_type()
			result['result'] = constants.RESULT_ERR_NOT_SUPPORTED
			print(json.JSONEncoder().encode(result))
		elif (args["action"] == constants.ACTION_GENERIC_ON_OFF_SET_UNACK):
			log("generic on off set unack action")
			if (not "state" in args or not "dst_addr" in args):
				json_content_type()
				result['result'] = constants.RESULT_ERR_BAD_ARGS
				print(json.JSONEncoder().encode(result))
			else:
				action = args["action"]
				log(constants.ACTION_GENERIC_ON_OFF_SET_UNACK+ " preparing arguments")
				dst_addr = args["dst_addr"]
				if firewall_allows(dst_addr):
					state = args["state"]
					result['dst_addr'] = dst_addr
					result['state'] = state
					log("calling gateway_i2mn_node.send_onoff()")
					rc = gateway_i2mn_node.send_onoff(dst_addr, state, result_cb)
					result['result'] = rc
					if (rc != constants.RESULT_OK):
						json_content_type()
						print(json.JSONEncoder().encode(result))
				else:
					log("firewall denied use of address "+dst_addr)
		elif (args["action"] == constants.ACTION_LIGHT_HSL_SET_UNACK):
			log("light HSL set unack action")
			if (not "h_state" in args or not "s_state" in args or not "l_state" in args or not "dst_addr" in args):
				result['result'] = constants.RESULT_ERR_BAD_ARGS
				json_content_type()
				print(json.JSONEncoder().encode(result))
			else:
				action = args["action"]
				log(constants.ACTION_LIGHT_HSL_SET_UNACK+ " preparing arguments")
				dst_addr = args["dst_addr"]
				if firewall_allows(dst_addr):
					h_state = args["h_state"]
					s_state = args["s_state"]
					l_state = args["l_state"]
					result['dst_addr'] = dst_addr
					result['h_state'] = h_state
					result['s_state'] = s_state
					result['l_state'] = l_state
					log("calling gateway_i2mn_node.send_light_hsl_set()")
					rc = gateway_i2mn_node.send_light_hsl_set(dst_addr, h_state, s_state, l_state, result_cb)
					result['result'] = rc
					if (rc != constants.RESULT_OK):
						json_content_type()
						print(json.JSONEncoder().encode(result))
				else:
					log("firewall denied use of address "+dst_addr)
		else:
			json_content_type()
			result['result'] = constants.RESULT_ERR_NOT_SUPPORTED
			print(json.JSONEncoder().encode(result))
	log("exiting script")
else:
	print("ERROR: Not called by HTTP")
