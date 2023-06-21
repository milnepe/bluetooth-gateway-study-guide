var device_controller_hidden = true;

var data_sets = [];
var indoor_temperature_data = [];
var indoor_data_inx = 0;
var outdoor_temperature_data = [];
var outdoor_data_inx = 0;
var chart_on = false;
var plot;
var options;

var selected_dst = destination_addresses[1].addr;
var indoor_temp_sub = false;
var outdoor_temp_sub = false;
var selected_colour = hsl_values[0];
var websocket

var next_action;
var sub_addr;

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

function initTemperatureCharting() {
    console.log("initTemperatureCharting");
        
	indoor_data_inx = 0;
	outdoor_data_inx = 0;

    var data_sets = [
        { color: "#FF0000", data: indoor_temperature_data, xaxis: 1, yaxis:1, lines: { show: true}},
        { color: "#00FF00", data: outdoor_temperature_data, xaxis: 1, yaxis:1, lines: { show: true}}
    ];
	
	options =  {
        xaxes: [
		{ show: true,
          showTickLabels : "major",
          mode: "time",
          timezone: "browser",
          twelveHourClock: false,
          tickSize: [5, "minute"],
          timeformat: "%H:%M"
        }
	    ],
	    yaxes: [
		{ show: true, 
            position: 'left', 
            autoScale: 'none', 
            min: -10, 
            max: 50 , 
            showTickLabels: "major"
        }
	    ]
	};
	
    console.log(options);

    plot = $.plot("#chart_area", data_sets, options);
	
}

// TODO complete the function to send a message in JSON format via the gateway
function sendMeshMessage(json) {
}

// TODO complete the function to formulate a generic on off set request in JSON format and send
function sendOnOffSetMessage(state_hex) {
}

// TODO complete the function to formulate a light HSL set request in JSON format and send
function sendLightHslSetMessage(h_hex, s_hex, l_hex) {
}

function onOn() {
    timedMessage("switching lights ON",3000);
    sendOnOffSetMessage(ACTION_GENERIC_ON_OFF_SET_UNACK,"01");
}

function onOff() {
    timedMessage("switching lights OFF",3000);
    sendOnOffSetMessage(ACTION_GENERIC_ON_OFF_SET_UNACK,"00");
}

function onColourClicked(event) {
    var btn = event.target || event.srcElement;
    var colour_inx = btn.id.slice(7)
    timedMessage("colour selected: "+colours[colour_inx],3000);
    var h = hsl_values[colour_inx].h;
    var s = hsl_values[colour_inx].s;
    var l = hsl_values[colour_inx].l;
    sendLightHslSetMessage(ACTION_LIGHT_HSL_SET_UNACK,h,s,l);
}

function new_ws_needed() {
    if (websocket == undefined || websocket.readyState === WebSocket.CLOSED) {
        return true;
    }
    return false;
}

function ws_is_ready() {
    if (websocket != undefined && websocket.readyState === WebSocket.OPEN) {
        return true;
    }
    return false;
}

function startWs() {
    if (new_ws_needed()) {
        console.log("creating websocket connection")
        websocket = new WebSocket(WS_SERVER);
        websocket.onopen = function(event) {
            if (next_action == ACTION_SUBSCRIBE) {
                subscribe(sub_addr);
            } else if (next_action == ACTION_UNSUBSCRIBE) {
                unsubscribe(sub_addr);
            }
        }
        websocket.onmessage = function (event) {
           console.log("message received: "+JSON.stringify(event.data))
            data = JSON.parse(event.data);
            if (data.dst != undefined) {
                message(data.dst+" says it's "+data.temperature+"C");
                if (data.dst == INDOOR_TEMP_DST) {
                    element("indoor_temperature").innerHTML = data.temperature+"C";
                    var time = (new Date().getTime()) / 1000;
                    var t = [time,data.temperature];
                    indoor_temperature_data.push(t);
                    if (indoor_temperature_data.length > MAX_TEMPERATURE_SAMPLES) {
                        indoor_temperature_data = indoor_temperature_data.slice(1, indoor_temperature_data.length);
                    }
                }
                if (data.dst == OUTDOOR_TEMP_DST) {
                    element("outdoor_temperature").innerHTML = data.temperature+"C";               
                    outdoor_data_inx++;
                    var time = (new Date().getTime()) / 1000;
                    var t = [time,data.temperature];
                    outdoor_temperature_data.push(t);
                    if (outdoor_temperature_data.length > MAX_TEMPERATURE_SAMPLES) {
                        outdoor_temperature_data = outdoor_temperature_data.slice(1, outdoor_temperature_data.length);
                    }
                }
                var data_sets = [
                    { color: "#FF0000", data: indoor_temperature_data, xaxis: 1, yaxis:1, lines: { show: true}},
                    { color: "#00FF00", data: outdoor_temperature_data, xaxis: 1, yaxis:1, lines: { show: true}}
                ];
                plot.setData(data_sets);
                plot.setupGrid(true);
                plot.draw();
            } else if (data.result != undefined) {
                if (parseInt(data.result) == 0) {
                    message("Operation was successfully executed");
                } else {
                    message("Error: "+error_messages[parseInt(data.result)]);
                }
            }

        };

        websocket.onclose = function (event) {
            console.log('The websocket connection has been closed');
        };

        websocket.onerror = function(event) {
            console.error("websocket error: ", event);
            message("WebSocket Error - is websocketd running on the server?");
        };
    }
}

