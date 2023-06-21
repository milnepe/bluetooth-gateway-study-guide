var device_list_hidden = false;
var device_controller_hidden = true;

var devices;
var selected_device;
var selected_device_inx;

var services; // and characteristics 2-dimensional array

var led_text_characteristic;
var led_text_characteristic_found;
var led_matrix_state_characteristic;
var led_matrix_state_characteristic_found;
var temperature_characteristic;
var temperature_characteristic_found;
var serial_number_characteristic;
var serial_number_characteristic_found;
var firmware_revision_characteristic;
var firmware_revision_characteristic_found;
var client_event_characteristic;
var client_event_found;

var led_rows = [0,0,0,0,0];
var led_cell_styles = ["cell_off", "cell_on"];

var on_off_events = [[0x8b,0x23,0x00,0x00],[0x8b,0x23,0x01,0x00]];

var data_sets = [];
var temperature_data = [];
var data_inx = 0;
var chart_on = false;
var plot;
var options;

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

function disableControlButtons() {
}

function enableControlButtons() {
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

function toggleConnectionState() {
    message("");
    console.log("toggleConnectionState: "+selected_device.bdaddr);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      console.log(this.responseText);
	      result = JSON.parse(this.responseText);
	      message(result_string(result.result));
	      if (result.result == 0) {
		  console.log("selected_device.connected="+selected_device.connected);
                  if (selected_device.connected == false || selected_device.connected == 0 || selected_device == undefined) {
		      element("btn_toggle").innerHTML = "Disconnect"
		      selected_device.connected = true;
                      doServiceDiscovery();	
		  } else {
		      element("btn_toggle").innerHTML = "Connect"
		      selected_device.connected = false;
		      disableControlButtons();
                      clearLedMatrixGraphic();
		  }
	      }
        }
    };
    var target = "do_connect.py";
    var info = "connecting..";
    console.log("selected_device.connected is currently "+selected_device.connected);
    if (selected_device.connected) {
	target = "do_disconnect.py";
	info = "disconnecting...";
    }

    var args = {};
    args.bdaddr = selected_device.bdaddr;
    var json = JSON.stringify(args);
    console.log(json);
    xhttp.open("PUT", CGI_ROOT+target, true);
    xhttp.setRequestHeader('Content-type','application/json; charset=utf-8');
    xhttp.send(json);

    message(info);
    return false;
    
}

function updateLedMatrixGraphic() {
    for (var r=0;r<5;r++) {
	for (c=0;c<5;c++) {
	    var id = "LED_" + r + "_" + c;
	    var cell_state = (led_rows[r] & Math.pow(2,c)) >> (c);
	    element(id).className = led_cell_styles[(led_rows[r] >> c) % 2];    
	}
    }
}

function clearLedMatrixGraphic() {
    led_rows = [0,0,0,0,0];
    updateLedMatrixGraphic();
}

function onCellSelected(r,c) {
    console.log("onCellSelected("+r+","+c+")");
    if (selected_device.connected == false) {
	message("micro:bit must first be connected");
	return;
    }
    console.log(led_rows);
    var cell_state = (led_rows[r] & Math.pow(2,c)) >> (c);
    var new_cell_state = cell_state;
    if (cell_state == 0) {
	new_cell_state = 1;
	led_rows[r] = led_rows[r] | 1 << (c);
    } else {
	new_cell_state = 0;
	led_rows[r] = led_rows[r] & ~(1 << (c));
    }

    onUpdateLedMatrix();    

}

function onLedText() {
    var led_text = document.getElementById("led_text").value;
    console.log("onLedText - text = "+led_text);
    if (selected_device.connected == false) {
	message("micro:bit must first be connected");
	return;
    }
    if (led_text.length == 0) {
	message("Please enter some text");
	return;
    }
    
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      result = JSON.parse(this.responseText);
	      message(result_string(result.result));
	      setTimeout(readLedMatrixState(), 6000);
        }
    };
    
    var value_bytes = convertToBytes(led_text, FORMAT_STR); 
    var value_hex = bytesToHex(value_bytes); 

    var args = {};
    args.bdaddr = selected_device.bdaddr;
    args.handle = led_text_characteristic.handle;
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

function readLedMatrixState() {
    var characteristic = led_matrix_state_characteristic;
    console.log(characteristic);
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      result = JSON.parse(this.responseText);
	      characteristic.value = hexToBytes(result.value);
	      led_rows = characteristic.value;
	      console.log(led_rows);
	      message(result_string(result.result));
	      if (result.result == 0) {
    		  updateLedMatrixGraphic();
	      }
        }
    };
    var target = "do_read_characteristic.py";
    var info = "reading..";
    xhttp.open("GET", CGI_ROOT+target+"?bdaddr="+selected_device.bdaddr+"&handle="+characteristic.handle, true);
    xhttp.send();
    message(info);
}

