from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_NODE_DEVICE_CLASS,
    CONF_NODE_INVERT,
    NODE_KIND_BINARY_SENSOR,
)
from .entity import OpcUaBaseEntity


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
        OpcUaBinarySensor(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_BINARY_SENSOR)
    ]
    async_add_entities(entities)


class OpcUaBinarySensor(OpcUaBaseEntity, BinarySensorEntity):
    """OPC UA Binary Sensor entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(
            entry_id, endpoint, node_cfg, coordinator, NODE_KIND_BINARY_SENSOR
        )
        self._attr_device_class = node_cfg.get(CONF_NODE_DEVICE_CLASS)
        self._invert = bool(node_cfg.get(CONF_NODE_INVERT, False))

    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value()
        if raw is None:
            return None
        state = bool(raw)
        return (not state) if self._invert else state
