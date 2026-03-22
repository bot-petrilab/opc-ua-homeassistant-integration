from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_NODES

REDACT_KEYS = {
    "password",
    "client_key_password",
    "username",
}


def _redact_obj(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in REDACT_KEYS:
                out[k] = "REDACTED"
            else:
                out[k] = _redact_obj(v)
        return out
    if isinstance(value, list):
        return [_redact_obj(v) for v in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = _redact_obj(dict(entry.data))
    options = _redact_obj(dict(entry.options))

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
