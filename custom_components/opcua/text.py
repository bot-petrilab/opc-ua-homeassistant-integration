from __future__ import annotations

from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, CONF_TEXT_MAX, NODE_KIND_TEXT
from .entity import OpcUaBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaText(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_TEXT)
    ]
    async_add_entities(entities)


class OpcUaText(OpcUaBaseEntity, TextEntity):
    """OPC-UA text entity."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_TEXT)
        self._attr_native_max = int(node_cfg.get(CONF_TEXT_MAX, 255))

    @property
    def native_value(self) -> str | None:
        raw = self._raw_value()
        if raw is None:
            return None
        return str(raw)

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.manager.write_node(self._node_id, value)
        await self.coordinator.async_request_refresh()