function onUpdateLedMatrix() {
    console.log("onUpdateLedMatrix");
    if (selected_device.connected == false) {
	message("micro:bit must first be connected");
	return;
    }
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (this.readyState == 4 && this.status == 200) {
	      result = JSON.parse(this.responseText);
	      message(result_string(result.result));
	      if (result.result == 0) {
		  updateLedMatrixGraphic();
	      }
        }
    };
    
    var value_hex = bytesToHex(led_rows); 

    var args = {};
    args.bdaddr = selected_device.bdaddr;
    args.handle = led_matrix_state_characteristic.handle;
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

function toggle_state_of_connected_thing(new_state) {
    if (selected_device.connected == false) {
        message("micro:bit must first be connected");
        return;
    }

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
              result = JSON.parse(this.responseText);
              message(result_string(result.result));
        }
    };

    var value_hex = bytesToHex(on_off_events[new_state]);

    var args = {};
    args.bdaddr = selected_device.bdaddr;
    args.handle = client_event_characteristic.handle;
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

function onOn() {
    console.log("ON");    
    toggle_state_of_connected_thing(1);
}

function onOff() {
    console.log("OFF");        
    toggle_state_of_connected_thing(0);
}

function onToggleChart() {
    console.log("onToggleChart");
    if (selected_device.connected == false) {
	message("micro:bit must first be connected");
	return;
    }
    chart_on = !chart_on;
    if (chart_on) {
        data_sets = [];
	temperature_data = [];
	data_inx = 0;
        var data_sets = [
            { color: "#FF0000", data: temperature_data, xaxis: 1, yaxis:1, lines: { show: true}}
        ];
	
	options =  {
	    xaxes: [
		{ show: false }
	    ],
	    yaxes: [
		{ show: true, position: 'left', autoScale: 'none', min: 10, max: 40 , showTickLabels: true}
	    ]
	};
	
        plot = $.plot("#chart_area", data_sets, options);
	
    }
    
    toggleNotifications();
    
}

function toggleNotifications() {
    console.log("onToggleNotifications");
    if (selected_device.connected == false) {
        message("micro:bit must first be connected");
        return;
    }

    var handle = temperature_characteristic.handle;
    var ws;

    if (temperature_characteristic.notifying == false || (temperature_characteristic.notifying == true && ws_map.get(handle) === undefined)) {
    	console.log("enabling temperature notifications...");
        ws = new WebSocket(NOTIFICATIONS_SERVER);
        ws_map.set(handle,ws);

        ws.onerror = function(event) {
            err = "ERROR: Web Socket for notification control and transport is not available";
            message(err);
            console.log(err);
            alert(err);
        };
	
        ws.onopen = function(e) {
            // enable notifications
            console.log(JSON.stringify(temperature_characteristic));
            var control_message = {
            "bdaddr" : selected_device.bdaddr,
            "handle" : temperature_characteristic.handle,
            "command" : NOTIFICATIONS_ON
            };
            console.log(JSON.stringify(control_message));
            ws.send(JSON.stringify(control_message));
        }

        ws.onmessage = function(event) {
            result = JSON.parse(event.data);
    //	    console.log("onmessage: "+JSON.stringify(result));
            if (result.value !== undefined) {
                if (!temperature_characteristic) {
                    return;
                }
                // convert to byte array from hex format and store
                temperature_characteristic.value = hexToBytes(result.value);
                var temperature = convertFromHex(result.value,FORMAT_NLE);
                element("current_temperature").innerHTML = temperature + " " + DEGREES_C;
                data_inx++;
                var t = [data_inx,temperature];
                temperature_data.push(t);
                if (temperature_data.length > MAX_TEMPERATURE_SAMPLES) {
                            temperature_data = temperature_data.slice(1, temperature_data.length);
                }
                data_sets = [
                    { color: "#FF0000", data: temperature_data, xaxis: 1, yaxis:1, lines: { show: true}}
                ];

                var axes = plot.getYAxes();
                axes.forEach(function(axis) {
                    axis.options.showTickLabels = true;
                });		
                
                plot.setData(data_sets);
                plot.setupGrid(true);
                plot.draw();
                
            } else if (result.result == 0) {
                if (temperature_characteristic.notifying == false) {
                    console.log("notifications enabled OK");
                    temperature_characteristic.notifying = true;
                    element("btn_toggle_chart").innerHTML = "Chart Off";
                    } else {
                    console.log("notifications disabled OK");
                    temperature_characteristic.notifying = false;
                    element("btn_toggle_chart").innerHTML = "Chart On";
                    element("current_temperature").innerHTML = "--";
                    data_sets = [];
                    $.plot("#chart_area", data_sets,options);
                    ws.close();
                    ws_map.delete(handle);
                }
            } else {
                        message(error[result.result]);
            }
        };
		
    } else {
        console.log("disabling...");
        ws = ws_map.get(handle);
        console.log(ws);
        var control_message = {
            "bdaddr" : selected_device.bdaddr,
            "handle" : temperature_characteristic.handle,
            "command" : NOTIFICATIONS_OFF
        };
        console.log(JSON.stringify(control_message));
        ws.send(JSON.stringify(control_message));
    }
    
}


