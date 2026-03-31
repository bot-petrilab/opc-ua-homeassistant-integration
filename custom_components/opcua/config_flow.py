from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import entity_registry as er
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
    CONF_NODE_DEVICE_ID,
    CONF_NODE_DEVICE_MANUFACTURER,
    CONF_NODE_DEVICE_MODEL,
    CONF_NODE_DEVICE_NAME,
    CONF_NODE_DEVICE_SERIAL,
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
    CONF_SCENE_ACTIVATE_VALUE,
    CONF_SECURITY_POLICY,
    CONF_SELECT_OPTIONS,
    CONF_SERVER_CERT_PATH,
    CONF_TEXT_MAX,
    CONF_VALIDATE_ON_SAVE,
    CONF_VALVE_CLOSE_NODE_ID,
    CONF_VALVE_INVERT_POSITION,
    CONF_VALVE_OPEN_NODE_ID,
    CONF_VALVE_SET_POSITION_NODE_ID,
    CONF_VALVE_STOP_NODE_ID,
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
    NODE_KIND_VALVE,
    NODE_KIND_WEATHER,
    SECURITY_POLICIES,
    SECURITY_POLICY_BASIC256SHA256_SIGN,
    SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
    SECURITY_POLICY_NONE,
)
from .opcua_client import OpcUaClientManager

_LOGGER = logging.getLogger(__name__)


def _friendly_node_name(item: Mapping[str, Any]) -> str:
    path = str(item.get("path") or "").strip("/")
    if path:
        leaf = path.split("/")[-1]
        parent = path.split("/")[-2] if len(path.split("/")) >= 2 else ""
        if parent and leaf:
            return f"{parent.replace('_', ' ').title().replace(' ', '')} – {leaf.replace('_', ' ').title()}"
        if leaf:
            return leaf.replace('_', ' ').title()
    name = str(item.get("name") or item.get("node_id") or "Node")
    return name.replace('_', ' ').title()


def _browse_option_label(item: Mapping[str, Any]) -> str:
    label = _friendly_node_name(item)
    sample_type = str(item.get("sample_type") or "unknown")
    writable = bool(item.get("is_writable", False))
    access = "writable" if writable else "read-only"
    return f"{label} ({sample_type}, {access})"


def _browse_folder_label(item: Mapping[str, Any]) -> str:
    name = str(item.get("name") or item.get("path") or "Folder")
    return name.strip("/").split("/")[-1].replace('_', ' ').title()


class OpcUaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OPC-UA."""

    VERSION = 1

    _discovered_endpoint: str | None = None
    _discovered_name: str | None = None
    _pending_user_data: dict[str, Any] | None = None
    _pending_zeroconf_data: dict[str, Any] | None = None

    @staticmethod
    def _normalize_keywords(raw: str | None) -> list[str]:
        text = str(raw or "").strip()
        if not text:
            return list(DEFAULT_NOTIFY_KEYWORDS)
        return [k.strip().lower() for k in text.split(",") if k.strip()]

    @staticmethod
    def _notification_schema(defaults: Mapping[str, Any]) -> dict[Any, Any]:
        return {
            vol.Optional(
                CONF_NOTIFY_ENABLED, default=defaults.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED)
            ): BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_SERVICE,
                default=defaults.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
            vol.Optional(
                CONF_NOTIFY_TITLE_PREFIX,
                default=defaults.get(CONF_NOTIFY_TITLE_PREFIX, DEFAULT_NOTIFY_TITLE_PREFIX),
            ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
            vol.Optional(
                CONF_NOTIFY_KEYWORDS,
                default=defaults.get(CONF_NOTIFY_KEYWORDS, ",".join(DEFAULT_NOTIFY_KEYWORDS)),
            ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
        }

    @staticmethod
    def _security_schema(defaults: Mapping[str, Any]) -> dict[Any, Any]:
        return {
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): TextSelector(
                TextSelectorConfig(type="text")
            ),
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): TextSelector(
                TextSelectorConfig(type="password")
            ),
            vol.Optional(CONF_CLIENT_CERT_PATH, default=defaults.get(CONF_CLIENT_CERT_PATH, "")): TextSelector(
                TextSelectorConfig(type="text", autocomplete="off")
            ),
            vol.Optional(CONF_CLIENT_KEY_PATH, default=defaults.get(CONF_CLIENT_KEY_PATH, "")): TextSelector(
                TextSelectorConfig(type="text", autocomplete="off")
            ),
            vol.Optional(CONF_SERVER_CERT_PATH, default=defaults.get(CONF_SERVER_CERT_PATH, "")): TextSelector(
                TextSelectorConfig(type="text", autocomplete="off")
            ),
            vol.Optional(CONF_CLIENT_KEY_PASSWORD, default=defaults.get(CONF_CLIENT_KEY_PASSWORD, "")): TextSelector(
                TextSelectorConfig(type="password")
            ),
        }

    async def _validate_pending_connection(self, pending: Mapping[str, Any]) -> bool:
        if not pending.get(CONF_VALIDATE_ON_SAVE, DEFAULT_VALIDATE_ON_SAVE):
            return True
        manager = OpcUaClientManager(
            endpoint=str(pending[CONF_ENDPOINT]),
            security_policy=str(pending[CONF_SECURITY_POLICY]),
            username=pending.get(CONF_USERNAME) or None,
            password=pending.get(CONF_PASSWORD) or None,
            client_cert_path=pending.get(CONF_CLIENT_CERT_PATH) or None,
            client_key_path=pending.get(CONF_CLIENT_KEY_PATH) or None,
            server_cert_path=pending.get(CONF_SERVER_CERT_PATH) or None,
            client_key_password=pending.get(CONF_CLIENT_KEY_PASSWORD) or None,
        )
        await manager.ensure_connected()
        await manager.disconnect()
        return True


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
                "Zeroconf-discovered OPC-UA endpoint probe failed (%s): %s",
                endpoint,
                err,
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
            return await self.async_step_zeroconf_setup()
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "name": self._discovered_name or "OPC UA Server",
                "endpoint": endpoint,
            },
        )

    async def async_step_zeroconf_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the basic security mode for a discovered OPC-UA server."""
        endpoint = self._discovered_endpoint
        if not endpoint:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            security_policy = str(user_input[CONF_SECURITY_POLICY]).strip()
            validate_on_save = bool(
                user_input.get(CONF_VALIDATE_ON_SAVE, DEFAULT_VALIDATE_ON_SAVE)
            )
            self._pending_zeroconf_data = {
                CONF_ENDPOINT: endpoint,
                CONF_SECURITY_POLICY: security_policy,
                CONF_VALIDATE_ON_SAVE: validate_on_save,
            }
            if security_policy == SECURITY_POLICY_NONE:
                return await self.async_step_zeroconf_notifications()
            return await self.async_step_zeroconf_auth()

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SECURITY_POLICY, default=DEFAULT_SECURITY_POLICY
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SECURITY_POLICIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_VALIDATE_ON_SAVE, default=DEFAULT_VALIDATE_ON_SAVE
                ): BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="zeroconf_setup",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "name": self._discovered_name or "OPC UA Server",
                "endpoint": endpoint,
            },
        )

    async def async_step_zeroconf_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        pending = self._pending_zeroconf_data or {}
        if not pending:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            pending.update({
                CONF_USERNAME: (user_input.get(CONF_USERNAME) or None),
                CONF_PASSWORD: (user_input.get(CONF_PASSWORD) or None),
                CONF_CLIENT_CERT_PATH: (user_input.get(CONF_CLIENT_CERT_PATH) or "").strip() or None,
                CONF_CLIENT_KEY_PATH: (user_input.get(CONF_CLIENT_KEY_PATH) or "").strip() or None,
                CONF_SERVER_CERT_PATH: (user_input.get(CONF_SERVER_CERT_PATH) or "").strip() or None,
                CONF_CLIENT_KEY_PASSWORD: (user_input.get(CONF_CLIENT_KEY_PASSWORD) or None),
            })
            return await self.async_step_zeroconf_notifications()

        return self.async_show_form(
            step_id="zeroconf_auth",
            data_schema=vol.Schema(self._security_schema(pending)),
            errors=errors,
            description_placeholders={"endpoint": str(pending[CONF_ENDPOINT])},
        )

    async def async_step_zeroconf_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        pending = self._pending_zeroconf_data or {}
        if not pending:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            pending.update({
                CONF_NOTIFY_ENABLED: bool(user_input.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED)),
                CONF_NOTIFY_SERVICE: str(user_input.get(CONF_NOTIFY_SERVICE) or DEFAULT_NOTIFY_SERVICE).strip(),
                CONF_NOTIFY_TITLE_PREFIX: str(user_input.get(CONF_NOTIFY_TITLE_PREFIX) or DEFAULT_NOTIFY_TITLE_PREFIX).strip(),
                CONF_NOTIFY_KEYWORDS: self._normalize_keywords(user_input.get(CONF_NOTIFY_KEYWORDS)),
                CONF_NODES: [],
            })
            try:
                await self._validate_pending_connection(pending)
            except Exception as err:
                _LOGGER.warning(
                    "OPC UA zeroconf setup validation failed for %s: %s",
                    pending.get(CONF_ENDPOINT),
                    err,
                )
                errors["base"] = "cannot_connect"
            if not errors:
                title = self._discovered_name or str(pending[CONF_ENDPOINT])
                data = dict(pending)
                data.pop(CONF_VALIDATE_ON_SAVE, None)
                return self.async_create_entry(title=title, data=data)

        defaults = {
            CONF_NOTIFY_ENABLED: pending.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED),
            CONF_NOTIFY_SERVICE: pending.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            CONF_NOTIFY_TITLE_PREFIX: pending.get(CONF_NOTIFY_TITLE_PREFIX, DEFAULT_NOTIFY_TITLE_PREFIX),
            CONF_NOTIFY_KEYWORDS: ",".join(pending.get(CONF_NOTIFY_KEYWORDS, DEFAULT_NOTIFY_KEYWORDS)),
        }
        return self.async_show_form(
            step_id="zeroconf_notifications",
            data_schema=vol.Schema(self._notification_schema(defaults)),
            errors=errors,
            description_placeholders={"endpoint": str(pending[CONF_ENDPOINT])},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            endpoint = str(user_input[CONF_ENDPOINT]).strip()
            security_policy = str(user_input[CONF_SECURITY_POLICY]).strip()
            title = str(user_input.get("title") or DEFAULT_TITLE).strip() or DEFAULT_TITLE
            validate_on_save = bool(
                user_input.get(CONF_VALIDATE_ON_SAVE, DEFAULT_VALIDATE_ON_SAVE)
            )

            if not endpoint:
                errors[CONF_ENDPOINT] = "required"
            elif not endpoint.lower().startswith("opc.tcp://"):
                errors[CONF_ENDPOINT] = "invalid_endpoint"

            if not errors:
                for entry in self._async_current_entries():
                    if str((entry.data or {}).get(CONF_ENDPOINT, "")).strip() == endpoint:
                        return self.async_abort(reason="already_configured")

            if not errors:
                self._pending_user_data = {
                    "title": title,
                    CONF_ENDPOINT: endpoint,
                    CONF_SECURITY_POLICY: security_policy,
                    CONF_VALIDATE_ON_SAVE: validate_on_save,
                }
                if security_policy == SECURITY_POLICY_NONE:
                    return await self.async_step_user_notifications()
                return await self.async_step_user_auth()

        data_schema = vol.Schema(
            {
                vol.Optional("title", default=DEFAULT_TITLE): TextSelector(),
                vol.Required(CONF_ENDPOINT): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                ),
                vol.Required(
                    CONF_SECURITY_POLICY, default=DEFAULT_SECURITY_POLICY
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SECURITY_POLICIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_VALIDATE_ON_SAVE, default=DEFAULT_VALIDATE_ON_SAVE
                ): BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_user_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        pending = self._pending_user_data or {}
        if not pending:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            pending.update({
                CONF_USERNAME: (user_input.get(CONF_USERNAME) or None),
                CONF_PASSWORD: (user_input.get(CONF_PASSWORD) or None),
                CONF_CLIENT_CERT_PATH: (user_input.get(CONF_CLIENT_CERT_PATH) or "").strip() or None,
                CONF_CLIENT_KEY_PATH: (user_input.get(CONF_CLIENT_KEY_PATH) or "").strip() or None,
                CONF_SERVER_CERT_PATH: (user_input.get(CONF_SERVER_CERT_PATH) or "").strip() or None,
                CONF_CLIENT_KEY_PASSWORD: (user_input.get(CONF_CLIENT_KEY_PASSWORD) or None),
            })
            return await self.async_step_user_notifications()

        return self.async_show_form(
            step_id="user_auth",
            data_schema=vol.Schema(self._security_schema(pending)),
            errors={},
            description_placeholders={"endpoint": str(pending[CONF_ENDPOINT])},
        )

    async def async_step_user_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        pending = self._pending_user_data or {}
        if not pending:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            pending.update({
                CONF_NOTIFY_ENABLED: bool(user_input.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED)),
                CONF_NOTIFY_SERVICE: str(user_input.get(CONF_NOTIFY_SERVICE) or DEFAULT_NOTIFY_SERVICE).strip(),
                CONF_NOTIFY_TITLE_PREFIX: str(user_input.get(CONF_NOTIFY_TITLE_PREFIX) or DEFAULT_NOTIFY_TITLE_PREFIX).strip(),
                CONF_NOTIFY_KEYWORDS: self._normalize_keywords(user_input.get(CONF_NOTIFY_KEYWORDS)),
                CONF_NODES: [],
            })
            try:
                await self._validate_pending_connection(pending)
            except Exception as err:
                _LOGGER.warning(
                    "OPC UA validation failed for %s: %s", pending.get(CONF_ENDPOINT), err
                )
                errors["base"] = "cannot_connect"
            if not errors:
                title = str(pending.get("title") or DEFAULT_TITLE)
                data = dict(pending)
                data.pop("title", None)
                data.pop(CONF_VALIDATE_ON_SAVE, None)
                return self.async_create_entry(title=title, data=data)

        defaults = {
            CONF_NOTIFY_ENABLED: pending.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED),
            CONF_NOTIFY_SERVICE: pending.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            CONF_NOTIFY_TITLE_PREFIX: pending.get(CONF_NOTIFY_TITLE_PREFIX, DEFAULT_NOTIFY_TITLE_PREFIX),
            CONF_NOTIFY_KEYWORDS: ",".join(pending.get(CONF_NOTIFY_KEYWORDS, DEFAULT_NOTIFY_KEYWORDS)),
        }
        return self.async_show_form(
            step_id="user_notifications",
            data_schema=vol.Schema(self._notification_schema(defaults)),
            errors=errors,
            description_placeholders={"endpoint": str(pending[CONF_ENDPOINT])},
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle re-authentication flow when credentials/security changed."""
        self._reauth_entry = self._get_reauth_entry()
        self._discovered_endpoint = str(
            (self._reauth_entry.data or {}).get(CONF_ENDPOINT, "")
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = getattr(self, "_reauth_entry", None)
        if entry is None:
            return self.async_abort(reason="cannot_connect")

        endpoint = str((entry.data or {}).get(CONF_ENDPOINT, ""))
        if not endpoint:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            security_policy = str(user_input[CONF_SECURITY_POLICY]).strip()
            username = user_input.get(CONF_USERNAME) or None
            password = user_input.get(CONF_PASSWORD) or None
            client_cert_path = (
                user_input.get(CONF_CLIENT_CERT_PATH) or ""
            ).strip() or None
            client_key_path = (
                user_input.get(CONF_CLIENT_KEY_PATH) or ""
            ).strip() or None
            server_cert_path = (
                user_input.get(CONF_SERVER_CERT_PATH) or ""
            ).strip() or None
            client_key_password = user_input.get(CONF_CLIENT_KEY_PASSWORD) or None

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
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_SECURITY_POLICY: security_policy,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_CLIENT_CERT_PATH: client_cert_path,
                        CONF_CLIENT_KEY_PATH: client_key_path,
                        CONF_SERVER_CERT_PATH: server_cert_path,
                        CONF_CLIENT_KEY_PASSWORD: client_key_password,
                    },
                )

        defaults = entry.data or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SECURITY_POLICY,
                    default=str(
                        defaults.get(CONF_SECURITY_POLICY, DEFAULT_SECURITY_POLICY)
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SECURITY_POLICIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_USERNAME, default=defaults.get(CONF_USERNAME) or ""
                ): TextSelector(TextSelectorConfig(type="text")),
                vol.Optional(
                    CONF_PASSWORD, default=defaults.get(CONF_PASSWORD) or ""
                ): TextSelector(TextSelectorConfig(type="password")),
                vol.Optional(
                    CONF_CLIENT_CERT_PATH,
                    default=defaults.get(CONF_CLIENT_CERT_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_CLIENT_KEY_PATH,
                    default=defaults.get(CONF_CLIENT_KEY_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_SERVER_CERT_PATH,
                    default=defaults.get(CONF_SERVER_CERT_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_CLIENT_KEY_PASSWORD,
                    default=defaults.get(CONF_CLIENT_KEY_PASSWORD) or "",
                ): TextSelector(TextSelectorConfig(type="password")),
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow editing endpoint/security fields from the UI reconfigure action."""
        entry = self._get_reconfigure_entry()
        defaults = entry.data or {}
        errors: dict[str, str] = {}

        if user_input is not None:
            endpoint = str(user_input[CONF_ENDPOINT]).strip()
            security_policy = str(user_input[CONF_SECURITY_POLICY]).strip()
            username = user_input.get(CONF_USERNAME) or None
            password = user_input.get(CONF_PASSWORD) or None
            client_cert_path = (
                user_input.get(CONF_CLIENT_CERT_PATH) or ""
            ).strip() or None
            client_key_path = (
                user_input.get(CONF_CLIENT_KEY_PATH) or ""
            ).strip() or None
            server_cert_path = (
                user_input.get(CONF_SERVER_CERT_PATH) or ""
            ).strip() or None
            client_key_password = user_input.get(CONF_CLIENT_KEY_PASSWORD) or None
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
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_ENDPOINT: endpoint,
                        CONF_SECURITY_POLICY: security_policy,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_CLIENT_CERT_PATH: client_cert_path,
                        CONF_CLIENT_KEY_PATH: client_key_path,
                        CONF_SERVER_CERT_PATH: server_cert_path,
                        CONF_CLIENT_KEY_PASSWORD: client_key_password,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENDPOINT, default=str(defaults.get(CONF_ENDPOINT, ""))
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Required(
                    CONF_SECURITY_POLICY,
                    default=str(
                        defaults.get(CONF_SECURITY_POLICY, DEFAULT_SECURITY_POLICY)
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=list(SECURITY_POLICIES),
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_USERNAME, default=defaults.get(CONF_USERNAME) or ""
                ): TextSelector(TextSelectorConfig(type="text")),
                vol.Optional(
                    CONF_PASSWORD, default=defaults.get(CONF_PASSWORD) or ""
                ): TextSelector(TextSelectorConfig(type="password")),
                vol.Optional(
                    CONF_CLIENT_CERT_PATH,
                    default=defaults.get(CONF_CLIENT_CERT_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_CLIENT_KEY_PATH,
                    default=defaults.get(CONF_CLIENT_KEY_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_SERVER_CERT_PATH,
                    default=defaults.get(CONF_SERVER_CERT_PATH) or "",
                ): TextSelector(TextSelectorConfig(type="text", autocomplete="off")),
                vol.Optional(
                    CONF_CLIENT_KEY_PASSWORD,
                    default=defaults.get(CONF_CLIENT_KEY_PASSWORD) or "",
                ): TextSelector(TextSelectorConfig(type="password")),
            }
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OpcUaOptionsFlow(config_entry)


class OpcUaOptionsFlow(OptionsFlow):
    """Handle options flow for OPC-UA."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry
        self._options: dict[str, Any] = dict(config_entry.options)
        self._options.setdefault(
            CONF_NODES, list(config_entry.data.get(CONF_NODES, []))
        )
        self._browse_cache: list[dict[str, Any]] = []
        self._browse_root_node_id: str = "i=85"
        self._browse_current_parent: str = "i=85"
        self._discovery_cache: list[dict[str, Any]] = []
        self._server_discovery_cache: list[dict[str, Any]] = []

    async def _persist_options(self) -> None:
        """Persist options immediately and reload entry so entities appear at once."""
        self.hass.config_entries.async_update_entry(self._entry, options=self._options)
        await self._cleanup_orphan_entity_registry_entries()
        await self.hass.config_entries.async_reload(self._entry.entry_id)

    async def _cleanup_orphan_entity_registry_entries(self) -> None:
        """Remove entity-registry entries that are no longer present in options nodes."""
        registry = er.async_get(self.hass)

        wanted_node_ids = {
            str(node.get(CONF_NODE_ID, ""))
            for node in self._options.get(CONF_NODES, [])
            if node.get(CONF_NODE_ID)
        }

        for entry in er.async_entries_for_config_entry(registry, self._entry.entry_id):
            uid = str(entry.unique_id or "")
            # unique_id format in this integration: "{entry_id}:{entity_kind}:{node_id}"
            parts = uid.split(":", 2)
            if len(parts) != 3:
                continue
            if parts[0] != self._entry.entry_id:
                continue

            node_id = parts[2]
            if node_id not in wanted_node_ids:
                registry.async_remove(entry.entity_id)

    async def async_step_init(
        self, user_input: Mapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "menu_add_entities",
                "menu_discovery_tools",
                "menu_settings",
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
                "add_valve",
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
                "init",
            ],
        )

    async def async_step_add_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SENSOR,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_UNIT: user_input.get(CONF_NODE_UNIT) or None,
                    CONF_NODE_DEVICE_CLASS: user_input.get(CONF_NODE_DEVICE_CLASS)
                    or None,
                    CONF_NODE_STATE_CLASS: user_input.get(CONF_NODE_STATE_CLASS)
                    or None,
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

    async def async_step_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_BINARY_SENSOR,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_DEVICE_CLASS: user_input.get(CONF_NODE_DEVICE_CLASS)
                    or None,
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

    async def async_step_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                    user_input.get(
                        CONF_LIGHT_BRIGHTNESS_SCALE, DEFAULT_BRIGHTNESS_SCALE
                    )
                )
            if light_cfg.get(CONF_LIGHT_COLOR_TEMP_NODE_ID):
                light_cfg[CONF_LIGHT_COLOR_TEMP_MIN_KELVIN] = int(
                    user_input.get(
                        CONF_LIGHT_COLOR_TEMP_MIN_KELVIN, DEFAULT_COLOR_TEMP_MIN_KELVIN
                    )
                )
                light_cfg[CONF_LIGHT_COLOR_TEMP_MAX_KELVIN] = int(
                    user_input.get(
                        CONF_LIGHT_COLOR_TEMP_MAX_KELVIN, DEFAULT_COLOR_TEMP_MAX_KELVIN
                    )
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
                light_cfg[CONF_LIGHT_RGB_SCALE] = float(
                    user_input.get(CONF_LIGHT_RGB_SCALE, DEFAULT_RGB_SCALE)
                )
            if light_cfg.get(CONF_LIGHT_WHITE_NODE_ID):
                light_cfg[CONF_LIGHT_WHITE_SCALE] = float(
                    user_input.get(CONF_LIGHT_WHITE_SCALE, DEFAULT_WHITE_SCALE)
                )
            if light_cfg.get(CONF_LIGHT_XY_X_NODE_ID) or light_cfg.get(
                CONF_LIGHT_XY_Y_NODE_ID
            ):
                light_cfg[CONF_LIGHT_XY_SCALE] = float(
                    user_input.get(CONF_LIGHT_XY_SCALE, DEFAULT_XY_SCALE)
                )

            effect_list = user_input.get(CONF_LIGHT_EFFECT_LIST)
            if effect_list:
                parsed = [
                    item.strip() for item in str(effect_list).split(",") if item.strip()
                ]
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
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, step=1, mode="box")
                ),
                vol.Optional(CONF_LIGHT_COLOR_TEMP_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_COLOR_TEMP_MIN_KELVIN,
                    default=DEFAULT_COLOR_TEMP_MIN_KELVIN,
                ): NumberSelector(
                    NumberSelectorConfig(min=1000, max=10000, step=1, mode="box")
                ),
                vol.Optional(
                    CONF_LIGHT_COLOR_TEMP_MAX_KELVIN,
                    default=DEFAULT_COLOR_TEMP_MAX_KELVIN,
                ): NumberSelector(
                    NumberSelectorConfig(min=1000, max=20000, step=1, mode="box")
                ),
                vol.Optional(CONF_LIGHT_HS_HUE_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_HS_HUE_SCALE,
                    default=DEFAULT_HS_HUE_SCALE,
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=10000, step=1, mode="box")
                ),
                vol.Optional(CONF_LIGHT_HS_SAT_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_HS_SAT_SCALE,
                    default=DEFAULT_HS_SAT_SCALE,
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=1000, step=1, mode="box")
                ),
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
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, step=1, mode="box")
                ),
                vol.Optional(CONF_LIGHT_WHITE_NODE_ID): TextSelector(),
                vol.Optional(
                    CONF_LIGHT_WHITE_SCALE,
                    default=DEFAULT_WHITE_SCALE,
                ): NumberSelector(
                    NumberSelectorConfig(min=1, max=65535, step=1, mode="box")
                ),
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

    def _guess_unit(
        self, name: str, path: str, engineering_units: str | None
    ) -> str | None:
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

    def _guess_sensor_classes(self, name: str, path: str) -> tuple[str | None, str | None]:
        token = f"{name} {path}".lower()
        if "temp" in token:
            return "temperature", "measurement"
        if "humidity" in token or "feuchte" in token:
            return "humidity", "measurement"
        if "pressure" in token or "druck" in token:
            return "pressure", "measurement"
        if "power" in token:
            return "power", "measurement"
        return None, None

    def _guess_binary_sensor_class(self, name: str, path: str) -> str | None:
        token = f"{name} {path}".lower()
        if "motion" in token or "beweg" in token:
            return "motion"
        if "door" in token or "window" in token or "fenster" in token or "tür" in token:
            return "door"
        if "alarm" in token or "fault" in token or "problem" in token:
            return "problem"
        return None

    @staticmethod
    def _normalize_discovery_name(name: str) -> str:
        return "".join(
            ch for ch in str(name).strip().lower() if ch.isalnum() or ch == "_"
        )

    def _extract_device_contexts(
        self, browsed: list[dict[str, Any]]
    ) -> dict[str, dict[str, str]]:
        """Build per-node device metadata by finding nearest device-like parent object."""
        by_id: dict[str, dict[str, Any]] = {
            str(item.get("node_id")): item for item in browsed if item.get("node_id")
        }
        children_by_parent: dict[str, list[dict[str, Any]]] = {}
        for item in browsed:
            parent = str(item.get("parent_node_id") or "")
            if not parent:
                continue
            children_by_parent.setdefault(parent, []).append(item)

        def _read_child_value(
            children: list[dict[str, Any]], *names: str
        ) -> str | None:
            wanted = set(names)
            for child in children:
                if str(child.get("node_class")) != "Variable":
                    continue
                n = self._normalize_discovery_name(str(child.get("name") or ""))
                if n in wanted:
                    value = child.get("sample_value")
                    if value is not None and str(value).strip() != "":
                        return str(value).strip()
            return None

        device_nodes: dict[str, dict[str, str]] = {}
        for node_id, item in by_id.items():
            if str(item.get("node_class")) != "Object":
                continue

            children = children_by_parent.get(node_id, [])
            manufacturer = _read_child_value(children, "manufacturer", "vendorname")
            model = _read_child_value(children, "model", "modelname")
            serial = _read_child_value(children, "serialnumber", "serial", "serialno")
            device_name = _read_child_value(children, "devicename", "name") or str(
                item.get("name") or ""
            )

            type_def = str(item.get("type_definition") or "").lower()
            # Device classification strictly via HasTypeDefinition marker.
            if "devicetype" not in type_def:
                continue

            device_nodes[node_id] = {
                CONF_NODE_DEVICE_ID: node_id,
                CONF_NODE_DEVICE_NAME: device_name or node_id,
                CONF_NODE_DEVICE_MANUFACTURER: manufacturer
                or "OPC Foundation / PLC Vendor",
                CONF_NODE_DEVICE_MODEL: model or "OPC UA Device",
                CONF_NODE_DEVICE_SERIAL: serial or "",
            }

        contexts: dict[str, dict[str, str]] = {}
        for node_id in by_id:
            current = node_id
            while current:
                if current in device_nodes:
                    contexts[node_id] = device_nodes[current]
                    break
                current = str(by_id.get(current, {}).get("parent_node_id") or "")

        return contexts

    def _discover_light_object_nodes(
        self,
        browsed: list[dict[str, Any]],
        *,
        include_readonly: bool,
        device_contexts: dict[str, dict[str, str]] | None = None,
    ) -> tuple[list[dict[str, Any]], set[str]]:
        """Detect OPC-UA Light objects via Object TypeDefinition (LightType).

        Returns a tuple: (light_node_configs, consumed_node_ids)
        consumed_node_ids are skipped by generic scalar discovery to avoid duplicates.
        """
        by_id: dict[str, dict[str, Any]] = {
            str(item.get("node_id")): item for item in browsed if item.get("node_id")
        }

        children_by_parent: dict[str, list[dict[str, Any]]] = {}
        for item in browsed:
            parent = str(item.get("parent_node_id") or "")
            if not parent:
                continue
            children_by_parent.setdefault(parent, []).append(item)

        discovered: list[dict[str, Any]] = []
        consumed_ids: set[str] = set()

        for node_id, item in by_id.items():
            if str(item.get("node_class")) != "Object":
                continue

            type_def = str(item.get("type_definition") or "")
            type_is_light = "lighttype" in type_def.lower()

            children = children_by_parent.get(node_id, [])
            child_by_name: dict[str, dict[str, Any]] = {}
            for child in children:
                normalized = self._normalize_discovery_name(
                    str(child.get("name") or "")
                )
                if normalized and normalized not in child_by_name:
                    child_by_name[normalized] = child

            if not type_is_light:
                continue

            state_node = (
                child_by_name.get("state")
                or child_by_name.get("on")
                or child_by_name.get("power")
            )
            if not state_node:
                continue

            state_node_id = str(state_node.get("node_id") or "")
            if not state_node_id:
                continue

            state_writable = bool(state_node.get("is_writable", False))
            if not include_readonly and not state_writable:
                continue

            cfg: dict[str, Any] = {
                CONF_NODE_KIND: NODE_KIND_LIGHT,
                CONF_NODE_NAME: str(
                    item.get("name") or state_node.get("name") or state_node_id
                ),
                CONF_NODE_ID: state_node_id,
            }
            if device_contexts and node_id in device_contexts:
                cfg.update(device_contexts[node_id])

            def _pick(*names: str) -> str | None:
                for n in names:
                    child = child_by_name.get(n)
                    if child and str(child.get("node_id") or ""):
                        return str(child.get("node_id"))
                return None

            brightness_id = _pick("brightness", "dimmer", "level")
            if brightness_id:
                cfg[CONF_LIGHT_BRIGHTNESS_NODE_ID] = brightness_id

            color_temp_id = _pick("colortemp", "colortempkelvin", "colortemperature")
            if color_temp_id:
                cfg[CONF_LIGHT_COLOR_TEMP_NODE_ID] = color_temp_id

            hs_hue_id = _pick("hue", "h")
            hs_sat_id = _pick("saturation", "sat", "s")
            if hs_hue_id and hs_sat_id:
                cfg[CONF_LIGHT_HS_HUE_NODE_ID] = hs_hue_id
                cfg[CONF_LIGHT_HS_SAT_NODE_ID] = hs_sat_id

            rgb_r_id = _pick("r", "red")
            rgb_g_id = _pick("g", "green")
            rgb_b_id = _pick("b", "blue")
            if rgb_r_id and rgb_g_id and rgb_b_id:
                cfg[CONF_LIGHT_RGB_R_NODE_ID] = rgb_r_id
                cfg[CONF_LIGHT_RGB_G_NODE_ID] = rgb_g_id
                cfg[CONF_LIGHT_RGB_B_NODE_ID] = rgb_b_id

            rgbw_r_id = _pick("rgbw_r")
            rgbw_g_id = _pick("rgbw_g")
            rgbw_b_id = _pick("rgbw_b")
            rgbw_w_id = _pick("rgbw_w")
            if rgbw_r_id and rgbw_g_id and rgbw_b_id and rgbw_w_id:
                cfg[CONF_LIGHT_RGBW_R_NODE_ID] = rgbw_r_id
                cfg[CONF_LIGHT_RGBW_G_NODE_ID] = rgbw_g_id
                cfg[CONF_LIGHT_RGBW_B_NODE_ID] = rgbw_b_id
                cfg[CONF_LIGHT_RGBW_W_NODE_ID] = rgbw_w_id

            rgbww_r_id = _pick("rgbww_r")
            rgbww_g_id = _pick("rgbww_g")
            rgbww_b_id = _pick("rgbww_b")
            rgbww_cw_id = _pick("rgbww_cw")
            rgbww_ww_id = _pick("rgbww_ww")
            if rgbww_r_id and rgbww_g_id and rgbww_b_id and rgbww_cw_id and rgbww_ww_id:
                cfg[CONF_LIGHT_RGBWW_R_NODE_ID] = rgbww_r_id
                cfg[CONF_LIGHT_RGBWW_G_NODE_ID] = rgbww_g_id
                cfg[CONF_LIGHT_RGBWW_B_NODE_ID] = rgbww_b_id
                cfg[CONF_LIGHT_RGBWW_CW_NODE_ID] = rgbww_cw_id
                cfg[CONF_LIGHT_RGBWW_WW_NODE_ID] = rgbww_ww_id

            white_id = _pick("white")
            if white_id:
                cfg[CONF_LIGHT_WHITE_NODE_ID] = white_id

            xy_x_id = _pick("x")
            xy_y_id = _pick("y")
            if xy_x_id and xy_y_id:
                cfg[CONF_LIGHT_XY_X_NODE_ID] = xy_x_id
                cfg[CONF_LIGHT_XY_Y_NODE_ID] = xy_y_id

            effect_id = _pick("effect")
            if effect_id:
                cfg[CONF_LIGHT_EFFECT_NODE_ID] = effect_id

            transition_id = _pick("transition")
            if transition_id:
                cfg[CONF_LIGHT_TRANSITION_NODE_ID] = transition_id

            flash_id = _pick("flash")
            if flash_id:
                cfg[CONF_LIGHT_FLASH_NODE_ID] = flash_id

            discovered.append(cfg)

            consumed_ids.add(node_id)
            consumed_ids.add(state_node_id)
            for optional_id in [
                brightness_id,
                color_temp_id,
                hs_hue_id,
                hs_sat_id,
                rgb_r_id,
                rgb_g_id,
                rgb_b_id,
                rgbw_r_id,
                rgbw_g_id,
                rgbw_b_id,
                rgbw_w_id,
                rgbww_r_id,
                rgbww_g_id,
                rgbww_b_id,
                rgbww_cw_id,
                rgbww_ww_id,
                white_id,
                xy_x_id,
                xy_y_id,
                effect_id,
                transition_id,
                flash_id,
            ]:
                if optional_id:
                    consumed_ids.add(optional_id)

        return discovered, consumed_ids

    def _map_discovered_item(
        self,
        item: dict[str, Any],
        *,
        include_readonly: bool,
        device_contexts: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, Any] | None:
        if item.get("node_class") != "Variable":
            return None

        node_id = str(item.get("node_id", ""))
        if not node_id:
            return None

        def _with_device(cfg: dict[str, Any]) -> dict[str, Any]:
            if device_contexts and node_id in device_contexts:
                cfg.update(device_contexts[node_id])
            return cfg

        name = str(item.get("name") or node_id)
        path = str(item.get("path") or name)
        sample_type = str(item.get("sample_type", "")).lower()
        writable = bool(item.get("is_writable", False))

        if not include_readonly and not writable:
            return None

        if sample_type in ("bool", "boolean"):
            if writable:
                return _with_device(
                    {
                        CONF_NODE_KIND: NODE_KIND_SWITCH,
                        CONF_NODE_NAME: name,
                        CONF_NODE_ID: node_id,
                    }
                )

            cfg = {
                CONF_NODE_KIND: NODE_KIND_BINARY_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
            }
            device_class = self._guess_binary_sensor_class(name, path)
            if device_class:
                cfg[CONF_NODE_DEVICE_CLASS] = device_class
            return _with_device(cfg)

        if sample_type in (
            "int",
            "float",
            "int32",
            "int64",
            "uint16",
            "uint32",
            "uint64",
            "double",
        ):
            cfg = {
                CONF_NODE_KIND: NODE_KIND_SENSOR,
                CONF_NODE_NAME: name,
                CONF_NODE_ID: node_id,
            }
            unit = self._guess_unit(name, path, item.get("engineering_units"))
            if unit:
                cfg[CONF_NODE_UNIT] = unit
            device_class, state_class = self._guess_sensor_classes(name, path)
            if device_class:
                cfg[CONF_NODE_DEVICE_CLASS] = device_class
            if state_class:
                cfg[CONF_NODE_STATE_CLASS] = state_class
            return _with_device(cfg)

        if sample_type in ("str", "string"):
            return _with_device(
                {
                    CONF_NODE_KIND: NODE_KIND_SENSOR,
                    CONF_NODE_NAME: name,
                    CONF_NODE_ID: node_id,
                    CONF_NODE_ICON: "mdi:form-textbox",
                }
            )

        # Fallback for unknown but readable variables
        if sample_type:
            return _with_device(
                {
                    CONF_NODE_KIND: NODE_KIND_SENSOR,
                    CONF_NODE_NAME: name,
                    CONF_NODE_ID: node_id,
                }
            )

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

    async def async_step_add_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:gesture-tap-button"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_button", data_schema=schema)

    async def async_step_add_climate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_CLIMATE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_TARGET_NODE_ID: user_input.get(CONF_NODE_TARGET_NODE_ID)
                    or None,
                    CONF_CLIMATE_HVAC_MODE_NODE_ID: user_input.get(
                        CONF_CLIMATE_HVAC_MODE_NODE_ID
                    )
                    or None,
                    CONF_CLIMATE_MIN_TEMP: float(
                        user_input.get(CONF_CLIMATE_MIN_TEMP, DEFAULT_CLIMATE_MIN_TEMP)
                    ),
                    CONF_CLIMATE_MAX_TEMP: float(
                        user_input.get(CONF_CLIMATE_MAX_TEMP, DEFAULT_CLIMATE_MAX_TEMP)
                    ),
                    CONF_CLIMATE_TEMP_STEP: float(
                        user_input.get(
                            CONF_CLIMATE_TEMP_STEP, DEFAULT_CLIMATE_TEMP_STEP
                        )
                    ),
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
                vol.Required(
                    CONF_CLIMATE_MIN_TEMP, default=DEFAULT_CLIMATE_MIN_TEMP
                ): NumberSelector(
                    NumberSelectorConfig(min=-50, max=100, step=0.1, mode="box")
                ),
                vol.Required(
                    CONF_CLIMATE_MAX_TEMP, default=DEFAULT_CLIMATE_MAX_TEMP
                ): NumberSelector(
                    NumberSelectorConfig(min=-50, max=100, step=0.1, mode="box")
                ),
                vol.Required(
                    CONF_CLIMATE_TEMP_STEP, default=DEFAULT_CLIMATE_TEMP_STEP
                ): NumberSelector(
                    NumberSelectorConfig(min=0.1, max=5, step=0.1, mode="box")
                ),
                vol.Optional(CONF_NODE_ICON, default="mdi:thermostat"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_climate", data_schema=schema)

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_COVER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_TARGET_NODE_ID: user_input.get(CONF_NODE_TARGET_NODE_ID)
                    or None,
                    CONF_COVER_SET_POSITION_NODE_ID: user_input.get(
                        CONF_COVER_SET_POSITION_NODE_ID
                    )
                    or None,
                    CONF_COVER_OPEN_NODE_ID: user_input.get(CONF_COVER_OPEN_NODE_ID)
                    or None,
                    CONF_COVER_CLOSE_NODE_ID: user_input.get(CONF_COVER_CLOSE_NODE_ID)
                    or None,
                    CONF_COVER_STOP_NODE_ID: user_input.get(CONF_COVER_STOP_NODE_ID)
                    or None,
                    CONF_COVER_INVERT_POSITION: bool(
                        user_input.get(CONF_COVER_INVERT_POSITION, False)
                    ),
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
                vol.Required(
                    CONF_COVER_INVERT_POSITION, default=False
                ): BooleanSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:blinds"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_cover", data_schema=schema)

    async def async_step_add_valve(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_VALVE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NODE_TARGET_NODE_ID: user_input.get(CONF_NODE_TARGET_NODE_ID)
                    or None,
                    CONF_VALVE_SET_POSITION_NODE_ID: user_input.get(
                        CONF_VALVE_SET_POSITION_NODE_ID
                    )
                    or None,
                    CONF_VALVE_OPEN_NODE_ID: user_input.get(CONF_VALVE_OPEN_NODE_ID)
                    or None,
                    CONF_VALVE_CLOSE_NODE_ID: user_input.get(CONF_VALVE_CLOSE_NODE_ID)
                    or None,
                    CONF_VALVE_STOP_NODE_ID: user_input.get(CONF_VALVE_STOP_NODE_ID)
                    or None,
                    CONF_VALVE_INVERT_POSITION: bool(
                        user_input.get(CONF_VALVE_INVERT_POSITION, False)
                    ),
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
                vol.Optional(CONF_VALVE_SET_POSITION_NODE_ID): TextSelector(),
                vol.Optional(CONF_VALVE_OPEN_NODE_ID): TextSelector(),
                vol.Optional(CONF_VALVE_CLOSE_NODE_ID): TextSelector(),
                vol.Optional(CONF_VALVE_STOP_NODE_ID): TextSelector(),
                vol.Required(
                    CONF_VALVE_INVERT_POSITION, default=False
                ): BooleanSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:valve"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_valve", data_schema=schema)

    async def async_step_add_date(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_add_datetime(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:calendar-clock"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_datetime", data_schema=schema)

    async def async_step_add_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_FAN,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_FAN_SPEED_NODE_ID: user_input.get(CONF_FAN_SPEED_NODE_ID)
                    or None,
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

    async def async_step_add_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_NOTIFY,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NOTIFY_MESSAGE_NODE_ID: user_input.get(
                        CONF_NOTIFY_MESSAGE_NODE_ID
                    )
                    or None,
                    CONF_NOTIFY_TITLE_NODE_ID: user_input.get(CONF_NOTIFY_TITLE_NODE_ID)
                    or None,
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:message-alert"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_notify", data_schema=schema)

    async def async_step_add_number(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_NUMBER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_NUMBER_MIN: float(
                        user_input.get(CONF_NUMBER_MIN, DEFAULT_NUMBER_MIN)
                    ),
                    CONF_NUMBER_MAX: float(
                        user_input.get(CONF_NUMBER_MAX, DEFAULT_NUMBER_MAX)
                    ),
                    CONF_NUMBER_STEP: float(
                        user_input.get(CONF_NUMBER_STEP, DEFAULT_NUMBER_STEP)
                    ),
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
                vol.Required(
                    CONF_NUMBER_MIN, default=DEFAULT_NUMBER_MIN
                ): NumberSelector(
                    NumberSelectorConfig(min=-100000, max=100000, step=0.1, mode="box")
                ),
                vol.Required(
                    CONF_NUMBER_MAX, default=DEFAULT_NUMBER_MAX
                ): NumberSelector(
                    NumberSelectorConfig(min=-100000, max=100000, step=0.1, mode="box")
                ),
                vol.Required(
                    CONF_NUMBER_STEP, default=DEFAULT_NUMBER_STEP
                ): NumberSelector(
                    NumberSelectorConfig(min=0.001, max=10000, step=0.001, mode="box")
                ),
                vol.Optional(CONF_NODE_UNIT): TextSelector(),
                vol.Optional(CONF_NODE_ICON, default="mdi:numeric"): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_number", data_schema=schema)

    async def async_step_add_scene(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            activate_value = self._parse_scalar_value(
                user_input.get(CONF_SCENE_ACTIVATE_VALUE)
            )
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_SCENE,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_SCENE_ACTIVATE_VALUE: True
                    if activate_value is None
                    else activate_value,
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

    async def async_step_add_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_add_text(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:form-textbox"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_text", data_schema=schema)

    async def async_step_add_time(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:clock-outline"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_time", data_schema=schema)

    async def async_step_add_weather(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._options[CONF_NODES].append(
                {
                    CONF_NODE_KIND: NODE_KIND_WEATHER,
                    CONF_NODE_NAME: user_input[CONF_NODE_NAME],
                    CONF_NODE_ID: user_input[CONF_NODE_ID],
                    CONF_WEATHER_HUMIDITY_NODE_ID: user_input.get(
                        CONF_WEATHER_HUMIDITY_NODE_ID
                    )
                    or None,
                    CONF_WEATHER_PRESSURE_NODE_ID: user_input.get(
                        CONF_WEATHER_PRESSURE_NODE_ID
                    )
                    or None,
                    CONF_WEATHER_WIND_SPEED_NODE_ID: user_input.get(
                        CONF_WEATHER_WIND_SPEED_NODE_ID
                    )
                    or None,
                    CONF_WEATHER_CONDITION_NODE_ID: user_input.get(
                        CONF_WEATHER_CONDITION_NODE_ID
                    )
                    or None,
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
                vol.Optional(
                    CONF_NODE_ICON, default="mdi:weather-partly-cloudy"
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="add_weather", data_schema=schema)

    async def async_step_auto_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            root_node_id = str(user_input.get("root_node_id", "i=85")).strip() or "i=85"
            # No hard limits for discovery scan; traverse from root until tree is exhausted.
            depth = None
            max_nodes = None
            import_limit = None
            include_readonly = bool(user_input.get("include_readonly", True))
            include_standard_nodes = bool(
                user_input.get("include_standard_nodes", False)
            )

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
                _LOGGER.warning(
                    "Auto discovery browse failed on %s: %s",
                    self._entry.data[CONF_ENDPOINT],
                    err,
                )
                errors["base"] = "cannot_connect"
                browsed = []
            finally:
                await manager.disconnect()

            if not errors:
                device_contexts = self._extract_device_contexts(browsed)

                light_candidates, consumed_node_ids = self._discover_light_object_nodes(
                    browsed,
                    include_readonly=include_readonly,
                    device_contexts=device_contexts,
                )

                candidates: list[dict[str, Any]] = list(light_candidates)
                for item in browsed:
                    node_id = str(item.get("node_id", ""))
                    if not node_id or node_id in consumed_node_ids:
                        continue
                    if not include_standard_nodes and node_id.startswith("i="):
                        continue

                    cfg = self._map_discovered_item(
                        item,
                        include_readonly=include_readonly,
                        device_contexts=device_contexts,
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

                self._discovery_cache = (
                    deduped if import_limit is None else deduped[:import_limit]
                )
                return await self.async_step_auto_discovery_review()

        schema = vol.Schema(
            {
                vol.Optional("root_node_id", default="i=85"): TextSelector(),
                vol.Optional("include_readonly", default=True): BooleanSelector(),
                vol.Optional(
                    "include_standard_nodes", default=False
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="auto_discovery", data_schema=schema, errors=errors
        )

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
        sensors = len(
            [
                n
                for n in self._discovery_cache
                if n.get(CONF_NODE_KIND) == NODE_KIND_SENSOR
            ]
        )
        binary = len(
            [
                n
                for n in self._discovery_cache
                if n.get(CONF_NODE_KIND) == NODE_KIND_BINARY_SENSOR
            ]
        )
        switches = len(
            [
                n
                for n in self._discovery_cache
                if n.get(CONF_NODE_KIND) == NODE_KIND_SWITCH
            ]
        )
        lights = len(
            [
                n
                for n in self._discovery_cache
                if n.get(CONF_NODE_KIND) == NODE_KIND_LIGHT
            ]
        )

        sample = (
            ", ".join(
                [str(n.get(CONF_NODE_NAME, "")) for n in self._discovery_cache[:5]]
            )
            or "-"
        )

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
                    self._server_discovery_cache = (
                        await OpcUaClientManager.discover_servers(
                            discovery_url,
                            include_network=include_network,
                        )
                    )
                except Exception as err:
                    _LOGGER.warning(
                        "Server discovery failed for %s: %s", discovery_url, err
                    )
                    errors["base"] = "cannot_connect"

                if not errors and not self._server_discovery_cache:
                    errors["base"] = "no_servers_found"

                if not errors:
                    return await self.async_step_discover_servers_select()

        schema = vol.Schema(
            {
                vol.Required(
                    "discovery_url",
                    default=str(
                        self._entry.data.get(CONF_ENDPOINT, "opc.tcp://127.0.0.1:4840")
                    ),
                ): TextSelector(),
                vol.Required("include_network", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="discover_servers", data_schema=schema, errors=errors
        )

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
                (
                    "Basic256Sha256",
                    "SignAndEncrypt",
                ): SECURITY_POLICY_BASIC256SHA256_SIGN_ENCRYPT,
            }
            mapped_policy = policy_map.get((policy_short, mode))

            if mapped_policy is None:
                return self.async_show_form(
                    step_id="discover_servers_select",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                "selected", default=selected_key
                            ): SelectSelector(
                                SelectSelectorConfig(
                                    options=options,
                                    multiple=False,
                                    mode=SelectSelectorMode.DROPDOWN,
                                )
                            )
                        }
                    ),
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
        return self.async_show_form(
            step_id="discover_servers_select", data_schema=schema
        )

    async def async_step_browse_nodes(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            root_node_id = str(user_input.get("root_node_id", "i=85")).strip() or "i=85"
            # No hard limits for browse scan; traverse from root until tree is exhausted.
            depth = None
            max_nodes = None

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
                _LOGGER.warning(
                    "Browse failed on %s: %s", self._entry.data[CONF_ENDPOINT], err
                )
                errors["base"] = "cannot_connect"
            finally:
                await manager.disconnect()

            if not errors:
                return await self.async_step_browse_pick_kind()

        schema = vol.Schema(
            {
                vol.Optional("root_node_id", default="i=85"): TextSelector(),
            }
        )
        placeholders = None
        if self._browse_cache and self._browse_current_parent:
            branch = [
                item
                for item in self._browse_cache
                if str(item.get("parent_node_id")) == str(self._browse_current_parent)
            ]
            folders = sum(1 for item in branch if str(item.get("node_class")) == "Object")
            variables = sum(1 for item in branch if str(item.get("node_class")) == "Variable")
            other = max(0, len(branch) - folders - variables)
            placeholders = {
                "current": str(self._browse_current_parent),
                "folders": str(folders),
                "variables": str(variables),
                "other": str(other),
            }
        return self.async_show_form(
            step_id="browse_nodes",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

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
                "browse_add_valve",
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

    def _browse_indexes(
        self,
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
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
                    str(parent_item.get("parent_node_id", ""))
                    if parent_item
                    else self._browse_root_node_id
                )
                self._browse_current_parent = (
                    parent_of_parent or self._browse_root_node_id
                )

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
                branch_options.append(
                    {
                        "value": child_id,
                        "label": f"📁 {self._label_for_browse_item(item)}",
                    }
                )

            if node_class == "Variable":
                import_options.append(
                    {
                        "value": child_id,
                        "label": f"🧩 {self._label_for_browse_item(item)}",
                    }
                )

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
        current_path = (
            current_item.get("path") if current_item else self._browse_root_node_id
        )

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
        return await self._browse_add_nodes_by_kind(
            "browse_add_sensor", NODE_KIND_SENSOR, user_input
        )

    async def async_step_browse_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_binary_sensor", NODE_KIND_BINARY_SENSOR, user_input
        )

    async def async_step_browse_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_switch", NODE_KIND_SWITCH, user_input
        )

    async def async_step_browse_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_light", NODE_KIND_LIGHT, user_input
        )

    async def async_step_browse_add_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_button", NODE_KIND_BUTTON, user_input
        )

    async def async_step_browse_add_climate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_climate", NODE_KIND_CLIMATE, user_input
        )

    async def async_step_browse_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_cover", NODE_KIND_COVER, user_input
        )

    async def async_step_browse_add_date(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_date", NODE_KIND_DATE, user_input
        )

    async def async_step_browse_add_datetime(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_datetime", NODE_KIND_DATETIME, user_input
        )

    async def async_step_browse_add_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_fan", NODE_KIND_FAN, user_input
        )

    async def async_step_browse_add_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_notify", NODE_KIND_NOTIFY, user_input
        )

    async def async_step_browse_add_number(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_number", NODE_KIND_NUMBER, user_input
        )

    async def async_step_browse_add_scene(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_scene", NODE_KIND_SCENE, user_input
        )

    async def async_step_browse_add_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_select", NODE_KIND_SELECT, user_input
        )

    async def async_step_browse_add_text(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_text", NODE_KIND_TEXT, user_input
        )

    async def async_step_browse_add_time(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_time", NODE_KIND_TIME, user_input
        )

    async def async_step_browse_add_weather(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._browse_add_nodes_by_kind(
            "browse_add_weather", NODE_KIND_WEATHER, user_input
        )

    async def async_step_remove_node(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        nodes = self._options.get(CONF_NODES, [])
        if not nodes:
            return await self.async_step_init()

        if user_input is not None:
            selected_raw = user_input.get("remove", [])
            if isinstance(selected_raw, str):
                selected = {selected_raw}
            else:
                selected = {str(v) for v in selected_raw}

            self._options[CONF_NODES] = [
                node for idx, node in enumerate(nodes) if str(idx) not in selected
            ]
            await self._persist_options()
            return await self.async_step_init()

        options = {
            str(
                idx
            ): f"{node.get(CONF_NODE_NAME)} ({node.get(CONF_NODE_KIND)} | {node.get(CONF_NODE_ID)})"
            for idx, node in enumerate(nodes)
        }
        schema = vol.Schema(
            {
                vol.Required("remove"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": key, "label": label}
                            for key, label in options.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="remove_node", data_schema=schema)

