from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, NODE_KIND_DATETIME
from .entity import OpcUaBaseEntity


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaDateTime(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_DATETIME)
    ]
    async_add_entities(entities)


class OpcUaDateTime(OpcUaBaseEntity, DateTimeEntity):
    """OPC-UA datetime entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_DATETIME)

    @property
    def native_value(self) -> datetime | None:
        return _as_datetime(self._raw_value())

    async def async_set_value(self, value: datetime) -> None:
        current = self._raw_value()
        if isinstance(current, datetime):
            payload = value
        else:
            payload = value.isoformat()
        await self.coordinator.manager.write_node(self._node_id, payload)
        await self.coordinator.async_request_refresh()