function doServiceDiscovery() {
  console.log("doServiceDiscovery");
  message("performing service discovery");
  led_text_characteristic = null;
  led_text_characteristic_found = false;
  led_matrix_state_characteristic = null;
  led_matrix_state_characteristic_found = false;
  temperature_characteristic = null;
  temperature_characteristic_found = false;
  serial_number_characteristic = null;
  serial_number_characteristic_found = false;
  firmware_revision_characteristic = null;
  firmware_revision_characteristic_found = false;
  client_event_characteristic = null;
  client_event_found = false;
  
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
		  handle_map.set(services[s].handle,[s,-1,-1]);
		  characteristics = services[s].characteristics
		  var characteristic_count = characteristics.length;
		  for (var c=0;c < characteristic_count; c++) {
		      // console.log(characteristics[c].UUID);
		      handle_map.set(characteristics[c].handle,[s,c,-1]);
		      descriptors = characteristics[c].descriptors
		      var descriptor_count = descriptors.length;
		      for (var d=0;d < descriptor_count; d++) {
		          handle_map.set(descriptors[d].handle,[s,c,d]);
		      }
		      if (characteristics[c].UUID == SERIAL_NUMBER_UUID) {
			  console.log("Found serial number characteristic");
			  serial_number_characteristic = characteristics[c];
			  serial_number_characteristic_found = true;
		      } else if (characteristics[c].UUID == FIRMWARE_REVISION_UUID) {
			  console.log("Found firmware revision characteristic");
			  firmware_revision_characteristic = characteristics[c];
			  firmware_revision_characteristic_found = true;
		      } else if (characteristics[c].UUID == LED_MATRIX_STATE_UUID) {
			  console.log("Found LED matrix state characteristic");
			  led_matrix_state_characteristic = characteristics[c];
			  led_matrix_state_characteristic_found = true;
		      } else if (characteristics[c].UUID == LED_TEXT_UUID) {
			  console.log("Found LED Text characteristic");
			  led_text_characteristic = characteristics[c];
			  led_text_characteristic_found = true;
		      } else if (characteristics[c].UUID == TEMPERATURE_UUID) {
			  console.log("Found temperature characteristic");
			  temperature_characteristic = characteristics[c];
			  temperature_characteristic_found = true;
		      } else if (characteristics[c].UUID == CLIENT_EVENT_UUID) {
			  console.log("Found client event characteristic");
			  client_event_characteristic = characteristics[c];
			  client_event_characteristic_found = true;
		      }
		  }
	      }
              message("ready");
              readLedMatrixState();
          }
    }
  };
  console.log(CGI_ROOT+"do_service_discovery.py?bdaddr="+selected_device.bdaddr);
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
    console.log("onDeviceSelected: "+device_inx);
    selected_device = devices[device_inx];   
    selected_device_inx = device_inx;
    console.log(JSON.stringify(selected_device)); 
    hideAll();
    if (selected_device.connected == false) {
        disableControlButtons();    
    } else {
	enableControlButtons();    
    }
    device_controller_hidden = false;
    if (selected_device.connected) {
	element("btn_toggle").innerHTML = "Disconnect";
        doServiceDiscovery();	
    } else {
	element("btn_toggle").innerHTML = "Connect";
    }
    setDivVisibility();
}

function onDevicesHtmlSelected() {
    clearDeviceContent();
    showDiscoveredDevice(true, -1, "<b>Address</b>", "<b>Name</b>", "<b>RSSI</b>", "<b>State</b>"); 
    get_devices_json();
}


function init_devices_page() {
    setDivVisibility();
    message("ready");
}	

function device_link(device_inx) {
    var id = "device_"+device_inx;
    return "<a id="+id+" onclick='onDeviceSelected("+device_inx+")'>"+devices[device_inx].bdaddr+"</a>";
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
  message("scanning for micro:bits");
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
	  console.log(this.responseText);
	  devices = JSON.parse(this.responseText);
	  message("");
	  var device_count = devices.length;
	  for (var i=0;i< device_count; i++) {
		  showDiscoveredDevice(false, i, devices[i].bdaddr, devices[i].name, devices[i].RSSI, devices[i].connected);
	  }
	  message("ready");
    }
  };
  xhttp.open("GET", CGI_ROOT+"do_discover_devices.py?scantime=3000", true);
  xhttp.send();
}

function message(text) {
	element('message').innerHTML = text;
}

function showDiscoveredDevice(header, device_inx, bdaddr, name, rssi, connected) {
    if (name === undefined) {
	// not a micro:bit
	return;
    }
    if (!header && !name.includes("BBC")) {
	// not a micro:bit
	return;
    }
    var tbl = element("tbl_devices");
    if (tbl != undefined) {
        var device_id = "device_"+device_inx;
        var action_id = "action_"+device_inx;
	var state_cell_id = "state_"+device_inx;
        var row_count = tbl.rows.length;
        var rows = tbl.rows;
        var new_row;
        new_row = tbl.insertRow(row_count);
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
	if (!header) {
            name_cell.innerHTML = name;
	} else {
	    name_cell.innerHTML = "<b>Name</b>";
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
	if (!header) {
	    devices[device_inx].state_cell_id = state_cell_id;
	    devices[device_inx].action_id = action_id;
        }
    }
};

function clearDeviceContent() {
    var tbl = element("tbl_devices");
    tbl.innerHTML = "";
}
