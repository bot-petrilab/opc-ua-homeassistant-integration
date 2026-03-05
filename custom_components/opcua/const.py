from __future__ import annotations

try:
    from homeassistant.const import Platform
except Exception:  # pragma: no cover - fallback for standalone smoke/import tests
    from enum import StrEnum

    class Platform(StrEnum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"
        LIGHT = "light"
        BUTTON = "button"
        CLIMATE = "climate"
        COVER = "cover"
        DATE = "date"
        DATETIME = "datetime"
        FAN = "fan"
        NOTIFY = "notify"
        NUMBER = "number"
        SCENE = "scene"
        SELECT = "select"
        TEXT = "text"
        TIME = "time"
        WEATHER = "weather"

DOMAIN = "opcua"
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.DATE,
    Platform.DATETIME,
    Platform.FAN,
    Platform.NOTIFY,
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SELECT,
    Platform.TEXT,
    Platform.TIME,
    Platform.WEATHER,
]

CONF_ENDPOINT = "endpoint"
CONF_SECURITY_POLICY = "security_policy"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_VALIDATE_ON_SAVE = "validate_on_save"

CONF_POLL_PROFILE = "poll_profile"
CONF_POLL_FAST_INTERVAL = "poll_fast_interval"
CONF_POLL_NORMAL_INTERVAL = "poll_normal_interval"
CONF_POLL_SLOW_INTERVAL = "poll_slow_interval"

# Security settings (for non-None policies)
CONF_CLIENT_CERT_PATH = "client_cert_path"
CONF_CLIENT_KEY_PATH = "client_key_path"
CONF_SERVER_CERT_PATH = "server_cert_path"
CONF_CLIENT_KEY_PASSWORD = "client_key_password"

# Notification bridge settings
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_TITLE_PREFIX = "notify_title_prefix"
CONF_NOTIFY_KEYWORDS = "notify_keywords"

CONF_NODES = "nodes"
CONF_NODE_NAME = "name"
CONF_NODE_ID = "node_id"
CONF_NODE_KIND = "kind"
CONF_NODE_UNIT = "unit_of_measurement"
CONF_NODE_DEVICE_CLASS = "device_class"
CONF_NODE_STATE_CLASS = "state_class"
CONF_NODE_ICON = "icon"
CONF_NODE_INVERT = "invert"

# Generic optional node mapping for write-capable entities
CONF_NODE_TARGET_NODE_ID = "target_node_id"

# Button
CONF_BUTTON_PAYLOAD = "button_payload"

# Climate
CONF_CLIMATE_HVAC_MODE_NODE_ID = "hvac_mode_node_id"
CONF_CLIMATE_MIN_TEMP = "min_temp"
CONF_CLIMATE_MAX_TEMP = "max_temp"
CONF_CLIMATE_TEMP_STEP = "temp_step"

# Cover
CONF_COVER_SET_POSITION_NODE_ID = "set_position_node_id"
CONF_COVER_OPEN_NODE_ID = "open_node_id"
CONF_COVER_CLOSE_NODE_ID = "close_node_id"
CONF_COVER_STOP_NODE_ID = "stop_node_id"
CONF_COVER_INVERT_POSITION = "invert_position"

# Fan
CONF_FAN_SPEED_NODE_ID = "speed_node_id"

# Number
CONF_NUMBER_MIN = "number_min"
CONF_NUMBER_MAX = "number_max"
CONF_NUMBER_STEP = "number_step"

# Scene
CONF_SCENE_ACTIVATE_VALUE = "scene_activate_value"

# Select
CONF_SELECT_OPTIONS = "select_options"

# Text
CONF_TEXT_MAX = "text_max"

# Notify entity
CONF_NOTIFY_MESSAGE_NODE_ID = "message_node_id"
CONF_NOTIFY_TITLE_NODE_ID = "title_node_id"

# Weather
CONF_WEATHER_HUMIDITY_NODE_ID = "humidity_node_id"
CONF_WEATHER_PRESSURE_NODE_ID = "pressure_node_id"
CONF_WEATHER_WIND_SPEED_NODE_ID = "wind_speed_node_id"
CONF_WEATHER_CONDITION_NODE_ID = "condition_node_id"

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
NODE_KIND_BUTTON = "button"
NODE_KIND_CLIMATE = "climate"
NODE_KIND_COVER = "cover"
NODE_KIND_DATE = "date"
NODE_KIND_DATETIME = "datetime"
NODE_KIND_FAN = "fan"
NODE_KIND_NOTIFY = "notify"
NODE_KIND_NUMBER = "number"
NODE_KIND_SCENE = "scene"
NODE_KIND_SELECT = "select"
NODE_KIND_TEXT = "text"
NODE_KIND_TIME = "time"
NODE_KIND_WEATHER = "weather"

DEFAULT_TITLE = "OPC-UA"
DEFAULT_SCAN_INTERVAL_SECONDS = 2
DEFAULT_POLL_FAST_INTERVAL_SECONDS = 1
DEFAULT_POLL_NORMAL_INTERVAL_SECONDS = 5
DEFAULT_POLL_SLOW_INTERVAL_SECONDS = 30
DEFAULT_POLL_PROFILE = "normal"
POLL_PROFILES: tuple[str, ...] = ("fast", "normal", "slow")

EVENT_NOTIFICATION = "opcua_notification"

SECURITY_POLICY_NONE = "None"
SECURITY_POLICY_BASIC256SHA256_SIGN = "Basic256Sha256_Sign"
SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT = "Basic256Sha256_SignAndEncrypt"

DEFAULT_SECURITY_POLICY = SECURITY_POLICY_NONE
DEFAULT_VALIDATE_ON_SAVE = False

DEFAULT_NOTIFY_ENABLED = True
DEFAULT_NOTIFY_SERVICE = "persistent_notification.create"
DEFAULT_NOTIFY_TITLE_PREFIX = "OPC-UA"
DEFAULT_NOTIFY_KEYWORDS: tuple[str, ...] = (
    "alarm",
    "warning",
    "warn",
    "fault",
    "error",
    "trip",
    "störung",
    "stoerung",
)

DEFAULT_BRIGHTNESS_SCALE = 255.0
DEFAULT_RGB_SCALE = 255.0
DEFAULT_WHITE_SCALE = 255.0
DEFAULT_HS_HUE_SCALE = 360.0
DEFAULT_HS_SAT_SCALE = 100.0
DEFAULT_XY_SCALE = 1.0
DEFAULT_COLOR_TEMP_MIN_KELVIN = 2000
DEFAULT_COLOR_TEMP_MAX_KELVIN = 6500

DEFAULT_CLIMATE_MIN_TEMP = 7.0
DEFAULT_CLIMATE_MAX_TEMP = 35.0
DEFAULT_CLIMATE_TEMP_STEP = 0.5

DEFAULT_NUMBER_MIN = 0.0
DEFAULT_NUMBER_MAX = 100.0
DEFAULT_NUMBER_STEP = 1.0

SECURITY_POLICIES: tuple[str, ...] = (
    SECURITY_POLICY_NONE,
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
)
