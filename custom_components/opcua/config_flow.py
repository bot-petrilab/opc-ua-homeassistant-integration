from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_BUTTON_PAYLOAD,
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_CLIENT_KEY_PATH,
    CONF_CLIMATE_HVAC_MODE_NODE_ID,
    CONF_CLIMATE_MAX_TEMP,
    CONF_CLIMATE_MIN_TEMP,
    CONF_CLIMATE_TEMP_STEP,
    CONF_COVER_CLOSE_NODE_ID,
    CONF_COVER_INVERT_POSITION,
    CONF_COVER_OPEN_NODE_ID,
    CONF_COVER_SET_POSITION_NODE_ID,
    CONF_COVER_STOP_NODE_ID,
    CONF_ENDPOINT,
    CONF_FAN_SPEED_NODE_ID,
    CONF_LIGHT_BRIGHTNESS_NODE_ID,
    CONF_LIGHT_BRIGHTNESS_SCALE,
    CONF_LIGHT_COLOR_TEMP_MAX_KELVIN,
    CONF_LIGHT_COLOR_TEMP_MIN_KELVIN,
    CONF_LIGHT_COLOR_TEMP_NODE_ID,
    CONF_LIGHT_EFFECT_LIST,
    CONF_LIGHT_EFFECT_NODE_ID,
    CONF_LIGHT_FLASH_NODE_ID,
    CONF_LIGHT_HS_HUE_NODE_ID,
    CONF_LIGHT_HS_HUE_SCALE,
    CONF_LIGHT_HS_SAT_NODE_ID,
    CONF_LIGHT_HS_SAT_SCALE,
    CONF_LIGHT_RGB_B_NODE_ID,
    CONF_LIGHT_RGB_G_NODE_ID,
    CONF_LIGHT_RGB_R_NODE_ID,
    CONF_LIGHT_RGB_SCALE,
    CONF_LIGHT_RGBW_B_NODE_ID,
    CONF_LIGHT_RGBW_G_NODE_ID,
    CONF_LIGHT_RGBW_R_NODE_ID,
    CONF_LIGHT_RGBW_W_NODE_ID,
    CONF_LIGHT_RGBWW_B_NODE_ID,
    CONF_LIGHT_RGBWW_CW_NODE_ID,
    CONF_LIGHT_RGBWW_G_NODE_ID,
    CONF_LIGHT_RGBWW_R_NODE_ID,
    CONF_LIGHT_RGBWW_WW_NODE_ID,
    CONF_LIGHT_TRANSITION_NODE_ID,
    CONF_LIGHT_WHITE_NODE_ID,
    CONF_LIGHT_WHITE_SCALE,
    CONF_LIGHT_XY_SCALE,
    CONF_LIGHT_XY_X_NODE_ID,
    CONF_LIGHT_XY_Y_NODE_ID,
    CONF_NODE_DEVICE_CLASS,
    CONF_NODE_ICON,
    CONF_NODE_ID,
    CONF_NODE_INVERT,
    CONF_NODE_KIND,
    CONF_NODE_NAME,
    CONF_NODE_STATE_CLASS,
    CONF_NODE_TARGET_NODE_ID,
    CONF_NODE_UNIT,
    CONF_NODES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_NOTIFY_MESSAGE_NODE_ID,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TITLE_NODE_ID,
    CONF_NOTIFY_TITLE_PREFIX,
    CONF_NUMBER_MAX,
    CONF_NUMBER_MIN,
    CONF_NUMBER_STEP,
    CONF_SCAN_INTERVAL,
    CONF_SCENE_ACTIVATE_VALUE,
    CONF_SECURITY_POLICY,
    CONF_SELECT_OPTIONS,
    CONF_SERVER_CERT_PATH,
    CONF_TEXT_MAX,
    CONF_VALIDATE_ON_SAVE,
    CONF_WEATHER_CONDITION_NODE_ID,
    CONF_WEATHER_HUMIDITY_NODE_ID,
    CONF_WEATHER_PRESSURE_NODE_ID,
    CONF_WEATHER_WIND_SPEED_NODE_ID,
    DEFAULT_BRIGHTNESS_SCALE,
    DEFAULT_CLIMATE_MAX_TEMP,
    DEFAULT_CLIMATE_MIN_TEMP,
    DEFAULT_CLIMATE_TEMP_STEP,
    DEFAULT_COLOR_TEMP_MAX_KELVIN,
    DEFAULT_COLOR_TEMP_MIN_KELVIN,
    DEFAULT_HS_HUE_SCALE,
    DEFAULT_HS_SAT_SCALE,
    DEFAULT_NOTIFY_ENABLED,
    DEFAULT_NOTIFY_KEYWORDS,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_TITLE_PREFIX,
    DEFAULT_NUMBER_MAX,
    DEFAULT_NUMBER_MIN,
    DEFAULT_NUMBER_STEP,
    DEFAULT_RGB_SCALE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_SECURITY_POLICY,
    DEFAULT_TITLE,
    DEFAULT_VALIDATE_ON_SAVE,
    DEFAULT_WHITE_SCALE,
    DEFAULT_XY_SCALE,
    DOMAIN,
    NODE_KIND_BINARY_SENSOR,
    NODE_KIND_BUTTON,
    NODE_KIND_CLIMATE,
    NODE_KIND_COVER,
    NODE_KIND_DATE,
    NODE_KIND_DATETIME,
    NODE_KIND_FAN,
    NODE_KIND_LIGHT,
    NODE_KIND_NOTIFY,
    NODE_KIND_NUMBER,
    NODE_KIND_SCENE,
    NODE_KIND_SELECT,
    NODE_KIND_SENSOR,
    NODE_KIND_SWITCH,
    NODE_KIND_TEXT,
    NODE_KIND_TIME,
    NODE_KIND_WEATHER,
    SECURITY_POLICIES,
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
    SECURITY_POLICY_NONE,
)
from .opcua_client import OpcUaClientManager

_LOGGER = logging.getLogger(__name__)


class OpcUaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OPC-UA."""

    VERSION = 1

    _discovered_endpoint: str | None = None
    _discovered_name: str | None = None

    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        """Handle zeroconf discovery for OPC-UA servers."""
        host = str(getattr(discovery_info, "host", "") or "").strip().strip("[]")
        port = int(getattr(discovery_info, "port", 0) or 0)
        name = str(getattr(discovery_info, "name", "") or "OPC UA Server")

        if not host or not port:
            return self.async_abort(reason="cannot_connect")

        endpoint = f"opc.tcp://{host}:{port}"
        await self.async_set_unique_id(endpoint)
        self._abort_if_unique_id_configured()

        # Probe discovered endpoint, but do not hard-abort discovery on probe errors.
        # Some servers are visible via mDNS yet may reject immediate client probes.
        try:
            manager = OpcUaClientManager(
                endpoint=endpoint,
                security_policy=DEFAULT_SECURITY_POLICY,
                username=None,
                password=None,
            )
            await manager.ensure_connected()
            await manager.disconnect()
        except Exception as err:
            _LOGGER.debug(
                "Zeroconf-discovered OPC-UA endpoint probe failed (%s): %s", endpoint, err
            )

        self._discovered_endpoint = endpoint
        self._discovered_name = name

        self.context["title_placeholders"] = {"name": name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm adding a discovered OPC-UA server."""
        endpoint = self._discovered_endpoint
        if not endpoint:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            title = self._discovered_name or endpoint
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ENDPOINT: endpoint,
                    CONF_SECURITY_POLICY: DEFAULT_SECURITY_POLICY,
                    CONF_USERNAME: None,
                    CONF_PASSWORD: None,
                    CONF_CLIENT_CERT_PATH: None,
                    CONF_CLIENT_KEY_PATH: None,
                    CONF_SERVER_CERT_PATH: None,
                    CONF_CLIENT_KEY_PASSWORD: None,
                    CONF_NOTIFY_ENABLED: DEFAULT_NOTIFY_ENABLED,
                    CONF_NOTIFY_SERVICE: DEFAULT_NOTIFY_SERVICE,
                    CONF_NOTIFY_TITLE_PREFIX: DEFAULT_NOTIFY_TITLE_PREFIX,
                    CONF_NOTIFY_KEYWORDS: list(DEFAULT_NOTIFY_KEYWORDS),
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL_SECONDS,
                    CONF_NODES: [],
                },
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovered_name or "OPC UA Server",
                "endpoint": endpoint,
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            endpoint = str(user_input[CONF_ENDPOINT]).strip()
            security_policy = str(user_input[CONF_SECURITY_POLICY]).strip()
            username = user_input.get(CONF_USERNAME) or None
            password = user_input.get(CONF_PASSWORD) or None
            client_cert_path = (user_input.get(CONF_CLIENT_CERT_PATH) or "").strip() or None
            client_key_path = (user_input.get(CONF_CLIENT_KEY_PATH) or "").strip() or None
            server_cert_path = (user_input.get(CONF_SERVER_CERT_PATH) or "").strip() or None
            client_key_password = user_input.get(CONF_CLIENT_KEY_PASSWORD) or None
            notify_enabled = bool(user_input.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED))
            notify_service = str(user_input.get(CONF_NOTIFY_SERVICE) or DEFAULT_NOTIFY_SERVICE).strip()
            notify_title_prefix = str(user_input.get(CONF_NOTIFY_TITLE_PREFIX) or DEFAULT_NOTIFY_TITLE_PREFIX).strip()
            notify_keywords_raw = str(user_input.get(CONF_NOTIFY_KEYWORDS) or "").strip()
            if notify_keywords_raw:
                notify_keywords = [k.strip().lower() for k in notify_keywords_raw.split(",") if k.strip()]
            else:
                notify_keywords = list(DEFAULT_NOTIFY_KEYWORDS)

            validate_on_save = bool(user_input.get(CONF_VALIDATE_ON_SAVE, DEFAULT_VALIDATE_ON_SAVE))
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])

            if not endpoint:
                errors[CONF_ENDPOINT] = "required"
            elif not endpoint.lower().startswith("opc.tcp://"):
                errors[CONF_ENDPOINT] = "invalid_endpoint"

            secure_policy = security_policy != SECURITY_POLICY_NONE
            if secure_policy:
                if not client_cert_path:
                    errors[CONF_CLIENT_CERT_PATH] = "required"
                if not client_key_path:
                    errors[CONF_CLIENT_KEY_PATH] = "required"

            if not errors:
                await self.async_set_unique_id(endpoint)
                self._abort_if_unique_id_configured()

                if validate_on_save:
                    try:
                        manager = OpcUaClientManager(
                            endpoint=endpoint,
                            security_policy=security_policy,
                            username=username,
                            password=password,
                            client_cert_path=client_cert_path,
                            client_key_path=client_key_path,
                            server_cert_path=server_cert_path,
                            client_key_password=client_key_password,
                        )
                        await manager.ensure_connected()
                        await manager.disconnect()
                    except Exception as err:
                        _LOGGER.warning("OPC UA validation failed for %s: %s", endpoint, err)
                        errors["base"] = "cannot_connect"

            if not errors:
                title = user_input.get("title") or DEFAULT_TITLE
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_ENDPOINT: endpoint,
                        CONF_SECURITY_POLICY: security_policy,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_CLIENT_CERT_PATH: client_cert_path,
                        CONF_CLIENT_KEY_PATH: client_key_path,
                        CONF_SERVER_CERT_PATH: server_cert_path,
                        CONF_CLIENT_KEY_PASSWORD: client_key_password,
                        CONF_NOTIFY_ENABLED: notify_enabled,
                        CONF_NOTIFY_SERVICE: notify_service,
                        CONF_NOTIFY_TITLE_PREFIX: notify_title_prefix,
                        CONF_NOTIFY_KEYWORDS: notify_keywords,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_NODES: [],
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Optional("title", default=DEFAULT_TITLE): TextSelector(),
                vol.Required(CONF_ENDPOINT): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Required(CONF_SECURITY_POLICY, default=DEFAULT_SECURITY_POLICY): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SECURITY_POLICIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_USERNAME): TextSelector(TextSelectorConfig(type="text")),
                vol.Optional(CONF_PASSWORD): TextSelector(TextSelectorConfig(type="password")),
                vol.Optional(CONF_CLIENT_CERT_PATH): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Optional(CONF_CLIENT_KEY_PATH): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Optional(CONF_SERVER_CERT_PATH): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Optional(CONF_CLIENT_KEY_PASSWORD): TextSelector(
                    TextSelectorConfig(type="password")
                ),
                vol.Optional(CONF_NOTIFY_ENABLED, default=DEFAULT_NOTIFY_ENABLED): BooleanSelector(),
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    default=DEFAULT_NOTIFY_SERVICE,
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_NOTIFY_TITLE_PREFIX,
                    default=DEFAULT_NOTIFY_TITLE_PREFIX,
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_NOTIFY_KEYWORDS,
                    default=",".join(DEFAULT_NOTIFY_KEYWORDS),
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_SECONDS): NumberSelector(
                    NumberSelectorConfig(min=1, max=60, step=1, mode="box")
                ),
                vol.Required(CONF_VALIDATE_ON_SAVE, default=DEFAULT_VALIDATE_ON_SAVE): BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return OpcUaOptionsFlow(config_entry)


