var device_list_hidden = false;
var device_controller_hidden = true;

var devices;
var selected_device;
var selected_device_inx;

var services; // and characteristics 2-dimensional array

// contains a list of handles
var handle_map = new Map([
]);

// maps handles to websocket objects
var ws_map = new Map([
]);

var write_form;
var close_form;
var selected_service_inx;
var selected_characteristic_inx;

function onCamera() {
    let params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=400,height=300`;
    window.open('camera.html','camera',params);
}

function setElementVisibility(id, hidden) {
    var elem = element(id);
    if (hidden) {
	elem.style.display = 'none';
    } else {
	elem.style.display = 'block'
    }
}

function hideAll() {
    device_list_hidden = true;
    device_controller_hidden = true;
}

function setDivVisibility() {
    setElementVisibility('device_list', device_list_hidden);
    setElementVisibility('device_controller', device_controller_hidden);
}

function onDeviceList() {
    hideAll();
    device_list_hidden = false;
    setDivVisibility();   
}

function toggleConnectionState(device_inx) {
    console.log("onConnect: "+devices[device_inx].bdaddr);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	    // console.log(this.responseText);
	      result = JSON.parse(this.responseText);
	      message(result_string(result.result));
	      if (result.result == 0) {
                  if (devices[device_inx].connected == 0) {
		      element(devices[device_inx].state_cell_id).innerHTML = "connected"
		      element(devices[device_inx].action_id).text = "disconnect"
		      devices[device_inx].connected = 1;
		  } else {
		      element(devices[device_inx].state_cell_id).innerHTML = "disconnected"
		      element(devices[device_inx].action_id).text = "connect"
		      devices[device_inx].connected = 0;
		  }
		  selected_device = devices[device_inx];
		  selected_device_inx = device_inx;
		  onDeviceSelected(device_inx)
	      }
        }
    };
    var target = "do_connect.py";
    var info = "connecting..";
    if (devices[device_inx].connected == 1) {
	    target = "do_disconnect.py";
	    info = "disconnecting...";
    }
    var args = {};
    args.bdaddr = devices[device_inx].bdaddr;
    var json = JSON.stringify(args);
    console.log(json);
    xhttp.open("PUT", CGI_ROOT+target, true);
    xhttp.setRequestHeader('Content-type','application/json; charset=utf-8');
    xhttp.send(json);
    message(info);
    return false;
    
}

function attribute_type_style(att_type) {
    if (att_type == "S") {
	return "gatt_service";
    }
    if (att_type == "C") {
	return "gatt_characteristic";
    }
    if (att_type == "D") {
	return "gatt_descriptor";
    }
    return "";
}

function showAttribute(inx, att_type, uuid, att_name, att_props, att_value, format_links) {
    var tbl = element("tbl_services");
    if (tbl != undefined) {
        var row_count = tbl.rows.length;
        var rows = tbl.rows;
        var new_row;
        new_row = tbl.insertRow(row_count);
	new_row.className = attribute_type_style(att_type);
        var formats_cell = new_row.insertCell(0);
        var att_value_cell = new_row.insertCell(0);
        var att_props_cell = new_row.insertCell(0);
        var att_name_cell = new_row.insertCell(0);
        var uuid_cell = new_row.insertCell(0);
        var att_type_cell = new_row.insertCell(0);
	formats_cell.innerHTML = format_links;
        att_type_cell.innerHTML = att_type;
	uuid_cell.innerHTML = uuid;
	att_name_cell.innerHTML = att_name;
	att_props_cell.innerHTML = att_props;
	att_value_cell.innerHTML = att_value;
    }
};

function toggleButton(service_inx,characteristic_inx, current_state) {
    var elem = element("btn_notify_"+service_inx+"_"+characteristic_inx);
    if (current_state == false) {
	if (elem.innerHTML.startsWith("notify")) {
	    console.log("notify off");
	    element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).innerHTML = "notify off";
	} else {
	    console.log("indicate off");
	    element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).innerHTML = "indicate off";
	}
	element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).className = "characteristic_button_off";   
    } else {
	if (elem.innerHTML.startsWith("notify")) {
	    console.log("notify on");
	    element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).innerHTML = "notify on";
	} else {
	    console.log("indicate on");
	    element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).innerHTML = "indicate on";
	}
	element("btn_notify_"+this_service_inx+"_"+this_characteristic_inx).className = "characteristic_button";   
    }	
}

function on_characteristic_indicate(service_inx, characteristic_inx) {
    on_characteristic_notify(service_inx, characteristic_inx);
}

function on_characteristic_notify(service_inx, characteristic_inx) {
    var handle = services[service_inx].characteristics[characteristic_inx].handle;
    var characteristic = services[service_inx].characteristics[characteristic_inx];
    var ws;

    if (characteristic.notifying == false) {
	console.log("enabling...");
        ws = new WebSocket(NOTIFICATIONS_SERVER);
	ws.onerror = function(event) {
	    err = "ERROR: Web Socket for notification control and transport is not available";
	    message(err);
	    console.log(err);
	    alert(err);
	};
	
	ws.onopen = function(e) {
	    // enable notifications
	    console.log(JSON.stringify(characteristic));
	    var control_message = {
		"bdaddr" : selected_device.bdaddr,
		"handle" : characteristic.handle,
		"command" : NOTIFICATIONS_ON
	    };
	    console.log(JSON.stringify(control_message));
	    ws.send(JSON.stringify(control_message));
	}

	ws.onmessage = function(event) {
	    result = JSON.parse(event.data);
	    console.log("onmessage: "+JSON.stringify(result));
	    if (result.value !== undefined) {
		var attribute_indices = handle_map.get(result.handle);
		this_service_inx = attribute_indices[0];
		this_characteristic_inx = attribute_indices[1];
		characteristic = services[this_service_inx].characteristics[this_characteristic_inx];
		// convert to byte array from hex format and store
		characteristic.value = hexToBytes(result.value);
		var display_value = convertFromHex(result.value,characteristic.format);
		element("char_val_"+this_service_inx+"_"+this_characteristic_inx).value = display_value;
	    } else if (result.result == 0) {
		var attribute_indices = handle_map.get(result.handle);
		this_service_inx = attribute_indices[0];
		this_characteristic_inx = attribute_indices[1];
		characteristic = services[this_service_inx].characteristics[this_characteristic_inx];
		toggleButton(this_service_inx,this_characteristic_inx,characteristic.notifying);
		if (characteristic.notifying == false) {
		    console.log("notifications enabled OK");
		    characteristic.notifying = true;
	        } else {
		    console.log("notifications disabled OK");
		    characteristic.notifying = false;
		    ws.close();
		    ws_map.delete(handle);
		}
	    } else {
                    message(error[result.result]);
	    }
	};
	
	ws_map.set(handle,ws);
	
    } else {
        console.log("disabling...");
        ws = ws_map.get(handle);
        console.log(ws);
        var control_message = {
            "bdaddr" : selected_device.bdaddr,
            "handle" : characteristic.handle,
            "command" : NOTIFICATIONS_OFF
        };
        console.log(JSON.stringify(control_message));
        ws.send(JSON.stringify(control_message));
    }
    

}

function on_characteristic_wwr(service_inx, characteristic_inx) {
    console.log("on_characteristic_wwr(" + service_inx+","+characteristic_inx+")");
    show_write_form(service_inx, characteristic_inx);
}

function on_characteristic_write(service_inx, characteristic_inx) {
    console.log("on_characteristic_write(" + service_inx+","+characteristic_inx+")");
    show_write_form(service_inx, characteristic_inx);
}

function show_write_form(service_inx, characteristic_inx) {
    console.log("show_write_form("+service_inx+","+characteristic_inx+")");
    // Get the write_form
    write_form = document.getElementById("write_form");

    // Get the <span> element that closes the modal
    close_form = document.getElementById("close_form");

    // When the user clicks on <span> (x), close the modal
    close_form.onclick = function() {
      console.log("close form");
      write_form.style.display = "none";
      close_form.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
      if (event.target == close_form) {
        write_form.style.display = "none";
	close_form.style.display = "none";
      }
    }  
    
    selected_service_inx = service_inx;
    selected_characteristic_inx = characteristic_inx;
    element("write_uuid").innerHTML = services[service_inx].characteristics[characteristic_inx].UUID;
    element("write_name").innerHTML = unknown(uuid_names.get(services[service_inx].characteristics[characteristic_inx].UUID));
    var current_value = services[service_inx].characteristics[characteristic_inx].value;
    if (current_value !== undefined) {
        element("write_value").value = "0x" + bytesToHex(services[service_inx].characteristics[characteristic_inx].value);
    } else {
	element("write_value").value = "";
    }
    write_form.style.display = "block";
    close_form.style.display = "block";
}


function onSubmitWrite() {
    console.log("onSubmitWrite: "+services[selected_service_inx].characteristics[selected_characteristic_inx].UUID);
    var input_value = element("write_value").value;
    var format_list = document.getElementById("write_formats");
    var format = format_list.options[format_list.selectedIndex].value;
    // close form
    write_form.style.display = "none";
    close_form.style.display = "none";    
    
    value_bytes = convertToBytes(input_value, format); 
    value_hex = bytesToHex(value_bytes); 

    var characteristic = services[selected_service_inx].characteristics[selected_characteristic_inx];
    
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      console.log(this.responseText);
	      result = JSON.parse(this.responseText);
	      characteristic.value = value_bytes;
	      message(result_string(result.result));
	      if (result.result == 0) {
		  value_hex = "0x" + value_hex;
  		  var attribute_indices = handle_map.get(characteristic.handle);
		  this_service_inx = attribute_indices[0];
		  this_characteristic_inx = attribute_indices[1];
		  element("char_val_"+this_service_inx+"_"+this_characteristic_inx).value = value_hex;
		  set_format_hex(this_service_inx,this_characteristic_inx);
	      }
        }
    };

    var args = {};
    args.bdaddr = selected_device.bdaddr;
    args.handle = characteristic.handle;
    args.value = value_hex
    var json = JSON.stringify(args);
    console.log(json);

    var target = "do_write_characteristic.py";
    var info = "writing..";

    xhttp.open("PUT", CGI_ROOT+target, true);
    xhttp.setRequestHeader('Content-type','application/json; charset=utf-8');
    xhttp.send(json);
    message(info);   
}

function input_id(service_inx, characteristic_inx) { 
    return id="char_val_"+service_inx+"_"+characteristic_inx;    
}

function format_value(service_inx, characteristic_inx) {
    if (services[service_inx].characteristics[characteristic_inx].format == FORMAT_HEX) {
        element(input_id(service_inx, characteristic_inx)).value = "0x" + bytesToHex(services[service_inx].characteristics[characteristic_inx].value);
    } else if (services[service_inx].characteristics[characteristic_inx].format == FORMAT_NLE) {
	element(input_id(service_inx, characteristic_inx)).value = bytesToIntLE(services[service_inx].characteristics[characteristic_inx].value);
    } else if (services[service_inx].characteristics[characteristic_inx].format == FORMAT_NBE) {
	element(input_id(service_inx, characteristic_inx)).value = bytesToIntBE(services[service_inx].characteristics[characteristic_inx].value);
    } else if (services[service_inx].characteristics[characteristic_inx].format == FORMAT_STR) {
	element(input_id(service_inx, characteristic_inx)).value = bytesToString(services[service_inx].characteristics[characteristic_inx].value);
    } 
}

function on_format_hex(service_inx, characteristic_inx) {
    var btn_hex_id ="btn_hex"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nle_id ="btn_nle"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nbe_id ="btn_nbe"+"_"+service_inx+"_"+characteristic_inx;
    var btn_str_id ="btn_str"+"_"+service_inx+"_"+characteristic_inx;
    element(btn_hex_id).className = "format_button_enabled";
    element(btn_nle_id).className = "format_button_disabled";
    element(btn_nbe_id).className = "format_button_disabled";
    element(btn_str_id).className = "format_button_disabled";
    services[service_inx].characteristics[characteristic_inx].format = FORMAT_HEX;
    format_value(service_inx, characteristic_inx);
}

function on_format_nle(service_inx, characteristic_inx) {
    var btn_hex_id ="btn_hex"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nle_id ="btn_nle"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nbe_id ="btn_nbe"+"_"+service_inx+"_"+characteristic_inx;
    var btn_str_id ="btn_str"+"_"+service_inx+"_"+characteristic_inx;
    element(btn_hex_id).className = "format_button_disabled";
    element(btn_nle_id).className = "format_button_enabled";
    element(btn_nbe_id).className = "format_button_disabled";
    element(btn_str_id).className = "format_button_disabled";   
    services[service_inx].characteristics[characteristic_inx].format = FORMAT_NLE;
    format_value(service_inx, characteristic_inx);
}

function on_format_nbe(service_inx, characteristic_inx) {
    var btn_hex_id ="btn_hex"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nle_id ="btn_nle"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nbe_id ="btn_nbe"+"_"+service_inx+"_"+characteristic_inx;
    var btn_str_id ="btn_str"+"_"+service_inx+"_"+characteristic_inx;
    element(btn_hex_id).className = "format_button_disabled";
    element(btn_nle_id).className = "format_button_disabled";
    element(btn_nbe_id).className = "format_button_enabled";
    element(btn_str_id).className = "format_button_disabled";   
    services[service_inx].characteristics[characteristic_inx].format = FORMAT_NBE;
    format_value(service_inx, characteristic_inx);
}

function on_format_str(service_inx, characteristic_inx) {
    var btn_hex_id ="btn_hex"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nle_id ="btn_nle"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nbe_id ="btn_nbe"+"_"+service_inx+"_"+characteristic_inx;
    var btn_str_id ="btn_str"+"_"+service_inx+"_"+characteristic_inx;
    element(btn_hex_id).className = "format_button_disabled";
    element(btn_nle_id).className = "format_button_disabled";
    element(btn_nbe_id).className = "format_button_disabled";
    element(btn_str_id).className = "format_button_enabled";
    services[service_inx].characteristics[characteristic_inx].format = FORMAT_STR;
    format_value(service_inx, characteristic_inx);
}


function set_format_hex(service_inx, characteristic_inx) {
    var btn_hex_id ="btn_hex"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nle_id ="btn_nle"+"_"+service_inx+"_"+characteristic_inx;
    var btn_nbe_id ="btn_nbe"+"_"+service_inx+"_"+characteristic_inx;
    var btn_str_id ="btn_str"+"_"+service_inx+"_"+characteristic_inx;
    element(btn_hex_id).className = "format_button_enabled";
    element(btn_nle_id).className = "format_button_disabled";
    element(btn_nbe_id).className = "format_button_disabled";
    element(btn_str_id).className = "format_button_disabled";
}

function on_characteristic_read(service_inx, characteristic_inx) {
    console.log("on_characteristic_read(" + service_inx+","+characteristic_inx+")");
    var characteristic = services[service_inx].characteristics[characteristic_inx];
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      console.log(this.responseText);
	      result = JSON.parse(this.responseText);
	      // convert to byte array and store in the characteristic object
	      characteristic.value = hexToBytes(result.value);
	      message(result_string(result.result));
	      if (result.result == 0) {
		  var value_hex = "0x" + result.value;
		  var display_value = convertFromHex(value_hex, characteristic.format);
		  var attribute_indices = handle_map.get(characteristic.handle);
		  this_service_inx = attribute_indices[0];
		  this_characteristic_inx = attribute_indices[1];
		  element("char_val_"+this_service_inx+"_"+this_characteristic_inx).value = display_value;
		  // set_format_hex(this_service_inx,this_characteristic_inx);
	      }
        }
    };
    var target = "do_read_characteristic.py";
    var info = "reading..";
    xhttp.open("GET", CGI_ROOT+target+"?bdaddr="+selected_device.bdaddr+"&handle="+characteristic.handle, true);
    xhttp.send();
    message(info);

}

function action_links_for(service_inx, characteristic_inx, properties) {
    var links = "";
    for (var i=0;i<properties.length;i++) {
        var action_label = "";
	var action = properties[i];
	if (properties[i] == "write-without-response") {
	    action = "wwr";
	}
	var function_call = "on_characteristic_"+action;
	var btn_name = "";
	action_label = action;
	var notifying = false;
	if (services[service_inx].characteristics[characteristic_inx].notifying) {
	    notifying = true;
	}
	btn_name="btn_"+action;
	if (properties[i] == "notify" || properties[i] == "indicate") {
	    btn_name = "btn_notify";
	    if (notifying) {
	        function_call = function_call+"("+service_inx+","+characteristic_inx+")";
	        action_label = properties[i] + " off";
	    } else {
	        function_call = function_call+"("+service_inx+","+characteristic_inx+")";
		action_label = properties[i] + " on";
	    }    
	} else {
	    function_call = function_call+"("+service_inx+","+characteristic_inx+")";
	}
	links = links + "<button id='"+btn_name+"_"+service_inx+"_"+characteristic_inx+"' class='characteristic_button' onclick='"+function_call+"'/>"+action_label+"</button>"
    }
    return links;
}

function format_links_for(service_inx, characteristic_inx) {
    var links = "";
    links = links + "<button id='btn_hex"+"_"+service_inx+"_"+characteristic_inx+"' class='format_button_enabled' onclick='on_format_hex("+service_inx+","+characteristic_inx+");'/>0x</button>"
    links = links + "<button id='btn_nle"+"_"+service_inx+"_"+characteristic_inx+"' class='format_button_disabled' onclick='on_format_nle("+service_inx+","+characteristic_inx+");'/>LE</button>"
    links = links + "<button id='btn_nbe"+"_"+service_inx+"_"+characteristic_inx+"' class='format_button_disabled' onclick='on_format_nbe("+service_inx+","+characteristic_inx+");'/>BE</button>"
    links = links + "<button id='btn_str"+"_"+service_inx+"_"+characteristic_inx+"' class='format_button_disabled' onclick='on_format_str("+service_inx+","+characteristic_inx+");'/>AZ</button>"
    return links;
}

function onServiceDiscovery() {
  message("performing service discovery");
  clearServices();
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
	  services = JSON.parse(this.responseText);
	  if (services.result !== undefined) {
	      message("ERROR "+services.result);
	  } else {
	      message("");
	      var service_count = services.length;
	      for (var s=0;s < service_count; s++) {
		  showAttribute(s, "S", services[s].UUID, unknown(uuid_names.get(services[s].UUID)), "", "","");
		  handle_map.set(services[s].handle,[s,-1,-1]);
		  characteristics = services[s].characteristics
		  // firewall rules can result in a service with no characteristics
		  if (characteristics === undefined) {
		      continue;
		  }
		  var characteristic_count = characteristics.length;
		  for (var c=0;c < characteristic_count; c++) {
		      var char_value_field = "<input type='text' id='"+input_id(s,c)+"' class='readonly' readonly>";
		      characteristics[c].format = FORMAT_HEX;
		      showAttribute(c, "C", "&nbsp;&nbsp;"+characteristics[c].UUID, unknown(uuid_names.get(characteristics[c].UUID)), action_links_for(s,c,characteristics[c].properties), char_value_field, format_links_for(s,c));
		      handle_map.set(characteristics[c].handle,[s,c,-1]);
		      descriptors = characteristics[c].descriptors
		      var descriptor_count = descriptors.length;
		      for (var d=0;d < descriptor_count; d++) {
		          showAttribute(d, "D", "&nbsp;&nbsp;&nbsp;&nbsp;"+descriptors[d].UUID, unknown(uuid_names.get(descriptors[d].UUID)), "", "","");
		          handle_map.set(descriptors[d].handle,[s,c,d]);
		      }
		  }
	      }
	      message("ready");
          }
    }
  };
  xhttp.open("GET", CGI_ROOT+"do_service_discovery.py?bdaddr="+selected_device.bdaddr, true);
  xhttp.send();
    
}

function result_string(result) {
    if (result == 0) {
	return "OK";
    } else {
	return "ERROR "+result;
    }
}

function onDeviceSelected(device_inx) {
    selected_device = devices[device_inx];   
    selected_device_inx = device_inx;
    console.log(JSON.stringify(selected_device)); 
    hideAll();
    device_controller_hidden = false;
    element("device_addr").innerHTML = optional(selected_device.bdaddr);
    element("name").innerHTML = optional(selected_device.name);
    element("connected").innerHTML = optional(selected_device.connected);
    element("paired").innerHTML = optional(selected_device.paired);
    element("rssi").innerHTML = optional(selected_device.RSSI);
    element("appearance").innerHTML = optional(selected_device.appearance);
    element("rssi").innerHTML = optional(selected_device.RSSI);
    var ad_data = "";
    if (selected_device.ad_manufacturer_data_cid !== undefined) {
	ad_data = ad_data + "manufacturer data CID="+selected_device.ad_manufacturer_data_cid
    }
    if (selected_device.ad_manufacturer_data !== undefined) {
	ad_data = ad_data + "<br>manufacturer data="+selected_device.ad_manufacturer_data_cid
    }
    if (selected_device.ad_manufacturer_data !== undefined) {
	ad_data = ad_data + "<br>manufacturer data="+selected_device.ad_manufacturer_data_cid
    }
    if (selected_device.ad_service_data_uuid !== undefined) {
	ad_data = ad_data + "<br>service data UUID="+selected_device.ad_service_data_uuid
    }
    if (selected_device.ad_service_data !== undefined) {
	ad_data = ad_data + "<br>service data="+selected_device.ad_service_data
    }
    if (selected_device.ad_flags !== undefined) {
	ad_data = ad_data + "<br>flags="+selected_device.ad_flags
    }    
    element("ad").innerHTML = ad_data;
    element("services_resolved").innerHTML = optional(selected_device.services_resolved);
    if (selected_device.connected) {
	setElementVisibility("btn_svc_discovery", false);
	element("btn_toggle").innerHTML = "Disconnect";
    } else {
	setElementVisibility("btn_svc_discovery", true);
	element("btn_toggle").innerHTML = "Connect";
    }
    clearServices();
    setDivVisibility();
}
function onDevicesHtmlSelected() {
    view_mode = HTML_MODE;
    select("btn_devices_html");
    deselect("btn_devices_json");
    clearDeviceContent();
    showDiscoveredDevice(true, -1, "<b>Address</b>", "<b>Name</b>", "<b>RSSI</b>", "<b>State</b>"); 
    get_devices_json();
}

function onDevicesJsonSelected() {
    view_mode = JSON_MODE;
    select("btn_devices_json");
    deselect("btn_devices_html");
    clearDeviceContent();
    get_devices_json();
}

function select(dom_id) {
	element(dom_id).style.color = "#ffffff";
}

function deselect(dom_id) {
	element(dom_id).style.color = "#D3D3D3";
}

function init_devices_page() {
    setDivVisibility();
    deselect("btn_devices_json");
    deselect("btn_devices_html");
    message("ready");
}	

function action_link(device_inx) {
    if (typeof devices[device_inx].connected !== "undefined") {
	var id = "action_"+device_inx;
	if (devices[device_inx].connected) {
	    return "<a id="+id+" onclick='toggleConnectionState(\""+device_inx+"\")'>disconnect</a>";
	} else {
	    return "<a id="+id+" onclick='toggleConnectionState(\""+device_inx+"\")'>connect</a>";
	}
    }
    return "<a onclick='onDeviceConnect(\""+device_inx+"\")'>connect</a>";
}

function device_link(device_inx) {
    var id = "device_"+device_inx;
    return "<a id="+id+" onclick='onDeviceSelected(\""+device_inx+"\")'>"+devices[device_inx].bdaddr+"</a>";
}

function state_name(connected) {
    if (connected == 0) {
	return "disconnected";
    }
    if (connected == 1) {
	return "connected";
    }
    return "unknown";
}	

function get_devices_json() {
  message("scanning for Bluetooth devices");
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
	  // console.log(this.responseText);
	  devices = JSON.parse(this.responseText);
	  message("");
	  if (view_mode == JSON_MODE) {
              element("json_content").innerHTML = JSON.stringify(devices,null,2);
          } else {
	      var device_count = devices.length;
	      for (var i=0;i< device_count; i++) {
		      showDiscoveredDevice(false, i, devices[i].bdaddr, devices[i].name, devices[i].RSSI, devices[i].connected);
	      }
	      message("ready");
	  }
    }
  };

  xhttp.open("GET", CGI_ROOT+"do_discover_devices.py?scantime=3000", true);
  xhttp.send();
}

function message(text) {
	element('message').innerHTML = text;
}

function showDiscoveredDevice(header, device_inx, bdaddr, name, rssi, connected) {
    var tbl = element("tbl_devices");
    if (tbl != undefined) {
        var device_id = "device_"+device_inx;
        var action_id = "action_"+device_inx;
	var state_cell_id = "state_"+device_inx;
        var row_count = tbl.rows.length;
        var rows = tbl.rows;
        var new_row;
        new_row = tbl.insertRow(row_count);
        var action_cell = new_row.insertCell(0);
        var state_cell = new_row.insertCell(0);
        var rssi_cell = new_row.insertCell(0);
        var name_cell = new_row.insertCell(0);
        var addr_cell = new_row.insertCell(0);
        if (header) {
	    addr_cell.innerHTML = "<b>Address</b>";
	} else {
	    if (typeof bdaddr !== "undefined") {
		addr_cell.innerHTML = device_link(device_inx);
	    }
	}
        if (typeof name !== "undefined") {
	    name_cell.innerHTML = name;
	}
        if (typeof rssi !== "undefined") {
	    rssi_cell.innerHTML = rssi;
	}
	if (header) {
	    state_cell.innerHTML = "<b>State</b>";
	} else {
	    if (typeof connected !== "undefined") {
		state_cell.id = state_cell_id;
	        state_cell.innerHTML = state_name(connected);
	    }
	}
        if (header) {
	    action_cell.innerHTML = "<b>Action</b>";
	} else {
	    action_cell.innerHTML = action_link(device_inx);
	}
	if (!header) {
	    devices[device_inx].state_cell_id = state_cell_id;
	    devices[device_inx].action_id = action_id;
        }
    }
};

function clearDeviceContent() {
    var tbl = element("tbl_devices");
    tbl.innerHTML = "";
    var jc = element("json_content");
    jc.innerHTML = "";
}

function clearServices() {
    var tbl = element("tbl_services");
    tbl.innerHTML = "";
    services = [];
    handle_map = new Map();
}
