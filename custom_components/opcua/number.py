from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_NUMBER_MAX,
    CONF_NUMBER_MIN,
    CONF_NUMBER_STEP,
    DEFAULT_NUMBER_MAX,
    DEFAULT_NUMBER_MIN,
    DEFAULT_NUMBER_STEP,
    NODE_KIND_NUMBER,
)
from .entity import OpcUaBaseEntity


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
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
        OpcUaNumber(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_NUMBER)
    ]
    async_add_entities(entities)


class OpcUaNumber(OpcUaBaseEntity, NumberEntity):
    """OPC-UA number entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_NUMBER)
        self._attr_native_min_value = float(
            node_cfg.get(CONF_NUMBER_MIN, DEFAULT_NUMBER_MIN)
        )
        self._attr_native_max_value = float(
            node_cfg.get(CONF_NUMBER_MAX, DEFAULT_NUMBER_MAX)
        )
        self._attr_native_step = float(
            node_cfg.get(CONF_NUMBER_STEP, DEFAULT_NUMBER_STEP)
        )

    @property
    def native_value(self) -> float | None:
        return _to_float(self._raw_value())

    async def async_set_native_value(self, value: float) -> None:
        current = self._raw_value()
        if isinstance(current, bool):
            payload = bool(value)
        elif isinstance(current, int):
            payload = int(round(value))
        elif isinstance(current, float):
            payload = float(value)
        else:
            payload = float(value)
        await self.coordinator.manager.write_node(self._node_id, payload)
        await self.coordinator.async_request_refresh()
