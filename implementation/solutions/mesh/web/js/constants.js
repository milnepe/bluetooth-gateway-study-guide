//let WS_SERVER = 'ws://pi400:8082/';
let WS_SERVER = 'wss://pi400:443/ws/';

let CGI_ROOT = "../cgi-bin/gateway/";
//let webcam_source = "<img src='http://pi400:8081?action=stream' alt='--- webcam feed not found ---'/>"
let webcam_source = "<img src='../camera/?action=stream' alt='--- webcam feed not found ---'/>"

let DEGREES_C = "&#x2103";
let MAX_TEMPERATURE_SAMPLES = 86400;
let TEMP_MAX = 40;
let TEMP_MIN = 10;

let INDOOR_TEMP_DST = "C002";
let OUTDOOR_TEMP_DST = "C003";

// comment: exposing mesh addresses beyond the mesh network itself is not necessarily the only way to do this.
// clients of the gateway could deal in other representations (e.g. just the human readable name) and the gateway could
// convert to the corresponding 16-bit address. But this approach makes it easier for developers/users to troubleshoot if they
// deal directly with mesh addresses which are passed through the gatewayunchanged.

var destination_addresses = [
	{ "name":"ALL NODES", "addr":"FFFF"},
	{ "name":"ALL LIGHTS", "addr":"C001"},
	{ "name":"ROW 1", "addr":"C011"},
	{ "name":"ROW 2", "addr":"C012"},
	{ "name":"ROW 3", "addr":"C013"},
	{ "name":"ROW 4", "addr":"C014"},
	{ "name":"COL 1", "addr":"C021"},
	{ "name":"COL 2", "addr":"C022"},
	{ "name":"COL 3", "addr":"C023"},
	{ "name":"COL 4", "addr":"C024"}
];

var subscribe_addresses = [
	{ "name":"Indoor Temperature", "addr":"C002"},
	{ "name":"Outdoor Temperature", "addr":"C003"},
];


var colours = [
	"white", "red", "green", "blue", "yellow", "cyan", "magenta", "black"
]

/*
WHITE   : HSL(    0,    0,65535) = RGB(255,255,255)

RED     : HSL(    0,65535,32767) = RGB(255,0,0)

GREEN   : HSL(21845,65535,32767) = RGB(0,255,0)

BLUE    : HSL(43690,65535,32767) = RGB(0,0,255)

YELLOW  : HSL(10922,65535,32767) = RGB(255,255,0)

MAGENTA : HSL(54613,65535,32767) = RGB(255,0,255)

CYAN    : HSL(32768,65535,32767) = RGB(0,255,255)

BLACK   : HSL(    0,    0,    0) = RGB(0,0,0)

*/

var hsl_values = [{h:"0000",s:"0000",l:"FFFF"},
                  {h:"0000",s:"FFFF",l:"7FFF"},
                  {h:"5555",s:"FFFF",l:"7FFF"},
                  {h:"AAAA",s:"FFFF",l:"7FFF"},
                  {h:"2AAA",s:"FFFF",l:"7FFF"},
                  {h:"8000",s:"FFFF",l:"7FFF"},
                  {h:"D555",s:"FFFF",l:"7FFF"},
                  {h:"0000",s:"0000",l:"0000"}
                 ];

let ACTION_GENERIC_ON_OFF_SET_UNACK = "generic_onoff_set_unack"
let ACTION_LIGHT_HSL_SET_UNACK = "light_hsl_set_unack"

let FORMAT_HEX = 0;
let FORMAT_NLE = 1;
let FORMAT_NBE = 2;
let FORMAT_STR = 3;
let FORMAT_UINT16LE = 4;
let FORMAT_UINT16BE = 5;


let RESULT_OK = 0;
let RESULT_ERR = 1;
let RESULT_ERR_NOT_SUPPORTED = 2;
let RESULT_ERR_WRONG_STATE = 3;
let RESULT_ERR_ACCESS_DENIED = 4;
let RESULT_ERR_BAD_ARGS = 5;
let RESULT_ATTACH_FAILED = 6;
let RESULT_SEND_FAILED = 7;

var error_messages = [
	"operation succeeded",
	"an unknown error occured",
	"requested operation is not supported",
	"an object is in the wrong state",
	"access denied due to security rules",
	"invalid arguments were provided to the operation",
	"concurrency limit reached",
	"attempt to send a mesh message failed"
];

let ACTION_NONE = 0;
let ACTION_SUBSCRIBE = 1;
let ACTION_UNSUBSCRIBE = 2;
