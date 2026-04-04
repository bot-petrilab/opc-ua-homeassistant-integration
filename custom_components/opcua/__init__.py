from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import (
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_CLIENT_KEY_PATH,
    CONF_ENDPOINT,
    CONF_NODE_ID,
    CONF_NODE_KIND,
    CONF_NODE_NAME,
    CONF_NODES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TITLE_PREFIX,
    CONF_SECURITY_POLICY,
    CONF_SERVER_CERT_PATH,
    DEFAULT_NOTIFY_ENABLED,
    DEFAULT_NOTIFY_KEYWORDS,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_TITLE_PREFIX,
    DEFAULT_SECURITY_POLICY,
    DOMAIN,
    PLATFORMS,
    SECURITY_POLICIES,
    SECURITY_POLICY_NONE,
)
from .coordinator import OpcUaCoordinator
from .opcua_client import OpcUaClientManager
from .repairs import async_delete_repairs, async_sync_repairs

_LOGGER = logging.getLogger(__name__)

_NODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NODE_ID): str,
        vol.Required(CONF_NODE_NAME): str,
        vol.Required(CONF_NODE_KIND): str,
    },
    extra=vol.ALLOW_EXTRA,
)

_YAML_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENDPOINT): str,
        vol.Optional(CONF_SECURITY_POLICY, default=DEFAULT_SECURITY_POLICY): vol.In(
            SECURITY_POLICIES
        ),
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
        vol.Optional(CONF_CLIENT_CERT_PATH): str,
        vol.Optional(CONF_CLIENT_KEY_PATH): str,
        vol.Optional(CONF_SERVER_CERT_PATH): str,
        vol.Optional(CONF_CLIENT_KEY_PASSWORD): str,
        vol.Optional(CONF_NOTIFY_ENABLED, default=DEFAULT_NOTIFY_ENABLED): bool,
        vol.Optional(CONF_NOTIFY_SERVICE, default=DEFAULT_NOTIFY_SERVICE): str,
        vol.Optional(
            CONF_NOTIFY_TITLE_PREFIX, default=DEFAULT_NOTIFY_TITLE_PREFIX
        ): str,
        vol.Optional(CONF_NOTIFY_KEYWORDS, default=list(DEFAULT_NOTIFY_KEYWORDS)): vol.Any(
            str, [str]
        ),
        vol.Optional(CONF_NODES, default=[]): [_NODE_SCHEMA],
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(lambda value: value if isinstance(value, list) else [value], [_YAML_ENTRY_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


def _is_auth_error(err: Exception) -> bool:
    text = str(err).lower()
    auth_markers = (
        "badidentitytoken",
        "baduseraccessdenied",
        "badsecuritychecksfailed",
        "user identity",
        "authentication",
        "access denied",
    )
    return any(marker in text for marker in auth_markers)


@dataclass
class OpcUaRuntimeData:
    manager: OpcUaClientManager
    coordinator: OpcUaCoordinator


OpcUaConfigEntry = ConfigEntry[OpcUaRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up OPC-UA from YAML imports and config entries."""
    for yaml_entry in config.get(DOMAIN, []):
        import_data: dict[str, Any] = dict(yaml_entry)
        if import_data.get(CONF_SECURITY_POLICY) == SECURITY_POLICY_NONE:
            import_data.pop(CONF_USERNAME, None)
            import_data.pop(CONF_PASSWORD, None)
            import_data.pop(CONF_CLIENT_CERT_PATH, None)
            import_data.pop(CONF_CLIENT_KEY_PATH, None)
            import_data.pop(CONF_SERVER_CERT_PATH, None)
            import_data.pop(CONF_CLIENT_KEY_PASSWORD, None)
        keywords = import_data.get(CONF_NOTIFY_KEYWORDS, list(DEFAULT_NOTIFY_KEYWORDS))
        if isinstance(keywords, str):
            import_data[CONF_NOTIFY_KEYWORDS] = [
                key.strip().lower() for key in keywords.split(",") if key.strip()
            ] or list(DEFAULT_NOTIFY_KEYWORDS)
        else:
            import_data[CONF_NOTIFY_KEYWORDS] = [
                str(key).strip().lower()
                for key in keywords
                if str(key).strip()
            ] or list(DEFAULT_NOTIFY_KEYWORDS)
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=import_data,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> bool:
    """Set up OPC-UA from a config entry."""
    endpoint: str = entry.data[CONF_ENDPOINT]
    security_policy: str = entry.data[CONF_SECURITY_POLICY]
    username: str | None = entry.data.get(CONF_USERNAME)
    password: str | None = entry.data.get(CONF_PASSWORD)
    client_cert_path: str | None = entry.data.get(CONF_CLIENT_CERT_PATH)
    client_key_path: str | None = entry.data.get(CONF_CLIENT_KEY_PATH)
    server_cert_path: str | None = entry.data.get(CONF_SERVER_CERT_PATH)
    client_key_password: str | None = entry.data.get(CONF_CLIENT_KEY_PASSWORD)

    nodes: list[dict] = entry.options.get(CONF_NODES, entry.data.get(CONF_NODES, []))


    notify_enabled = bool(
        entry.options.get(
            CONF_NOTIFY_ENABLED,
            entry.data.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED),
        )
    )
    notify_service = str(
        entry.options.get(
            CONF_NOTIFY_SERVICE,
            entry.data.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
        )
    )
    notify_title_prefix = str(
        entry.options.get(
            CONF_NOTIFY_TITLE_PREFIX,
            entry.data.get(CONF_NOTIFY_TITLE_PREFIX, DEFAULT_NOTIFY_TITLE_PREFIX),
        )
    )
    notify_keywords = entry.options.get(
        CONF_NOTIFY_KEYWORDS,
        entry.data.get(CONF_NOTIFY_KEYWORDS, list(DEFAULT_NOTIFY_KEYWORDS)),
    )
    if not isinstance(notify_keywords, list):
        notify_keywords = list(DEFAULT_NOTIFY_KEYWORDS)

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

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=nodes,
        entry_id=entry.entry_id,
        endpoint=endpoint,
        notify_enabled=notify_enabled,
        notify_service=notify_service,
        notify_title_prefix=notify_title_prefix,
        notify_keywords=[str(k).lower() for k in notify_keywords if str(k).strip()],
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        await manager.disconnect()
        if _is_auth_error(err):
            raise ConfigEntryAuthFailed(
                f"Authentication/security failed for OPC UA endpoint {endpoint}: {err}"
            ) from err
        raise ConfigEntryNotReady(
            f"Unable to connect to OPC UA endpoint {endpoint}: {err}"
        ) from err

    entry.runtime_data = OpcUaRuntimeData(manager=manager, coordinator=coordinator)
    async_sync_repairs(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("OPC-UA loaded for endpoint %s", endpoint)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> bool:
    """Unload OPC-UA config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    runtime = entry.runtime_data
    await runtime.manager.disconnect()

    if unload_ok:
        async_delete_repairs(hass, entry)
        _LOGGER.info("OPC-UA unloaded for endpoint %s", entry.data.get(CONF_ENDPOINT))

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> None:
    """Reload when config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)
