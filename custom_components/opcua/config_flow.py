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
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_CLIENT_KEY_PATH,
    CONF_ENDPOINT,
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
    CONF_NODE_UNIT,
    CONF_NODES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TITLE_PREFIX,
    CONF_SCAN_INTERVAL,
    CONF_SECURITY_POLICY,
    CONF_SERVER_CERT_PATH,
    CONF_VALIDATE_ON_SAVE,
    DEFAULT_BRIGHTNESS_SCALE,
    DEFAULT_COLOR_TEMP_MAX_KELVIN,
    DEFAULT_COLOR_TEMP_MIN_KELVIN,
    DEFAULT_HS_HUE_SCALE,
    DEFAULT_HS_SAT_SCALE,
    DEFAULT_NOTIFY_ENABLED,
    DEFAULT_NOTIFY_KEYWORDS,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_TITLE_PREFIX,
    DEFAULT_RGB_SCALE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_SECURITY_POLICY,
    DEFAULT_TITLE,
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
    SECURITY_POLICY_NONE,
    DEFAULT_VALIDATE_ON_SAVE,
    DEFAULT_WHITE_SCALE,
    DEFAULT_XY_SCALE,
    DOMAIN,
    NODE_KIND_BINARY_SENSOR,
    NODE_KIND_LIGHT,
    NODE_KIND_SENSOR,
    NODE_KIND_SWITCH,
    SECURITY_POLICIES,
)
from .opcua_client import OpcUaClientManager

_LOGGER = logging.getLogger(__name__)


class OpcUaMachineConfigFlow(ConfigFlow, domain=DOMAIN):
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

        # Validate endpoint quickly so we only prompt on real candidates.
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
            _LOGGER.debug("Zeroconf-discovered OPC-UA endpoint not reachable (%s): %s", endpoint, err)
            return self.async_abort(reason="cannot_connect")

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
        return OpcUaMachineOptionsFlow(config_entry)


class OpcUaMachineOptionsFlow(OptionsFlow):
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
                "add_sensor",
                "add_binary_sensor",
                "add_switch",
                "add_light",
                "add_stack_light_profile",
                "discover_servers",
                "auto_discovery",
                "browse_nodes",
                "remove_node",
                "set_poll_interval",
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
                "browse_add_sensor",
                "browse_add_binary_sensor",
                "browse_add_switch",
                "browse_add_light",
                "browse_nodes",
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

    async def async_step_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        # Changes are already auto-saved on each action.
        return self.async_abort(reason="finished")
