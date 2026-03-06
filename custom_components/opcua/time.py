from __future__ import annotations

from datetime import datetime, time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, NODE_KIND_TIME
from .entity import OpcUaBaseEntity


def _as_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except Exception:
            # try datetime and cut time part
            try:
                return datetime.fromisoformat(value).time()
            except Exception:
                return None
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaTime(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_TIME)
    ]
    async_add_entities(entities)


class OpcUaTime(OpcUaBaseEntity, TimeEntity):
    """OPC-UA time entity."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_TIME)

    @property
    def native_value(self) -> time | None:
        return _as_time(self._raw_value())

    async def async_set_value(self, value: time) -> None:
        current = self._raw_value()
        if isinstance(current, datetime):
            payload = datetime.combine(current.date(), value.replace(microsecond=0))
        elif isinstance(current, time):
            payload = value.replace(microsecond=0)
        else:
            payload = value.replace(microsecond=0).isoformat()
        await self.coordinator.manager.write_node(self._node_id, payload)
        await self.coordinator.async_request_refresh()
