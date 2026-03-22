from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_NODES

REDACT_KEYS = {
    "password",
    "client_key_password",
    "username",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = async_redact_data(dict(entry.data), REDACT_KEYS)
    options = async_redact_data(dict(entry.options), REDACT_KEYS)

    # Keep node counts visible while avoiding accidental sensitive payload leakage.
    node_count = len(options.get(CONF_NODES, []) or data.get(CONF_NODES, []))

    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "state": str(getattr(entry, "state", "unknown")),
        "data": data,
        "options": options,
        "node_count": node_count,
    }