class OpcUaOptionsFlow(OptionsFlow):
    """Handle options flow for OPC-UA."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry
        self._options: dict[str, Any] = dict(config_entry.options)
        self._options.setdefault(
            CONF_SCAN_INTERVAL,
            int(config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)),
        )
        self._options.setdefault(CONF_NODES, list(config_entry.data.get(CONF_NODES, [])))
        self._browse_cache: list[dict[str, Any]] = []
        self._browse_root_node_id: str = "i=85"
        self._browse_current_parent: str = "i=85"
        self._discovery_cache: list[dict[str, Any]] = []
        self._server_discovery_cache: list[dict[str, Any]] = []

    async def _persist_options(self) -> None:
        """Persist options immediately and reload entry so entities appear at once."""
        self.hass.config_entries.async_update_entry(self._entry, options=self._options)
        await self.hass.config_entries.async_reload(self._entry.entry_id)

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "menu_quick_setup",
                "menu_add_entities",
                "menu_discovery_tools",
                "menu_settings",
            ],
        )

    async def async_step_menu_quick_setup(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="menu_quick_setup",
            menu_options=[
                "auto_discovery",
                "browse_nodes",
                "add_stack_light_profile",
                "init",
            ],
        )

    async def async_step_menu_add_entities(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="menu_add_entities",
            menu_options=[
                "add_sensor",
                "add_binary_sensor",
                "add_switch",
                "add_light",
                "add_number",
                "add_select",
                "add_text",
                "add_button",
                "menu_add_entities_advanced",
                "init",
            ],
        )

    async def async_step_menu_add_entities_advanced(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="menu_add_entities_advanced",
            menu_options=[
                "add_climate",
                "add_cover",
                "add_fan",
                "add_scene",
                "add_date",
                "add_datetime",
                "add_time",
                "add_weather",
                "add_notify",
                "menu_add_entities",
                "init",
            ],
        )

    async def async_step_menu_discovery_tools(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="menu_discovery_tools",
            menu_options=[
                "auto_discovery",
                "browse_nodes",
                "init",
            ],
        )

    async def async_step_menu_settings(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="menu_settings",
            menu_options=[
                "remove_node",
                "set_poll_interval",
                "init",
            ],
        )

    async def async_step_add_sensor(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SENSOR,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_UNIT: user_input.get(CONF_NODE_UNIT) or None,
                    CONF_NODE_DEVICE_CLASS: user_input.get(CONF_NODE_DEVICE_CLASS) or None,
                    CONF_NODE_STATE_CLASS: user_input.get(CONF_NODE_STATE_CLASS) or None,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_UNIT): TextSelector(),
                vol.Optional(CONF_NODE_DEVICE_CLASS): TextSelector(),
                vol.Optional(CONF_NODE_STATE_CLASS): TextSelector(),
                vol.Optional(CONF_NODE_ICON): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_sensor", data_schema=schema)

    async def async_step_add_binary_sensor(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_BINARY_SENSOR,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_DEVICE_CLASS: user_input.get(CONF_NODE_DEVICE_CLASS) or None,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                    CONF_NODE_INVERT: bool(user_input.get(CONF_NODE_INVERT, False)),
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_DEVICE_CLASS): TextSelector(),
                vol.Optional(CONF_NODE_ICON): TextSelector(),
                vol.Required(CONF_NODE_INVERT, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="add_binary_sensor", data_schema=schema)

    async def async_step_add_switch(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SWITCH,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                    CONF_NODE_INVERT: bool(user_input.get(CONF_NODE_INVERT, False)),
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON): TextSelector(),
                vol.Required(CONF_NODE_INVERT, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="add_switch", data_schema=schema)

    async def async_step_add_light(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            light_cfg: dict[str, Any] = {
                CONF_NODE_KIND: NODE_KIND_LIGHT,
                CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                CONF_NODE_ID: user_input[CONF_NODE_ID],
                CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                CONF_NODE_INVERT: bool(user_input.get(CONF_NODE_INVERT, False)),
            }

            optional_text_keys = [
                CONF_LIGHT_BRIGHTNESS_NODE_ID,
                CONF_LIGHT_COLOR_TEMP_NODE_ID,
                CONF_LIGHT_HS_HUE_NODE_ID,
                CONF_LIGHT_HS_SAT_NODE_ID,
                CONF_LIGHT_RGB_R_NODE_ID,
                CONF_LIGHT_RGB_G_NODE_ID,
                CONF_LIGHT_RGB_B_NODE_ID,
                CONF_LIGHT_RGBW_R_NODE_ID,
                CONF_LIGHT_RGBW_G_NODE_ID,
                CONF_LIGHT_RGBW_B_NODE_ID,
                CONF_LIGHT_RGBW_W_NODE_ID,
                CONF_LIGHT_RGBWW_R_NODE_ID,
                CONF_LIGHT_RGBWW_G_NODE_ID,
                CONF_LIGHT_RGBWW_B_NODE_ID,
                CONF_LIGHT_RGBWW_CW_NODE_ID,
                CONF_LIGHT_RGBWW_WW_NODE_ID,
                CONF_LIGHT_WHITE_NODE_ID,
                CONF_LIGHT_XY_X_NODE_ID,
                CONF_LIGHT_XY_Y_NODE_ID,
                CONF_LIGHT_EFFECT_NODE_ID,
                CONF_LIGHT_TRANSITION_NODE_ID,
                CONF_LIGHT_FLASH_NODE_ID,
            ]
            for key in optional_text_keys:
                value = user_input.get(key)
                if value:
                    light_cfg[key] = str(value).strip()

            # Optional scales / ranges (only persist when relevant node mapping exists)
            if light_cfg.get(CONF_LIGHT_BRIGHTNESS_NODE_ID):
                light_cfg[CONF_LIGHT_BRIGHTNESS_SCALE] = float(
                    user_input.get(CONF_LIGHT_BRIGHTNESS_SCALE, DEFAULT_BRIGHTNESS_SCALE)
                )
            if light_cfg.get(CONF_LIGHT_COLOR_TEMP_NODE_ID):
                light_cfg[CONF_LIGHT_COLOR_TEMP_MIN_KELVIN] = int(
                    user_input.get(CONF_LIGHT_COLOR_TEMP_MIN_KELVIN, DEFAULT_COLOR_TEMP_MIN_KELVIN)
                )
                light_cfg[CONF_LIGHT_COLOR_TEMP_MAX_KELVIN] = int(
                    user_input.get(CONF_LIGHT_COLOR_TEMP_MAX_KELVIN, DEFAULT_COLOR_TEMP_MAX_KELVIN)
                )
            if light_cfg.get(CONF_LIGHT_HS_HUE_NODE_ID):
                light_cfg[CONF_LIGHT_HS_HUE_SCALE] = float(
                    user_input.get(CONF_LIGHT_HS_HUE_SCALE, DEFAULT_HS_HUE_SCALE)
                )
            if light_cfg.get(CONF_LIGHT_HS_SAT_NODE_ID):
                light_cfg[CONF_LIGHT_HS_SAT_SCALE] = float(
                    user_input.get(CONF_LIGHT_HS_SAT_SCALE, DEFAULT_HS_SAT_SCALE)
                )
            if (
                light_cfg.get(CONF_LIGHT_RGB_R_NODE_ID)
                or light_cfg.get(CONF_LIGHT_RGB_G_NODE_ID)
                or light_cfg.get(CONF_LIGHT_RGB_B_NODE_ID)
                or light_cfg.get(CONF_LIGHT_RGBW_R_NODE_ID)
                or light_cfg.get(CONF_LIGHT_RGBWW_R_NODE_ID)
            ):
                light_cfg[CONF_LIGHT_RGB_SCALE] = float(user_input.get(CONF_LIGHT_RGB_SCALE, DEFAULT_RGB_SCALE))
            if light_cfg.get(CONF_LIGHT_WHITE_NODE_ID):
                light_cfg[CONF_LIGHT_WHITE_SCALE] = float(
                    user_input.get(CONF_LIGHT_WHITE_SCALE, DEFAULT_WHITE_SCALE)
                )
            if light_cfg.get(CONF_LIGHT_XY_X_NODE_ID) or light_cfg.get(CONF_LIGHT_XY_Y_NODE_ID):
                light_cfg[CONF_LIGHT_XY_SCALE] = float(user_input.get(CONF_LIGHT_XY_SCALE, DEFAULT_XY_SCALE))

            effect_list = user_input.get(CONF_LIGHT_EFFECT_LIST)
            if effect_list:
                parsed = [item.strip() for item in str(effect_list).split(",") if item.strip()]
                if parsed:
                    light_cfg[CONF_LIGHT_EFFECT_LIST] = parsed

            self._options[CONF_NODES].append(light_cfg)
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON): TextSelector(),
                vol.Required(CONF_NODE_INVERT, default=False): BooleanSelector(),

                vol.Optional(CONF_LIGHT_BRIGHTNESS_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_BRIGHTNESS_SCALE,
                    default=DEFAULT_BRIGHTNESS_SCALE,
                ): NumberSelector(NumberSelectorConfig(min=1, max=65535, step=1, mode="box")),

                vol.Optional(CONF_LIGHT_COLOR_TEMP_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_COLOR_TEMP_MIN_KELVIN,
                    default=DEFAULT_COLOR_TEMP_MIN_KELVIN,
                ): NumberSelector(NumberSelectorConfig(min=1000, max=10000, step=1, mode="box")),
                vol.Optional(
                    CONF_LIGHT_COLOR_TEMP_MAX_KELVIN,
                    default=DEFAULT_COLOR_TEMP_MAX_KELVIN,
                ): NumberSelector(NumberSelectorConfig(min=1000, max=20000, step=1, mode="box")),

                vol.Optional(CONF_LIGHT_HS_HUE_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_HS_HUE_SCALE,
                    default=DEFAULT_HS_HUE_SCALE,
                ): NumberSelector(NumberSelectorConfig(min=1, max=10000, step=1, mode="box")),
                vol.Optional(CONF_LIGHT_HS_SAT_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_HS_SAT_SCALE,
                    default=DEFAULT_HS_SAT_SCALE,
                ): NumberSelector(NumberSelectorConfig(min=1, max=1000, step=1, mode="box")),

                vol.Optional(CONF_LIGHT_RGB_R_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGB_G_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGB_B_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBW_R_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBW_G_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBW_B_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBW_W_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBWW_R_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBWW_G_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBWW_B_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBWW_CW_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_RGBWW_WW_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_RGB_SCALE,
                    default=DEFAULT_RGB_SCALE,
                ): NumberSelector(NumberSelectorConfig(min=1, max=65535, step=1, mode="box")),

                vol.Optional(CONF_LIGHT_WHITE_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_WHITE_SCALE,
                    default=DEFAULT_WHITE_SCALE,
                ): NumberSelector(NumberSelectorConfig(min=1, max=65535, step=1, mode="box")),

                vol.Optional(CONF_LIGHT_XY_X_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_XY_Y_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_XY_SCALE,
                    default=str(DEFAULT_XY_SCALE),
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),

                vol.Optional(CONF_LIGHT_EFFECT_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_EFFECT_LIST): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Optional(CONF_LIGHT_TRANSITION_NODE_ID): TextSelector(),
                vol.Optional(CONF_LIGHT_FLASH_NODE_ID): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_light", data_schema=schema)

    def _guess_unit(self, name: str, path: str, engineering_units: str | None) -> str | None:
        if engineering_units:
            eu = engineering_units.lower()
            if "°c" in eu or "degc" in eu or "celsius" in eu:
                return "°C"
            if "bar" in eu:
                return "bar"
            if "rpm" in eu:
                return "rpm"
            if "percent" in eu or "%" in eu:
                return "%"
            if "volt" in eu or " v" in eu:
                return "V"
            if "amp" in eu or " a" in eu:
                return "A"
            if "hz" in eu:
                return "Hz"

        token = f"{name} {path}".lower()
        if "temp" in token:
            return "°C"
        if "humidity" in token or "feuchte" in token:
            return "%"
        if "pressure" in token or "druck" in token:
            return "bar"
        if "rpm" in token or "speed" in token or "drehzahl" in token:
            return "rpm"
        return None

    def _map_discovered_item(
        self,
        item: dict[str, Any],
        *,
        companion_profiles: bool,
        include_readonly: bool,
        prefer_lights: bool,
    ) -> dict[str, Any] | None:
        if item.get("node_class") != "Variable":
            return None

        node_id = str(item.get("node_id", ""))
        if not node_id:
            return None

        name = str(item.get("name") or node_id)
        path = str(item.get("path") or name)
        sample_type = str(item.get("sample_type", "")).lower()
        writable = bool(item.get("is_writable", False))

        if not include_readonly and not writable:
            return None

        marker = f"{name} {path} {item.get('type_definition', '')}".lower()
        is_alarm = any(k in marker for k in ["alarm", "condition", "offnormal"])
        is_stack_light = any(k in marker for k in ["stacklight", "towerlight", "beacon", "signal light", "lamp"])
        is_packml_state = any(k in marker for k in ["packml", "statecurrent", "machinestate", "machine_state"])

        if sample_type in ("bool", "boolean"):
            if companion_profiles and prefer_lights and writable and is_stack_light:
                return {
                    CONF_NODE_KIND: NODE_KIND_LIGHT,
                    CONF_NODE_NAME: name,
                    CONF_NODE_ID: node_id,
                    CONF_NODE_ICON: "mdi:alarm-light",
                }
            if writable:
                cfg = {
                    CONF_NODE_KIND: NODE_KIND_SWITCH,
                    CONF_NODE_NAME: name,
                    CONF_NODE_ID: node_id,
                }
                if companion_profiles and is_stack_light:
                    cfg[CONF_NODE_ICON] = "mdi:light-switch"
                return cfg

            cfg = {
                CONF_NODE_KIND: NODE_KIND_BINARY_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
            }
            if companion_profiles and is_alarm:
                cfg[CONF_NODE_DEVICE_CLASS] = "problem"
                cfg[CONF_NODE_ICON] = "mdi:alert-circle"
            return cfg

        if sample_type in ("int", "float", "int32", "int64", "uint16", "uint32", "uint64", "double"):
            cfg = {
                CONF_NODE_KIND: NODE_KIND_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
            }
            unit = self._guess_unit(name, path, item.get("engineering_units"))
            if unit:
                cfg[CONF_NODE_UNIT] = unit
            if companion_profiles and is_packml_state:
                cfg[CONF_NODE_ICON] = "mdi:state-machine"
            return cfg

        if sample_type in ("str", "string"):
            return {
                CONF_NODE_KIND: NODE_KIND_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
                CONF_NODE_ICON: "mdi:form-textbox",
            }

        # Fallback for unknown but readable variables
        if sample_type:
            return {
                CONF_NODE_KIND: NODE_KIND_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
            }

        return None

    @staticmethod
    def _parse_scalar_value(raw: Any) -> Any:
        if raw is None:
            return None
        s = str(raw).strip()
        if s == "":
            return None
        lower = s.lower()
        if lower in {"true", "on", "yes"}:
            return True
        if lower in {"false", "off", "no"}:
            return False
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            return s

    async def async_step_add_button(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            payload = self._parse_scalar_value(user_input.get(CONF_BUTTON_PAYLOAD))
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_BUTTON,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_BUTTON_PAYLOAD: True if payload is None else payload,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_BUTTON_PAYLOAD, default="true"): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:gesture-tap-button"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_button", data_schema=schema)

    async def async_step_add_climate(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_CLIMATE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_TARGET_NODE_ID: user_input.get(CONF_NODE_TARGET_NODE_ID) or None,
                    CONF_CLIMATE_HVAC_MODE_NODE_ID: user_input.get(CONF_CLIMATE_HVAC_MODE_NODE_ID) or None,
                    CONF_CLIMATE_MIN_TEMP: float(user_input.get(CONF_CLIMATE_MIN_TEMP, DEFAULT_CLIMATE_MIN_TEMP)),
                    CONF_CLIMATE_MAX_TEMP: float(user_input.get(CONF_CLIMATE_MAX_TEMP, DEFAULT_CLIMATE_MAX_TEMP)),
                    CONF_CLIMATE_TEMP_STEP: float(user_input.get(CONF_CLIMATE_TEMP_STEP, DEFAULT_CLIMATE_TEMP_STEP)),
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Required(CONF_NODE_TARGET_NODE_ID): TextSelector(),
                vol.Optional(CONF_CLIMATE_HVAC_MODE_NODE_ID): TextSelector(),
                vol.Required(CONF_CLIMATE_MIN_TEMP, default=DEFAULT_CLIMATE_MIN_TEMP): NumberSelector(
                    NumberSelectorConfig(min=-50, max=100, step=0.1, mode="box")
                ),
                vol.Required(CONF_CLIMATE_MAX_TEMP, default=DEFAULT_CLIMATE_MAX_TEMP): NumberSelector(
                    NumberSelectorConfig(min=-50, max=100, step=0.1, mode="box")
                ),
                vol.Required(CONF_CLIMATE_TEMP_STEP, default=DEFAULT_CLIMATE_TEMP_STEP): NumberSelector(
                    NumberSelectorConfig(min=0.1, max=5, step=0.1, mode="box")
                ),
                vol.Optional(CONF_NODE_ICON, default="mdi:thermostat"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_climate", data_schema=schema)

    async def async_step_add_cover(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_COVER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_TARGET_NODE_ID: user_input.get(CONF_NODE_TARGET_NODE_ID) or None,
                    CONF_COVER_SET_POSITION_NODE_ID: user_input.get(CONF_COVER_SET_POSITION_NODE_ID) or None,
                    CONF_COVER_OPEN_NODE_ID: user_input.get(CONF_COVER_OPEN_NODE_ID) or None,
                    CONF_COVER_CLOSE_NODE_ID: user_input.get(CONF_COVER_CLOSE_NODE_ID) or None,
                    CONF_COVER_STOP_NODE_ID: user_input.get(CONF_COVER_STOP_NODE_ID) or None,
                    CONF_COVER_INVERT_POSITION: bool(user_input.get(CONF_COVER_INVERT_POSITION, False)),
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_TARGET_NODE_ID): TextSelector(),
                vol.Optional(CONF_COVER_SET_POSITION_NODE_ID): TextSelector(),
                vol.Optional(CONF_COVER_OPEN_NODE_ID): TextSelector(),
                vol.Optional(CONF_COVER_CLOSE_NODE_ID): TextSelector(),
                vol.Optional(CONF_COVER_STOP_NODE_ID): TextSelector(),
                vol.Required(CONF_COVER_INVERT_POSITION, default=False): BooleanSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:blinds"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_cover", data_schema=schema)

    async def async_step_add_date(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_DATE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:calendar"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_date", data_schema=schema)

    async def async_step_add_datetime(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_DATETIME,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:calendar-clock"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_datetime", data_schema=schema)

    async def async_step_add_fan(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_FAN,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_FAN_SPEED_NODE_ID: user_input.get(CONF_FAN_SPEED_NODE_ID) or None,
                    CONF_NODE_INVERT: bool(user_input.get(CONF_NODE_INVERT, False)),
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_FAN_SPEED_NODE_ID): TextSelector(),
                vol.Required(CONF_NODE_INVERT, default=False): BooleanSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:fan"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_fan", data_schema=schema)

    async def async_step_add_notify(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_NOTIFY,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NOTIFY_MESSAGE_NODE_ID: user_input.get(CONF_NOTIFY_MESSAGE_NODE_ID) or None,
                    CONF_NOTIFY_TITLE_NODE_ID: user_input.get(CONF_NOTIFY_TITLE_NODE_ID) or None,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NOTIFY_MESSAGE_NODE_ID): TextSelector(),
                vol.Optional(CONF_NOTIFY_TITLE_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:message-alert"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_notify", data_schema=schema)

    async def async_step_add_number(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_NUMBER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NUMBER_MIN: float(user_input.get(CONF_NUMBER_MIN, DEFAULT_NUMBER_MIN)),
                    CONF_NUMBER_MAX: float(user_input.get(CONF_NUMBER_MAX, DEFAULT_NUMBER_MAX)),
                    CONF_NUMBER_STEP: float(user_input.get(CONF_NUMBER_STEP, DEFAULT_NUMBER_STEP)),
                    CONF_NODE_UNIT: user_input.get(CONF_NODE_UNIT) or None,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Required(CONF_NUMBER_MIN, default=DEFAULT_NUMBER_MIN): NumberSelector(
                    NumberSelectorConfig(min=-100000, max=100000, step=0.1, mode="box")
                ),
                vol.Required(CONF_NUMBER_MAX, default=DEFAULT_NUMBER_MAX): NumberSelector(
                    NumberSelectorConfig(min=-100000, max=100000, step=0.1, mode="box")
                ),
                vol.Required(CONF_NUMBER_STEP, default=DEFAULT_NUMBER_STEP): NumberSelector(
                    NumberSelectorConfig(min=0.001, max=10000, step=0.001, mode="box")
                ),
                vol.Optional(CONF_NODE_UNIT): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:numeric"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_number", data_schema=schema)

    async def async_step_add_scene(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            activate_value = self._parse_scalar_value(user_input.get(CONF_SCENE_ACTIVATE_VALUE))
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SCENE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_SCENE_ACTIVATE_VALUE: True if activate_value is None else activate_value,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_SCENE_ACTIVATE_VALUE, default="true"): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:palette"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_scene", data_schema=schema)

    async def async_step_add_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            options_raw = str(user_input.get(CONF_SELECT_OPTIONS) or "").strip()
            options = [x.strip() for x in options_raw.split(",") if x.strip()]
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SELECT,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_SELECT_OPTIONS: options,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Required(CONF_SELECT_OPTIONS): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:form-select"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_select", data_schema=schema)

    async def async_step_add_text(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_TEXT,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_TEXT_MAX: int(user_input.get(CONF_TEXT_MAX, 255)),
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Required(CONF_TEXT_MAX, default=255): NumberSelector(
                    NumberSelectorConfig(min=1, max=2048, step=1, mode="box")
                ),
                vol.Optional(CONF_NODE_ICON, default="mdi:form-textbox"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_text", data_schema=schema)

    async def async_step_add_time(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_TIME,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:clock-outline"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_time", data_schema=schema)

    async def async_step_add_weather(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_WEATHER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_WEATHER_HUMIDITY_NODE_ID: user_input.get(CONF_WEATHER_HUMIDITY_NODE_ID) or None,
                    CONF_WEATHER_PRESSURE_NODE_ID: user_input.get(CONF_WEATHER_PRESSURE_NODE_ID) or None,
                    CONF_WEATHER_WIND_SPEED_NODE_ID: user_input.get(CONF_WEATHER_WIND_SPEED_NODE_ID) or None,
                    CONF_WEATHER_CONDITION_NODE_ID: user_input.get(CONF_WEATHER_CONDITION_NODE_ID) or None,
                    CONF_NODE_ICON: user_input.get(CONF_NODE_ICON) or None,
                }
            )
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_NODE_NAME): TextSelector(),
                vol.Required(CONF_NODE_ID): TextSelector(),
                vol.Optional(CONF_WEATHER_HUMIDITY_NODE_ID): TextSelector(),
                vol.Optional(CONF_WEATHER_PRESSURE_NODE_ID): TextSelector(),
                vol.Optional(CONF_WEATHER_WIND_SPEED_NODE_ID): TextSelector(),
                vol.Optional(CONF_WEATHER_CONDITION_NODE_ID): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:weather-partly-cloudy"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_weather", data_schema=schema)

    async def async_step_auto_discovery(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            root_node_id = str(user_input.get("root_node_id", "i=85")).strip() or "i=85"
            depth = int(user_input.get("depth", 2))
            max_nodes = int(user_input.get("max_nodes", 400))
            import_limit = int(user_input.get("import_limit", 200))
            companion_profiles = bool(user_input.get("companion_profiles", True))
            include_readonly = bool(user_input.get("include_readonly", True))
            include_standard_nodes = bool(user_input.get("include_standard_nodes", False))
            prefer_lights = bool(user_input.get("prefer_lights", True))

            manager = OpcUaClientManager(
                endpoint=self._entry.data[CONF_ENDPOINT],
                security_policy=self._entry.data[CONF_SECURITY_POLICY],
                username=self._entry.data.get(CONF_USERNAME),
                password=self._entry.data.get(CONF_PASSWORD),
                client_cert_path=self._entry.data.get(CONF_CLIENT_CERT_PATH),
                client_key_path=self._entry.data.get(CONF_CLIENT_KEY_PATH),
                server_cert_path=self._entry.data.get(CONF_SERVER_CERT_PATH),
                client_key_password=self._entry.data.get(CONF_CLIENT_KEY_PASSWORD),
            )
            try:
                browsed = await manager.browse_nodes(
                    root_node_id=root_node_id,
                    depth=depth,
                    max_nodes=max_nodes,
                )
            except Exception as err:
                _LOGGER.warning("Auto discovery browse failed on %s: %s", self._entry.data[CONF_ENDPOINT], err)
                errors["base"] = "cannot_connect"
                browsed = []
            finally:
                await manager.disconnect()

            if not errors:
                candidates: list[dict[str, Any]] = []
                for item in browsed:
                    node_id = str(item.get("node_id", ""))
                    if not include_standard_nodes and node_id.startswith("i="):
                        continue

                    cfg = self._map_discovered_item(
                        item,
                        companion_profiles=companion_profiles,
                        include_readonly=include_readonly,
                        prefer_lights=prefer_lights,
                    )
                    if cfg:
                        candidates.append(cfg)

                # Deduplicate by node_id while preserving order
                seen: set[str] = set()
                deduped: list[dict[str, Any]] = []
                for cfg in candidates:
                    node_id = str(cfg.get(CONF_NODE_ID, ""))
                    if not node_id or node_id in seen:
                        continue
                    seen.add(node_id)
                    deduped.append(cfg)

                self._discovery_cache = deduped[:import_limit]
                return await self.async_step_auto_discovery_review()

        schema = vol.Schema(
            {
                vol.Required("root_node_id", default="i=85"): TextSelector(),
                vol.Required("depth", default=2): NumberSelector(
                    NumberSelectorConfig(min=1, max=6, step=1, mode="box")
                ),
                vol.Required("max_nodes", default=400): NumberSelector(
                    NumberSelectorConfig(min=20, max=2000, step=20, mode="box")
                ),
                vol.Required("import_limit", default=200): NumberSelector(
                    NumberSelectorConfig(min=1, max=2000, step=1, mode="box")
                ),
                vol.Required("companion_profiles", default=True): BooleanSelector(),
                vol.Required("include_readonly", default=True): BooleanSelector(),
                vol.Required("include_standard_nodes", default=False): BooleanSelector(),
                vol.Required("prefer_lights", default=True): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="auto_discovery", data_schema=schema, errors=errors)

    async def async_step_auto_discovery_review(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        if user_input is not None:
            if bool(user_input.get("apply", True)):
                self._append_unique_nodes(self._discovery_cache)
                await self._persist_options()
            return await self.async_step_init()

        total = len(self._discovery_cache)
        sensors = len([n for n in self._discovery_cache if n.get(CONF_NODE_KIND) == NODE_KIND_SENSOR])
        binary = len([n for n in self._discovery_cache if n.get(CONF_NODE_KIND) == NODE_KIND_BINARY_SENSOR])
        switches = len([n for n in self._discovery_cache if n.get(CONF_NODE_KIND) == NODE_KIND_SWITCH])
        lights = len([n for n in self._discovery_cache if n.get(CONF_NODE_KIND) == NODE_KIND_LIGHT])

        sample = ", ".join([str(n.get(CONF_NODE_NAME, "")) for n in self._discovery_cache[:5]]) or "-"

        schema = vol.Schema({vol.Required("apply", default=True): BooleanSelector()})
        return self.async_show_form(
            step_id="auto_discovery_review",
            data_schema=schema,
            description_placeholders={
                "total": str(total),
                "sensors": str(sensors),
                "binary": str(binary),
                "switches": str(switches),
                "lights": str(lights),
                "sample": sample,
            },
        )

    def _append_unique_nodes(self, new_nodes: list[dict[str, Any]]) -> int:
        existing_ids = {
            str(node.get(CONF_NODE_ID))
            for node in self._options.get(CONF_NODES, [])
            if node.get(CONF_NODE_ID)
        }
        added = 0
        for node in new_nodes:
            node_id = str(node.get(CONF_NODE_ID, ""))
            if not node_id or node_id in existing_ids:
                continue
            self._options[CONF_NODES].append(node)
            existing_ids.add(node_id)
            added += 1
        return added

    async def async_step_add_stack_light_profile(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            ns = int(user_input.get("namespace", 2))
            base = str(user_input.get("base_path", "Machine.StackLight")).strip()
            with_effect = bool(user_input.get("with_effect", False))
            effect_node_id = str(user_input.get("effect_node_id", "")).strip()

            nodes: list[dict[str, Any]] = []
            color_defs = [
                ("red", "Red", "mdi:alarm-light"),
                ("yellow", "Yellow", "mdi:alarm-light-outline"),
                ("green", "Green", "mdi:alarm-light"),
            ]
            for key, suffix, icon in color_defs:
                if not bool(user_input.get(f"include_{key}", True)):
                    continue
                cfg: dict[str, Any] = {
                    CONF_NODE_KIND: NODE_KIND_LIGHT,
                    CONF_NODE_NAME: f"Stack Light {suffix}",
                    CONF_NODE_ID: f"ns={ns};s={base}.{suffix}",
                    CONF_NODE_ICON: icon,
                }
                if with_effect and effect_node_id:
                    cfg[CONF_LIGHT_EFFECT_NODE_ID] = effect_node_id
                    cfg[CONF_LIGHT_EFFECT_LIST] = ["off", "blink", "flash"]
                nodes.append(cfg)

            if bool(user_input.get("include_buzzer", False)):
                nodes.append(
                    {
                        CONF_NODE_KIND: NODE_KIND_SWITCH,
                        CONF_NODE_NAME: "Stack Buzzer",
                        CONF_NODE_ID: f"ns={ns};s={base}.Buzzer",
                        CONF_NODE_ICON: "mdi:bullhorn",
                    }
                )

            self._append_unique_nodes(nodes)
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required("namespace", default=2): NumberSelector(
                    NumberSelectorConfig(min=0, max=1000, step=1, mode="box")
                ),
                vol.Required("base_path", default="Machine.StackLight"): TextSelector(),
                vol.Required("include_red", default=True): BooleanSelector(),
                vol.Required("include_yellow", default=True): BooleanSelector(),
                vol.Required("include_green", default=True): BooleanSelector(),
                vol.Required("include_buzzer", default=False): BooleanSelector(),
                vol.Required("with_effect", default=False): BooleanSelector(),
                vol.Optional("effect_node_id"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_stack_light_profile", data_schema=schema)

    async def async_step_discover_servers(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            discovery_url = str(user_input.get("discovery_url", "")).strip()
            include_network = bool(user_input.get("include_network", False))

            if not discovery_url:
                errors["discovery_url"] = "required"
            elif not discovery_url.lower().startswith("opc.tcp://"):
                errors["discovery_url"] = "invalid_endpoint"

            if not errors:
                try:
                    self._server_discovery_cache = await OpcUaClientManager.discover_servers(
                        discovery_url,
                        include_network=include_network,
                    )
                except Exception as err:
                    _LOGGER.warning("Server discovery failed for %s: %s", discovery_url, err)
                    errors["base"] = "cannot_connect"

                if not errors and not self._server_discovery_cache:
                    errors["base"] = "no_servers_found"

                if not errors:
                    return await self.async_step_discover_servers_select()

        schema = vol.Schema(
            {
                vol.Required(
                    "discovery_url",
                    default=str(self._entry.data.get(CONF_ENDPOINT, "opc.tcp://127.0.0.1:4840")),
                ): TextSelector(),
                vol.Required("include_network", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="discover_servers", data_schema=schema, errors=errors)

    async def async_step_discover_servers_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._server_discovery_cache:
            return await self.async_step_discover_servers()

        options = []
        by_key: dict[str, dict[str, Any]] = {}

        for idx, row in enumerate(self._server_discovery_cache):
            key = str(idx)
            app_name = str(row.get("application_name") or "OPC UA Server")
            endpoint_url = str(row.get("endpoint_url") or "")
            policy = str(row.get("security_policy") or "")
            mode = str(row.get("security_mode") or "")
            supported = bool(row.get("supported_now", False))
            marker = "✅" if supported else "⚠️"
            label = f"{marker} {app_name} | {endpoint_url} | {policy}/{mode}"
            options.append({"value": key, "label": label[:220]})
            by_key[key] = row

        if user_input is not None:
            selected_key = str(user_input.get("selected", ""))
            chosen = by_key.get(selected_key)
            if not chosen:
                return await self.async_step_discover_servers_select()

            endpoint_url = str(chosen.get("endpoint_url", "")).strip()
            policy_short = str(chosen.get("security_policy", "None")).strip() or "None"
            mode_raw = str(chosen.get("security_mode", "None")).strip() or "None"
            mode = mode_raw.rstrip("_")

            policy_map = {
                ("None", "None"): SECURITY_POLICY_NONE,
                ("Basic256Sha256", "Sign"): SECURITY_POLICY_BASIC256SHA256_SIGN,
                ("Basic256Sha256", "SignAndEncrypt"): SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
            }
            mapped_policy = policy_map.get((policy_short, mode))

            if mapped_policy is None:
                return self.async_show_form(
                    step_id="discover_servers_select",
                    data_schema=vol.Schema({
                        vol.Required("selected", default=selected_key): SelectSelector(
                            SelectSelectorConfig(
                                options=options,
                                multiple=False,
                                mode=SelectSelectorMode.DROPDOWN,
                            )
                        )
                    }),
                    errors={"base": "unsupported_security_policy"},
                )

            current_data = dict(self._entry.data)
            current_data[CONF_ENDPOINT] = endpoint_url
            current_data[CONF_SECURITY_POLICY] = mapped_policy
            self.hass.config_entries.async_update_entry(self._entry, data=current_data)
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required("selected"): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=False,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="discover_servers_select", data_schema=schema)

    async def async_step_browse_nodes(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            root_node_id = str(user_input.get("root_node_id", "i=85")).strip() or "i=85"
            depth = int(user_input.get("depth", 2))
            max_nodes = int(user_input.get("max_nodes", 200))

            manager = OpcUaClientManager(
                endpoint=self._entry.data[CONF_ENDPOINT],
                security_policy=self._entry.data[CONF_SECURITY_POLICY],
                username=self._entry.data.get(CONF_USERNAME),
                password=self._entry.data.get(CONF_PASSWORD),
                client_cert_path=self._entry.data.get(CONF_CLIENT_CERT_PATH),
                client_key_path=self._entry.data.get(CONF_CLIENT_KEY_PATH),
                server_cert_path=self._entry.data.get(CONF_SERVER_CERT_PATH),
                client_key_password=self._entry.data.get(CONF_CLIENT_KEY_PASSWORD),
            )
            try:
                self._browse_cache = await manager.browse_nodes(
                    root_node_id=root_node_id,
                    depth=depth,
                    max_nodes=max_nodes,
                )
                self._browse_root_node_id = root_node_id
                self._browse_current_parent = root_node_id
            except Exception as err:
                _LOGGER.warning("Browse failed on %s: %s", self._entry.data[CONF_ENDPOINT], err)
                errors["base"] = "cannot_connect"
            finally:
                await manager.disconnect()

            if not errors:
                return await self.async_step_browse_pick_kind()

        schema = vol.Schema(
            {
                vol.Required("root_node_id", default="i=85"): TextSelector(),
                vol.Required("depth", default=2): NumberSelector(
                    NumberSelectorConfig(min=1, max=6, step=1, mode="box")
                ),
                vol.Required("max_nodes", default=200): NumberSelector(
                    NumberSelectorConfig(min=10, max=1000, step=10, mode="box")
                ),
            }
        )
        return self.async_show_form(step_id="browse_nodes", data_schema=schema, errors=errors)

    async def async_step_browse_pick_kind(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._browse_cache:
            return await self.async_step_browse_nodes()

        return self.async_show_menu(
            step_id="browse_pick_kind",
            menu_options=[
                "browse_pick_kind_basic",
                "browse_pick_kind_advanced",
                "browse_nodes",
                "menu_discovery_tools",
                "init",
            ],
        )

    async def async_step_browse_pick_kind_basic(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="browse_pick_kind_basic",
            menu_options=[
                "browse_add_sensor",
                "browse_add_binary_sensor",
                "browse_add_switch",
                "browse_add_light",
                "browse_add_number",
                "browse_add_select",
                "browse_add_text",
                "browse_add_button",
                "browse_pick_kind",
                "init",
            ],
        )

    async def async_step_browse_pick_kind_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="browse_pick_kind_advanced",
            menu_options=[
                "browse_add_climate",
                "browse_add_cover",
                "browse_add_fan",
                "browse_add_scene",
                "browse_add_date",
                "browse_add_datetime",
                "browse_add_time",
                "browse_add_weather",
                "browse_add_notify",
                "browse_pick_kind",
                "init",
            ],
        )

    def _browse_options(self) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []
        for item in self._browse_cache:
            node_id = str(item.get("node_id", ""))
            node_class = str(item.get("node_class", ""))
            name = str(item.get("name", node_id))
            sample = str(item.get("sample_type", ""))
            writable = "RW" if item.get("is_writable") else "RO"
            label = f"{name} [{node_class}/{sample}/{writable}] · {node_id}"
            options.append({"value": node_id, "label": label[:180]})
        return options

    def _browse_indexes(self) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
        by_parent: dict[str, list[dict[str, Any]]] = {}
        by_id: dict[str, dict[str, Any]] = {}

        for item in self._browse_cache:
            node_id = str(item.get("node_id", ""))
            if not node_id:
                continue
            parent_id = str(item.get("parent_node_id", ""))
            by_id[node_id] = item
            by_parent.setdefault(parent_id, []).append(item)

        return by_parent, by_id

    def _label_for_browse_item(self, item: dict[str, Any]) -> str:
        node_id = str(item.get("node_id", ""))
        node_class = str(item.get("node_class", ""))
        name = str(item.get("name", node_id))
        sample = str(item.get("sample_type", ""))
        writable = "RW" if item.get("is_writable") else "RO"
        return f"{name} [{node_class}/{sample}/{writable}] · {node_id}"[:180]

    async def _browse_add_nodes_by_kind(
        self,
        step_id: str,
        kind: str,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        if not self._browse_cache:
            return await self.async_step_browse_nodes()

        by_parent, by_id = self._browse_indexes()
        if not self._browse_current_parent:
            self._browse_current_parent = self._browse_root_node_id

        if user_input is not None:
            selected_raw = user_input.get("node_ids", [])
            if isinstance(selected_raw, str):
                selected = [selected_raw]
            else:
                selected = list(selected_raw)

            nodes_to_add: list[dict[str, Any]] = []
            for node_id in selected:
                item = by_id.get(node_id)
                if not item:
                    continue
                cfg: dict[str, Any] = {
                    CONF_NODE_KIND: kind,
                    CONF_NODE_NAME: item.get("name") or node_id,
                    CONF_NODE_ID: node_id,
                }
                if kind == NODE_KIND_SWITCH:
                    cfg[CONF_NODE_ICON] = "mdi:toggle-switch"
                elif kind == NODE_KIND_LIGHT:
                    cfg[CONF_NODE_ICON] = "mdi:lightbulb"
                elif kind == NODE_KIND_BUTTON:
                    cfg[CONF_NODE_ICON] = "mdi:gesture-tap-button"
                elif kind == NODE_KIND_CLIMATE:
                    cfg[CONF_NODE_ICON] = "mdi:thermostat"
                elif kind == NODE_KIND_COVER:
                    cfg[CONF_NODE_ICON] = "mdi:blinds"
                elif kind == NODE_KIND_FAN:
                    cfg[CONF_NODE_ICON] = "mdi:fan"
                elif kind == NODE_KIND_NOTIFY:
                    cfg[CONF_NODE_ICON] = "mdi:message-alert"
                elif kind == NODE_KIND_NUMBER:
                    cfg[CONF_NODE_ICON] = "mdi:numeric"
                elif kind == NODE_KIND_SCENE:
                    cfg[CONF_NODE_ICON] = "mdi:palette"
                elif kind == NODE_KIND_SELECT:
                    cfg[CONF_NODE_ICON] = "mdi:form-select"
                elif kind == NODE_KIND_TEXT:
                    cfg[CONF_NODE_ICON] = "mdi:form-textbox"
                elif kind == NODE_KIND_DATE:
                    cfg[CONF_NODE_ICON] = "mdi:calendar"
                elif kind == NODE_KIND_DATETIME:
                    cfg[CONF_NODE_ICON] = "mdi:calendar-clock"
                elif kind == NODE_KIND_TIME:
                    cfg[CONF_NODE_ICON] = "mdi:clock-outline"
                elif kind == NODE_KIND_WEATHER:
                    cfg[CONF_NODE_ICON] = "mdi:weather-partly-cloudy"
                nodes_to_add.append(cfg)

            if nodes_to_add:
                self._append_unique_nodes(nodes_to_add)
                await self._persist_options()

            open_branch = user_input.get("open_branch")
            go_up = bool(user_input.get("go_up", False))

            if open_branch:
                self._browse_current_parent = str(open_branch)
            elif go_up and self._browse_current_parent != self._browse_root_node_id:
                parent_item = by_id.get(self._browse_current_parent)
                parent_of_parent = (
                    str(parent_item.get("parent_node_id", "")) if parent_item else self._browse_root_node_id
                )
                self._browse_current_parent = parent_of_parent or self._browse_root_node_id

            return await self._browse_add_nodes_by_kind(step_id, kind, None)

        children = by_parent.get(self._browse_current_parent, [])

        branch_options: list[dict[str, str]] = []
        import_options: list[dict[str, str]] = []

        for item in children:
            child_id = str(item.get("node_id", ""))
            node_class = str(item.get("node_class", ""))
            if not child_id:
                continue

            has_children = child_id in by_parent
            if has_children and node_class != "Variable":
                branch_options.append({"value": child_id, "label": f"📁 {self._label_for_browse_item(item)}"})

            if node_class == "Variable":
                import_options.append({"value": child_id, "label": f"🧩 {self._label_for_browse_item(item)}"})

        schema_dict: dict[Any, Any] = {}
        if import_options:
            schema_dict[vol.Optional("node_ids")] = SelectSelector(
                SelectSelectorConfig(
                    options=import_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        if branch_options:
            schema_dict[vol.Optional("open_branch")] = SelectSelector(
                SelectSelectorConfig(
                    options=branch_options,
                    multiple=False,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        if self._browse_current_parent != self._browse_root_node_id:
            schema_dict[vol.Optional("go_up", default=False)] = BooleanSelector()

        current_item = by_id.get(self._browse_current_parent)
        current_path = current_item.get("path") if current_item else self._browse_root_node_id

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "current": str(current_path),
                "count": str(len(import_options)),
            },
        )

    async def async_step_browse_add_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_sensor", NODE_KIND_SENSOR, user_input)

    async def async_step_browse_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_binary_sensor", NODE_KIND_BINARY_SENSOR, user_input
        )

    async def async_step_browse_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_switch", NODE_KIND_SWITCH, user_input)

    async def async_step_browse_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_light", NODE_KIND_LIGHT, user_input)

    async def async_step_browse_add_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_button", NODE_KIND_BUTTON, user_input)

    async def async_step_browse_add_climate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_climate", NODE_KIND_CLIMATE, user_input)

    async def async_step_browse_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_cover", NODE_KIND_COVER, user_input)

    async def async_step_browse_add_date(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_date", NODE_KIND_DATE, user_input)

    async def async_step_browse_add_datetime(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_datetime", NODE_KIND_DATETIME, user_input)

    async def async_step_browse_add_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_fan", NODE_KIND_FAN, user_input)

    async def async_step_browse_add_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_notify", NODE_KIND_NOTIFY, user_input)

    async def async_step_browse_add_number(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_number", NODE_KIND_NUMBER, user_input)

    async def async_step_browse_add_scene(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_scene", NODE_KIND_SCENE, user_input)

    async def async_step_browse_add_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_select", NODE_KIND_SELECT, user_input)

    async def async_step_browse_add_text(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_text", NODE_KIND_TEXT, user_input)

    async def async_step_browse_add_time(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_time", NODE_KIND_TIME, user_input)

    async def async_step_browse_add_weather(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind("browse_add_weather", NODE_KIND_WEATHER, user_input)

    async def async_step_remove_node(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        nodes = self._options.get(CONF_NODES, [])
        if not nodes:
            return await self.async_step_init()

        if user_input is not None:
            selected_raw = user_input.get("remove", [])
            if isinstance(selected_raw, str):
                selected = {selected_raw}
            else:
                selected = set(selected_raw)

            self._options[CONF_NODES] = [
                node for idx, node in enumerate(nodes) if str(idx) not in selected
            ]
            await self._persist_options()
            return await self.async_step_init()

        options = {
            str(idx): f"{node.get(CONF_NODE_NAME)} ({node.get(CONF_NODE_KIND)} | {node.get(CONF_NODE_ID)})"
            for idx, node in enumerate(nodes)
        }
        schema = vol.Schema(
            {
                vol.Required("remove"): SelectSelector(
                    SelectSelectorConfig(
                        options=[{"value": key, "label": label} for key, label in options.items()],
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="remove_node", data_schema=schema)

    async def async_step_set_poll_interval(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
            await self._persist_options()
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=int(self._options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)),
                ): NumberSelector(NumberSelectorConfig(min=1, max=60, step=1, mode="box"))
            }
        )
        return self.async_show_form(step_id="set_poll_interval", data_schema=schema)

