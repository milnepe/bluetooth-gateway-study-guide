function bytesToHex(bytes) {
    for (var hex = [], i = 0; i < bytes.length; i++) {
        hex.push((bytes[i] >>> 4).toString(16));
        hex.push((bytes[i] & 0xF).toString(16));
    }
    return hex.join("");
}

// e.g. 01 03 = (3 * 256) + 1 = 769
function bytesToIntLE(bytes) {
    var number = 0;
    for (var i=0;i<bytes.length;i++) {
        number = number + (bytes[i] << (8 * i));
    }    
    return number;
}

// e.g. 01 03 = (1 * 256) + 3 = 259
function bytesToIntBE(bytes) {
    var number = 0;
    var shift_bits = (bytes.length - 1) * 8;
    for (var i=0;i<bytes.length;i++) {
        number = number + (bytes[i] << shift_bits);
        shift_bits = shift_bits - 8;
    }    
    return number;
}

function uint16ToBytesLE(number) {
    console.log("uint16ToBytesLE: "+number);
    var b = [2];
	b[0] = (number & 0xFF);
	b[1] = ((number >> 8) & 0xFF);
	return b;
}

function uint16ToBytesBE(number) {
    console.log("uint16ToBytesBE: "+number);
    var b = [2];
	b[0] = ((number >> 8) & 0xFF);
	b[1] = (number & 0xFF);
	return b;
}

function bytesToString(bytes) {
    var s = "";
    for (var i=0;i<bytes.length;i++) {
        s = s + String.fromCharCode(bytes[i]);
    }
    return s;
}

function hexToBytes(hex) {
    hex = hex.trim();
    hex = hex.replace(/ /g, '');
	if (hex.startsWith("0x")) {
	    hex = hex.substring(2);
	}
    var bytes = [];
    while (hex.length >= 2) {
        bytes.push(parseInt(hex.substring(0, 2), 16));
        hex = hex.substring(2, hex.length);
    }
    return bytes;
}


function toCharacterCodes(text) {
    var bytes = [];
    for (var i = 0; i < text.length; i++) {
        bytes.push(text.charCodeAt(i));
    }
    return bytes;
}

function convertToBytes(input_value, format) {
    if (format == FORMAT_HEX) {
        return hexToBytes(input_value);
    }
    if (format == FORMAT_UINT16LE) {
        return uint16ToBytesLE(input_value);
    }
    if (format == FORMAT_UINT16BE) {
        return uint16ToBytesBE(input_value);
    }
    if (format == FORMAT_STR) {
        return toCharacterCodes(input_value);
    }
}

function convertFromHex(hex_value, format) {
    if (format == FORMAT_HEX) {
        if (!hex_value.startsWith("0x")) {
            hex_value = "0x"+hex_value;
        }
        return hex_value;
    }
    if (format == FORMAT_NLE) {
        return bytesToIntLE(hexToBytes(hex_value));
    }
    if (format == FORMAT_NBE) {
        return bytesToIntBE(hexToBytes(hex_value));

    }
    if (format == FORMAT_STR) {
        return bytesToString(hexToBytes(hex_value));
    }
}

function convertFromBytes(bytes, format) {
    if (format == FORMAT_HEX) {
        var hex_value = "0x" + bytesToHex(bytes)
        return hex_value;
    }
    if (format == FORMAT_NLE) {
        return bytesToIntLE(bytes);
    }
    if (format == FORMAT_NBE) {
        return bytesToIntBE(bytes);

    }
    if (format == FORMAT_STR) {
        return bytesToString(bytes);
    }
}


function optional(prop) {
    if (typeof prop == 'undefined') {
	return "";
    } else {
	return prop;
    }
}

function unknown(thing) {
    if (typeof thing == 'undefined') {
	return "unknown";
    } else {
	return thing;
    }
}

function element(id) {
    return document.getElementById(id);
}

function getHexRandom() {
    var uint8_array = new Uint8Array(16);
    crypto.getRandomValues(uint8_array);
    var byte_array = Array.from(uint8_array)
    return bytesToHex(byte_array)
}
