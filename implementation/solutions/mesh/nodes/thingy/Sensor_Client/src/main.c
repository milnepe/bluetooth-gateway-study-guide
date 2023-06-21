/**
 * 
 * Partial implementation of the sensor client model. Simply flashes the Thingy LED when a sensor status message is received
 * and logs its contents. For testing the sensor server model.
 * 
 * Coded for and tested with Nordic Thingy
 * 
 **/

#include <stdlib.h>
#include <bluetooth/bluetooth.h>
#include <settings/settings.h>
#include <drivers/gpio.h>
#include <bluetooth/mesh.h>
#include <random/rand32.h>

bool provisioned = 0;

// GPIO for the Thingy LED controller
const struct device *led_ctrlr;

#define PORT "GPIO_P0"
#define LED_R 7
#define LED_G 5
#define LED_B 6

uint16_t rgb_r;
uint16_t rgb_g;
uint16_t rgb_b;

uint16_t reply_addr;
uint8_t reply_net_idx;
uint8_t reply_app_idx;

#define TEMPERATURE_ID 0x004F
#define HUMIDITY_ID    0x0076

static uint8_t dev_uuid[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,0x00, 0x00, 0x00, 0x00,0x00, 0x00, 0x00, 0x00 };

void gen_uuid() {
    uint32_t rnd1 = sys_rand32_get();
    uint32_t rnd2 = sys_rand32_get();
    uint32_t rnd3 = sys_rand32_get();
    uint32_t rnd4 = sys_rand32_get();

    dev_uuid[15] = (rnd1 >> 24) & 0x0FF;
    dev_uuid[14] = (rnd1 >> 16) & 0x0FF;
    dev_uuid[13] = (rnd1 >>  8) & 0x0FF;
    dev_uuid[12] =  rnd1 & 0x0FF;

    dev_uuid[11] = (rnd2 >> 24) & 0x0FF;
    dev_uuid[10] = (rnd2 >> 16) & 0x0FF;
    dev_uuid[9] = (rnd2 >>  8) & 0x0FF;
    dev_uuid[8] =  rnd2 & 0x0FF;

    dev_uuid[7] = (rnd3 >> 24) & 0x0FF;
    dev_uuid[6] = (rnd3 >> 16) & 0x0FF;
    dev_uuid[5] = (rnd3 >>  8) & 0x0FF;
    dev_uuid[4] =  rnd3 & 0x0FF;

    dev_uuid[3] = (rnd4 >> 24) & 0x0FF;
    dev_uuid[2] = (rnd4 >> 16) & 0x0FF;
    dev_uuid[1] = (rnd4 >>  8) & 0x0FF;
    dev_uuid[0] =  rnd4 & 0x0FF;

    /* Set 4 MSB bits of time_hi_and_version field */
    dev_uuid[6] &= 0x0f;
    dev_uuid[6] |= 4 << 4;

    /* Set 2 MSB of clock_seq_hi_and_reserved to 10 */
    dev_uuid[8] &= 0x3f;
    dev_uuid[8] |= 0x80;

}

// Sensor Client
// -------------
// Sensor data has to be marshalled using the rules specified in 4.2.14 of the mesh models specification
//    MPID - Marshalling Property ID
//      1-bit Format field 
//        Format A - 0b0 - a 4-bit Length field and an 11-bit Property ID field
//        Format B - 0b1 - a 7-bit Length field and a 16-bit Property ID field
//      4-bit or 7-bit Length of the Property Value field
//      11-bit or 16-bit Property ID
//    Raw Value
//      Raw Value field with a size and representation defined by the device property.
//
// Two mesh properties are included in status messages sent by the associated sensor:
//  Present Ambient Temperature property [0x004F] (Temperature 8 characteristic)
//    The Temperature 8 characteristic is used to represent a measure of temperature with a unit of 0.5 degree Celsius.
//    sint8
//    Unit is degree Celsius with a resolution of 0.5.
//    Minimum: -64.0
//    Maximum: 63.0
//    MPID=0b0100000001001111 (2 octets)
//
//  Present Ambient Relative Humidity device property [0x0076] (Humidity characteristic)
//    The Humidity characteristic is a fixed-length structure containing a single Humidity field.
//    uint16
//    Unit is in percent with a resolution of 0.01 percent.
//    Allowed range is: 0.00 to 100.00
//    MPID=0b100100000000000001110110 (3 octets)
//
// anything else received will be ignored

