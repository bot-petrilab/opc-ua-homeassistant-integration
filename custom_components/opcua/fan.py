from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, CONF_FAN_SPEED_NODE_ID, CONF_NODE_INVERT, NODE_KIND_FAN
from .entity import OpcUaBaseEntity


def _as_int(value: Any) -> int | None:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
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
        OpcUaFan(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_FAN)
    ]
    async_add_entities(entities)


class OpcUaFan(OpcUaBaseEntity, FanEntity):
    """OPC-UA fan entity."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_FAN)
        self._cfg = node_cfg
        self._invert = bool(node_cfg.get(CONF_NODE_INVERT, False))
        self._speed_node_id = node_cfg.get(CONF_FAN_SPEED_NODE_ID)
        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._speed_node_id:
            features |= FanEntityFeature.SET_SPEED
        self._attr_supported_features = features

    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value()
        if raw is None:
            return None
        state = bool(raw)
        return (not state) if self._invert else state

    @property
    def percentage(self) -> int | None:
        if not self._speed_node_id:
            return None
        raw = self.coordinator.data.get(self._speed_node_id)
        value = _as_int(raw)
        if value is None:
            return None
        return max(0, min(100, value))

    async def async_turn_on(self, percentage: int | None = None, **kwargs: Any) -> None:
        await self.coordinator.manager.write_node(self._node_id, False if self._invert else True)
        if percentage is not None and self._speed_node_id:
            await self.coordinator.manager.write_node(self._speed_node_id, int(max(0, min(100, percentage))))
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.manager.write_node(self._node_id, True if self._invert else False)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        if not self._speed_node_id:
            return
        await self.coordinator.manager.write_node(self._speed_node_id, int(max(0, min(100, percentage))))
        await self.coordinator.async_request_refresh()
