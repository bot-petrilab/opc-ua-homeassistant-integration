from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_NODE_DEVICE_CLASS,
    CONF_NODE_STATE_CLASS,
    CONF_NODE_UNIT,
    NODE_KIND_SENSOR,
)
from .entity import OpcUaBaseEntity


def _to_float_if_possible(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


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
        OpcUaSensor(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_SENSOR)
    ]
    async_add_entities(entities)


class OpcUaSensor(OpcUaBaseEntity, SensorEntity):
    """OPC UA Sensor entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_SENSOR)
        self._attr_native_unit_of_measurement = node_cfg.get(CONF_NODE_UNIT)
        self._attr_device_class = node_cfg.get(CONF_NODE_DEVICE_CLASS)
        self._attr_state_class = node_cfg.get(CONF_NODE_STATE_CLASS)

    @property
    def native_value(self):
        return _to_float_if_possible(self._raw_value())