static int TEMP_VALUE_INX = 2;
static int HUMIDITY_VALUE_INX = 6;
static uint8_t temp_and_humidity[8] = {
		0x40,
		0x4F,
		0x00,
		0x90,
		0x00,
		0x76,
		0x00,
		0x00
};

void thingy_led_on(int r, int g, int b)
{
	// LEDs on Thingy are "active low" so zero means on. Args are expressed as RGB 0-255 values so we map them to GPIO low/high.
	r = !(r / 255);
	g = !(g / 255);
	b = !(b / 255);

	printk("r=%d g=%d b=%d\n",r,g,b);

	gpio_pin_set(led_ctrlr, LED_R, r);
	gpio_pin_set(led_ctrlr, LED_G, g);
	gpio_pin_set(led_ctrlr, LED_B, b);
}

void thingy_led_off()
{
	gpio_pin_set(led_ctrlr, LED_R, 1);
	gpio_pin_set(led_ctrlr, LED_G, 1);
	gpio_pin_set(led_ctrlr, LED_B, 1);
}

static void attention_on(struct bt_mesh_model *model)
{
	printk("attention_on()\n");
	thingy_led_on(255,0,0);
}

static void attention_off(struct bt_mesh_model *model)
{
	printk("attention_off()\n");
	thingy_led_off();
}

static const struct bt_mesh_health_srv_cb health_srv_cb = {
	.attn_on = attention_on,
	.attn_off = attention_off,
};

static int provisioning_output_pin(bt_mesh_output_action_t action, uint32_t number) {
	printk("OOB Number: %u\n", number);
	return 0;
}

static void provisioning_complete(uint16_t net_idx, uint16_t addr) {
    printk("Provisioning completed\n");
}

static void provisioning_reset(void)
{
	bt_mesh_prov_enable(BT_MESH_PROV_ADV | BT_MESH_PROV_GATT);
}

// provisioning properties and capabilities
static const struct bt_mesh_prov prov = {
	.uuid = dev_uuid,
	.output_size = 4,
	.output_actions = BT_MESH_DISPLAY_NUMBER,
	.output_number = provisioning_output_pin,
	.complete = provisioning_complete,
	.reset = provisioning_reset,
};

/*
 * The following two functions were converted from the pseudocode provided in the mesh models specification, section 6.1.1 Introduction
 */

double Hue_2_RGB(double v1, double v2, double vH ) {

	// printf("Hue_2_RGB: v1=%f v2=%f vH=%f\n",v1,v2,vH);

    if ( vH < 0.0f ) {
		vH += 1.0f;
	}
    if ( vH > 1.0f ) {
		vH -= 1.0f;
	}
    if (( 6.0f * vH ) < 1.0f ) {
		return ( v1 + ( v2 - v1 ) * 6.0f * vH );
	}
    if (( 2.0f * vH ) < 1.0f ) {
		return ( v2 );
	}
    if (( 3.0f * vH ) < 2.0f ) {
		return ( v1 + ( v2 - v1 ) * ( ( 2.0f / 3.0f ) - vH ) * 6.0f );
	}
    return ( v1 );
}	

