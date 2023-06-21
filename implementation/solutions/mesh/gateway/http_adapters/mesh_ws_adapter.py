#!/usr/bin/python3
import threading
import json
import sys
sys.path.insert(0, '.')
import gateway_mn2i_node
import bluetooth_firewall

sub_addresses = set()

fo = open("ws_log.txt", "a")
def wslog(line):
	fo.write(line+"\n")
	fo.flush()

def firewall_allows(addr):
	if not bluetooth_firewall.mn2i_address_allowed(addr):
		print('Status: 403 Forbidden')
		print()
		print('Status-Line: HTTP/1.0 403 Forbidden')
		print()
		return False
	else:
		return True

def on_error(err_code, err_message):
	wslog(tid+" error reported: "+str(err_code))
	result = {}
	result['result'] = err_code
	result['message'] = err_message
	sys.stdout.write(json.JSONEncoder().encode(result)+"\n")
	sys.stdout.flush()

def message_dispatcher(dst, sensor_data):
	global sub_addresses
	tid = str(threading.current_thread().ident)
	wslog(tid+" message_dispatcher:"+dst.upper()+" "+sensor_data)

	if (dst.upper() in sub_addresses):
		wslog(tid+" sending sensor_data to subscribed client")
		message = {}
		message['dst'] = dst.upper()
		message['temperature'] = sensor_data
		print(json.JSONEncoder().encode(message))
		sys.stdout.flush()

keep_going = 1
tid = str(threading.current_thread().ident)
gateway_mn2i_node.set_message_dispatcher(message_dispatcher)
gateway_mn2i_node.set_on_error(on_error)

t = threading.Thread(target=gateway_mn2i_node.receive)
t.daemon = True
t.start()

wslog(tid+" starting loop")
while keep_going == 1:
	try:
		line = sys.stdin.readline()
		if len(line) == 0:
		# means websocket has closed
			keep_going = 0
			wslog(tid+" Websocket closed")
			# tell the mesh node application to exit
			gateway_mn2i_node.finished()
		else:
			line = line.strip()
			message = {}
			wslog(tid+" RX> "+line)
			subscription_control = json.loads(line)
			# handle subscribe and unsubscribe requests
			# {"action":"subscribe","dst":"C002"}
			if (subscription_control["action"] == "subscribe"):
				dst_addr = subscription_control["dst"].upper()
				if firewall_allows(dst_addr):
					sub_addresses.add(dst_addr)
					wslog(tid+" subscribed:"+str(sub_addresses))
				# else silently ignore
				else:
					wslog(tid+" firewall denied subscribe request to "+dst_addr)
			elif (subscription_control["action"] == "unsubscribe"):
				sub_addresses.remove(subscription_control["dst"])
				wslog(tid+" unsubscribed:"+str(sub_addresses))
	except Exception as err:
		wslog(tid+" Exception: {0}".format(err))
		gateway_mn2i_node.finished()

# tell the mesh node application to exit
wslog(tid+" Exiting")
gateway_mn2i_node.finished()
sys.stdout.flush()
