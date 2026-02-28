from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_ENDPOINT,
    CONF_NODES,
    CONF_SCAN_INTERVAL,
    CONF_SECURITY_POLICY,
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
    """Set up OPC UA Machine from YAML (not used, config-entry only)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> bool:
    """Set up OPC UA Machine from a config entry."""
    endpoint: str = entry.data[CONF_ENDPOINT]
    security_policy: str = entry.data[CONF_SECURITY_POLICY]
    username: str | None = entry.data.get(CONF_USERNAME)
    password: str | None = entry.data.get(CONF_PASSWORD)

    scan_interval: int = int(
        entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS))
    )
    nodes: list[dict] = entry.options.get(CONF_NODES, entry.data.get(CONF_NODES, []))

    manager = OpcUaClientManager(
        endpoint=endpoint,
        security_policy=security_policy,
        username=username,
        password=password,
    )

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=nodes,
        scan_interval_seconds=scan_interval,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        await manager.disconnect()
        raise ConfigEntryNotReady(f"Unable to connect to OPC UA endpoint {endpoint}: {err}") from err

    entry.runtime_data = OpcUaRuntimeData(manager=manager, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("OPC UA Machine loaded for endpoint %s", endpoint)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> bool:
    """Unload OPC UA Machine config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    runtime = entry.runtime_data
    await runtime.manager.disconnect()

    if unload_ok:
        _LOGGER.info("OPC UA Machine unloaded for endpoint %s", entry.data.get(CONF_ENDPOINT))

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: OpcUaConfigEntry) -> None:
    """Reload when config entry options change."""
    await hass.config_entries.async_reload(entry.entry_id)
