from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "opcua_machine"
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
]

CONF_ENDPOINT = "endpoint"
CONF_SECURITY_POLICY = "security_policy"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VALIDATE_ON_SAVE = "validate_on_save"

# Security settings (for non-None policies)
CONF_CLIENT_CERT_PATH = "client_cert_path"
CONF_CLIENT_KEY_PATH = "client_key_path"
CONF_SERVER_CERT_PATH = "server_cert_path"
CONF_CLIENT_KEY_PASSWORD = "client_key_password"

CONF_NODES = "nodes"
CONF_NODE_NAME = "name"
CONF_NODE_ID = "node_id"
CONF_NODE_KIND = "kind"
CONF_NODE_UNIT = "unit_of_measurement"
CONF_NODE_DEVICE_CLASS = "device_class"
CONF_NODE_STATE_CLASS = "state_class"
CONF_NODE_ICON = "icon"
CONF_NODE_INVERT = "invert"

# Optional advanced light mapping
CONF_LIGHT_BRIGHTNESS_NODE_ID = "brightness_node_id"
CONF_LIGHT_BRIGHTNESS_SCALE = "brightness_scale"

CONF_LIGHT_COLOR_TEMP_NODE_ID = "color_temp_node_id"
CONF_LIGHT_COLOR_TEMP_MIN_KELVIN = "color_temp_min_kelvin"
CONF_LIGHT_COLOR_TEMP_MAX_KELVIN = "color_temp_max_kelvin"

CONF_LIGHT_HS_HUE_NODE_ID = "hs_hue_node_id"
CONF_LIGHT_HS_SAT_NODE_ID = "hs_saturation_node_id"
CONF_LIGHT_HS_HUE_SCALE = "hs_hue_scale"
CONF_LIGHT_HS_SAT_SCALE = "hs_saturation_scale"

CONF_LIGHT_RGB_R_NODE_ID = "rgb_r_node_id"
CONF_LIGHT_RGB_G_NODE_ID = "rgb_g_node_id"
CONF_LIGHT_RGB_B_NODE_ID = "rgb_b_node_id"
CONF_LIGHT_RGB_SCALE = "rgb_scale"

CONF_LIGHT_RGBW_R_NODE_ID = "rgbw_r_node_id"
CONF_LIGHT_RGBW_G_NODE_ID = "rgbw_g_node_id"
CONF_LIGHT_RGBW_B_NODE_ID = "rgbw_b_node_id"
CONF_LIGHT_RGBW_W_NODE_ID = "rgbw_w_node_id"

CONF_LIGHT_RGBWW_R_NODE_ID = "rgbww_r_node_id"
CONF_LIGHT_RGBWW_G_NODE_ID = "rgbww_g_node_id"
CONF_LIGHT_RGBWW_B_NODE_ID = "rgbww_b_node_id"
CONF_LIGHT_RGBWW_CW_NODE_ID = "rgbww_cw_node_id"
CONF_LIGHT_RGBWW_WW_NODE_ID = "rgbww_ww_node_id"

CONF_LIGHT_WHITE_NODE_ID = "white_node_id"
CONF_LIGHT_WHITE_SCALE = "white_scale"

CONF_LIGHT_XY_X_NODE_ID = "xy_x_node_id"
CONF_LIGHT_XY_Y_NODE_ID = "xy_y_node_id"
CONF_LIGHT_XY_SCALE = "xy_scale"

CONF_LIGHT_EFFECT_NODE_ID = "effect_node_id"
CONF_LIGHT_EFFECT_LIST = "effect_list"
CONF_LIGHT_TRANSITION_NODE_ID = "transition_node_id"
CONF_LIGHT_FLASH_NODE_ID = "flash_node_id"

NODE_KIND_SENSOR = "sensor"
NODE_KIND_BINARY_SENSOR = "binary_sensor"
NODE_KIND_SWITCH = "switch"
NODE_KIND_LIGHT = "light"

DEFAULT_TITLE = "OPC-UA"
DEFAULT_SCAN_INTERVAL_SECONDS = 2

SECURITY_POLICY_NONE = "None"
SECURITY_POLICY_BASIC256SHA256_SIGN = "Basic256Sha256_Sign"
SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT = "Basic256Sha256_SignAndEncrypt"

DEFAULT_SECURITY_POLICY = SECURITY_POLICY_NONE
DEFAULT_VALIDATE_ON_SAVE = False

DEFAULT_BRIGHTNESS_SCALE = 255.0
DEFAULT_RGB_SCALE = 255.0
DEFAULT_WHITE_SCALE = 255.0
DEFAULT_HS_HUE_SCALE = 360.0
DEFAULT_HS_SAT_SCALE = 100.0
DEFAULT_XY_SCALE = 1.0
DEFAULT_COLOR_TEMP_MIN_KELVIN = 2000
DEFAULT_COLOR_TEMP_MAX_KELVIN = 6500

SECURITY_POLICIES: tuple[str, ...] = (
    SECURITY_POLICY_NONE,
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
)
