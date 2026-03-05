from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_CLIENT_KEY_PATH,
    CONF_ENDPOINT,
    CONF_NODES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TITLE_PREFIX,
    CONF_POLL_FAST_INTERVAL,
    CONF_POLL_NORMAL_INTERVAL,
    CONF_POLL_SLOW_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_SECURITY_POLICY,
    CONF_SERVER_CERT_PATH,
    DEFAULT_NOTIFY_ENABLED,
    DEFAULT_NOTIFY_KEYWORDS,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_TITLE_PREFIX,
    DEFAULT_POLL_FAST_INTERVAL_SECONDS,
    DEFAULT_POLL_NORMAL_INTERVAL_SECONDS,
    DEFAULT_POLL_SLOW_INTERVAL_SECONDS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import OpcUaCoordinator
from .opcua_client import OpcUaClientManager

_LOGGER = logging.getLogger(__name__)


@dataclass
class OpcUaRuntimeData:
    manager: OpcUaClientManager
    coordinator: OpcUaCoordinator


OpcUaConfigEntry = ConfigEntry[OpcUaRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up OPC-UA from YAML (not used, config-entry only)."""
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

    scan_interval: int = int(
        entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS))
    )
    nodes: list[dict] = entry.options.get(CONF_NODES, entry.data.get(CONF_NODES, []))

    poll_intervals = {
        "fast": int(entry.options.get(CONF_POLL_FAST_INTERVAL, DEFAULT_POLL_FAST_INTERVAL_SECONDS)),
        "normal": int(entry.options.get(CONF_POLL_NORMAL_INTERVAL, DEFAULT_POLL_NORMAL_INTERVAL_SECONDS)),
        "slow": int(entry.options.get(CONF_POLL_SLOW_INTERVAL, DEFAULT_POLL_SLOW_INTERVAL_SECONDS)),
    }

    notify_enabled = bool(entry.options.get(CONF_NOTIFY_ENABLED, entry.data.get(CONF_NOTIFY_ENABLED, DEFAULT_NOTIFY_ENABLED)))
    notify_service = str(entry.options.get(CONF_NOTIFY_SERVICE, entry.data.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)))
    notify_title_prefix = str(
        entry.options.get(CONF_NOTIFY_TITLE_PREFIX, entry.data.get(CONF_NOTIFY_TITLE_PREFIX, DEFAULT_NOTIFY_TITLE_PREFIX))
    )
    notify_keywords = entry.options.get(CONF_NOTIFY_KEYWORDS, entry.data.get(CONF_NOTIFY_KEYWORDS, list(DEFAULT_NOTIFY_KEYWORDS)))
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
        scan_interval_seconds=scan_interval,
        poll_intervals=poll_intervals,
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
        raise ConfigEntryNotReady(f"Unable to connect to OPC UA endpoint {endpoint}: {err}") from err

    entry.runtime_data = OpcUaRuntimeData(manager=manager, coordinator=coordinator)

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
        _LOGGER.info("OPC-UA unloaded for endpoint %s", entry.data.get(CONF_ENDPOINT))

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> None:
    """Reload when config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)