void convert_hsl_to_rgb(unsigned short hsl_h,unsigned short hsl_s,unsigned short hsl_l ) {
	// printf("hsl_h=%d hsl_s=%d hsl_l=%d\n",hsl_h,hsl_s,hsl_l);
    double H = hsl_h / 65535.0f;
    double S = hsl_s / 65535.0f;
    double L = hsl_l / 65535.0f;
	double var_1 = 0.0f;
	double var_2 = 0.0f;
	
    if ( S == 0 ) {
      rgb_r = L * 255;
      rgb_g = L * 255;
      rgb_b = L * 255;
    } else {
      if ( L < 0.5f ) {
	      var_2 = L * ( 1.0f + S );
	  } else { 
		  var_2 = ( L + S ) - ( S * L );
	  }
      var_1 = 2.0f * L - var_2;
	  
      double R = Hue_2_RGB( var_1, var_2, H + ( 1.0f / 3.0f ));
      double G = Hue_2_RGB( var_1, var_2, H );
      double B = Hue_2_RGB( var_1, var_2, H - ( 1.0f / 3.0f ));
	  
	  // printf("R=%f G=%f B=%f\n",R,G,B);
	  
	  rgb_r = 256 * R;
	  rgb_g = 256 * G;
	  rgb_b = 256 * B;
    }
}

void indicate_sensor_data(uint16_t addr) {
	// flash red for the indoor temperature sensor (C002)
	int r = 255, g = 0, b = 0;
	// or green for the outdoor temperature sensor (C003)
	if (addr == 0xC003) {
		r = 0;
		g = 255;
	}
	thingy_led_on(r, g, b);
    k_sleep(K_MSEC(250));
    r = 0, g = 0, b = 0;
	thingy_led_on(r, g, b);	
}

// handler functions for this model's operations. We only need handlers for those message types we might receive.
static void sensor_status(struct bt_mesh_model *model, struct bt_mesh_msg_ctx *ctx, struct net_buf_simple *buf)
{
    uint16_t dst_addr;
	dst_addr = ctx->recv_dst;
    indicate_sensor_data(dst_addr);
    uint8_t buflen = buf->len;

	// uint8_t sensor_data[3] = {
	// 	0x01, // MPID: 0b00001000 = Format A, length 1
	// 	0x4F, // 11-bit property ID (inc 3 bits from first octet): 0b01001111 = Temperature 8 characteristic
	// 	0x00, // 1 byte value
	// };

	uint8_t format = 0;
	uint8_t length = 0;
	uint16_t property_id;
	uint8_t id1;
	uint8_t id2;
	int8_t temperature = 0;

	int i=0;
	// 08 4f 27
	while (i < buflen) {
		uint8_t format_length = net_buf_simple_pull_u8(buf);
		format = (format_length >> 7);
		if (format == 0) { // Format A - a 4-bit Length field and an 11-bit Property ID field
			length = ((format_length & 0b01111000) >> 3);
			id1 = format_length & 0b00000111;
			id2 = net_buf_simple_pull_u8(buf);
			property_id = (id1 << 8) | id2;
			if (property_id == TEMPERATURE_ID) {
				temperature = (net_buf_simple_pull_u8(buf) * 0.5);
				printk("\nLEN: %d PROPERTY_ID: 0x%x TEMPERATURE: %dC\n",length,property_id,temperature);
			} else {
				// property not supported
				printk("\nLEN: %d PROPERTY_ID: 0x%x\n",length,property_id);
			}
			i = i + 2 + length;
		} else {           // Format B - a 7-bit Length field and a 16-bit Property ID field
			length = format_length & 0b01111111;
			id1 = net_buf_simple_pull_u8(buf);
			id2 = net_buf_simple_pull_u8(buf);
			property_id = (id1 << 8) | id2;
			printk("\nLEN: %d PROPERTY_ID: 0x%x\n",length,property_id);
			i = i + 3 + length;
		}

	}

}

// messages the model might receive
static const struct bt_mesh_model_op sensor_client_op[] = {
		{BT_MESH_MODEL_OP_1(0x52), 0, sensor_status},
		BT_MESH_MODEL_OP_END,
};

// -------------------------------------------------------------------------------------------------------
// Health Server
// -------------
BT_MESH_HEALTH_PUB_DEFINE(health_pub, 0);
static struct bt_mesh_health_srv health_srv = {
	.cb = &health_srv_cb,
};

// -------------------------------------------------------------------------------------------------------
// Composition
// -----------

#define CONFIG_SERVER_MODEL       0
#define HEALTH_SERVER_MODEL       1
#define SENSOR_CLIENT_MODEL       2