function stopWs() {
    websocket.close();
};

// TODO complete the function to send a subscribe request to the gateway
function subscribe(dst) {
}

// TODO complete the function to send an unsubscribe request to the gateway
function unsubscribe(dst) {
}

function onWebcamSwitchClicked(event) {
    var cb = event.target || event.srcElement;
    var webcam = element('webcam');
    if (cb.checked == true) {
        timedMessage("enabling webcam",3000);
        webcam.innerHTML = webcam_source;
    } else {
        timedMessage("disabling webcam",3000);
        webcam.innerHTML = "";
    }
}

function onDstAddressListChanged(event) {
    selected_dst = element("dst_addresses").value;
    element("selected_dst").innerHTML = "0x" + selected_dst;
    timedMessage("Destination address changed to "+selected_dst,3000);
}

function onIndoorTempSubSwitchClicked(event) {
    indoor_temp_sub = element("sub_indoor_temp").checked;
    if (indoor_temp_sub == true) {
        timedMessage("Subscribing to indoor temperature readings",3000);
        indoor_temperature_data = [];
        if (ws_is_ready()) {
            next_action = ACTION_NONE;
            subscribe(INDOOR_TEMP_DST);
        } else {
            sub_addr = INDOOR_TEMP_DST;
            next_action = ACTION_SUBSCRIBE;
            startWs();
        }
    } else {
        timedMessage("Unsubscribing from indoor temperature readings",3000);
        element("indoor_temperature").innerHTML = "";
        if (ws_is_ready()) {
            next_action = ACTION_NONE;
            unsubscribe(INDOOR_TEMP_DST);
        } else {
            sub_addr = INDOOR_TEMP_DST;
            next_action = ACTION_UNSUBSCRIBE;
            startWs();
        }            
    }
}

function onOutdoorTempSubSwitchClicked(event) {
    outdoor_temp_sub = element("sub_outdoor_temp").checked;
    if (outdoor_temp_sub == true) {
        timedMessage("Subscribing to outdoor temperature readings",3000);
        outdoor_temperature_data = [];
        if (ws_is_ready()) {
            next_action = ACTION_NONE;
            subscribe(OUTDOOR_TEMP_DST);
        } else {
            sub_addr = OUTDOOR_TEMP_DST;
            next_action = ACTION_SUBSCRIBE;
            startWs();
        }
    } else {
        timedMessage("Unsubscribing from outdoor temperature readings",3000);
        element("outdoor_temperature").innerHTML = "";
        if (ws_is_ready()) {
            next_action = ACTION_NONE;
            unsubscribe(OUTDOOR_TEMP_DST);
        } else {
            sub_addr = OUTDOOR_TEMP_DST;
            next_action = ACTION_UNSUBSCRIBE;
            startWs();
        }            
    }
}

function init_page() {
    message("ready!");
    data_sets = [];
    dst_addresses_list = element("dst_addresses");
    dst_addresses_list.addEventListener('change', onDstAddressListChanged);
    for (inx in destination_addresses) {
        address_obj = destination_addresses[inx];
        option_text = address_obj.name;
        option_value = address_obj.addr;
        dst_addresses_list.options[dst_addresses_list.options.length] = new Option(option_text, option_value)
    }
    element("selected_dst").innerHTML = "0x" + destination_addresses[1].addr;
    element("dst_addresses").options[1].selected = true;

    webcam_switch = element('webcam_switch');
    webcam_switch.addEventListener('click', onWebcamSwitchClicked);

    indoor_temp_sub_switch = element('sub_indoor_temp');
    indoor_temp_sub_switch.checked = false;
    indoor_temp_sub_switch.addEventListener('click', onIndoorTempSubSwitchClicked);
    outdoor_temp_sub_switch = element('sub_outdoor_temp');
    outdoor_temp_sub_switch.checked = false;
    outdoor_temp_sub_switch.addEventListener('click', onOutdoorTempSubSwitchClicked);

    var i;
    for (i=0; i<8; i++) {
        var colour_btn = element("colour_"+i);
        colour_btn.addEventListener('click', onColourClicked);
    }

    initTemperatureCharting();

    next_action = ACTION_NONE;
    startWs();

}	

function clearMessage() {
    var msg = element('message');
    msg.innerHTML = "&nbsp;";
}

function timedMessage(text, duration) {
    message(text);
    setTimeout(function () {
        clearMessage();
    }, duration);

};

function message(text) {
	element('message').innerHTML = text;
}

function result_string(result) {
    if (result == 0) {
	return "OK";
    } else {
	return "ERROR "+result;
    }
}