static struct bt_mesh_model sig_models[] = {
		BT_MESH_MODEL_CFG_SRV,
		BT_MESH_MODEL_HEALTH_SRV(&health_srv, &health_pub),
		BT_MESH_MODEL(BT_MESH_MODEL_ID_SENSOR_CLI, sensor_client_op,
									NULL, NULL)};

// node contains elements.note that BT_MESH_MODEL_NONE means "none of this type" ands here means "no vendor models"
static struct bt_mesh_elem elements[] = {
		BT_MESH_ELEM(0, sig_models, BT_MESH_MODEL_NONE),
};

// node
static const struct bt_mesh_comp comp = {
		.cid = 0xFFFF,
		.elem = elements,
		.elem_count = ARRAY_SIZE(elements),
};

void indicate_provisioned() {
	int r = 0, g = 255, b = 0;
	thingy_led_on(r, g, b);
    k_sleep(K_MSEC(250));
    r = 0, g = 0, b = 0;
	thingy_led_on(r, g, b);	
}

void indicate_unprovisioned() {
	int r = 255, g = 0, b = 0;
	thingy_led_on(r, g, b);
    k_sleep(K_MSEC(250));
    r = 0, g = 0, b = 0;
	thingy_led_on(r, g, b);	
}

static void bt_ready(int err)
{
	if (err)
	{
		printk("bt_enable init failed with err %d\n", err);
		return;
	}
    printk("Bluetooth initialised OK\n");

	gen_uuid();

    printk("\n%02X%02X%02X%02X-%02X%02X-%02X%02X-%02X%02X-%02X%02X%02X%02X%02X%02X\n\n",
            dev_uuid[15], dev_uuid[14], dev_uuid[13], dev_uuid[12],dev_uuid[11], dev_uuid[10], dev_uuid[9], dev_uuid[8],
            dev_uuid[7], dev_uuid[6], dev_uuid[5], dev_uuid[4],dev_uuid[3], dev_uuid[2], dev_uuid[1], dev_uuid[0]);

	err = bt_mesh_init(&prov, &comp);

	if (err)
	{
		printk("bt_mesh_init failed with err %d\n", err);
		return;
	}

	printk("Mesh initialised OK: 0x%04x\n",elements[0].addr);

	if (IS_ENABLED(CONFIG_SETTINGS)) {
		settings_load();
	    printk("Settings loaded\n");
	}

	/* This will be a no-op if settings_load() loaded provisioning info */
	/* run nrfjprog -e against your board (assuming it's a Nordic board) to clear provisioning data and start again */

    if (!bt_mesh_is_provisioned()) {
    	printk("Node has not been provisioned - beaconing\n");
		bt_mesh_prov_enable(BT_MESH_PROV_ADV | BT_MESH_PROV_GATT);
		provisioned = 0;
		indicate_unprovisioned();
	} else {
    	printk("Node has already been provisioned\n");
		provisioned = 1;
	    printk("Node unicast address: 0x%04x\n",elements[0].addr);
		indicate_provisioned();
	}

}

static void configure_thingy_led_controller()
{
	led_ctrlr = device_get_binding(PORT);
	gpio_pin_configure(led_ctrlr, LED_R, GPIO_OUTPUT);
	gpio_pin_configure(led_ctrlr, LED_G, GPIO_OUTPUT);
	gpio_pin_configure(led_ctrlr, LED_B, GPIO_OUTPUT);
}

void indicate_on() {
	int r = 0, g = 0, b = 255;
	thingy_led_on(r, g, b);
    k_sleep(K_MSEC(500));
    r = 0, g = 0, b = 0;
	thingy_led_on(r, g, b);	
}

void main(void)
{
	printk("thingy sensor client node v1.0.0\n");

	configure_thingy_led_controller();

    indicate_on();

	// set default colour to white
	rgb_r = 255;
	rgb_g = 255;
	rgb_b = 255;

	printk("Calling bt_enable\n");
	int err = bt_enable(bt_ready);
	if (err)
	{
		printk("bt_enable failed with err %d\n", err);
		return;
	}

	printk("Node is ready\n");

}
