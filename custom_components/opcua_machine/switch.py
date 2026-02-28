from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, CONF_NODE_INVERT, NODE_KIND_SWITCH
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
        OpcUaSwitch(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_SWITCH)
    ]
    async_add_entities(entities)


class OpcUaSwitch(OpcUaBaseEntity, SwitchEntity):
    """OPC UA Switch entity (read + write bool)."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_SWITCH)
        self._invert = bool(node_cfg.get(CONF_NODE_INVERT, False))

    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value()
        if raw is None:
            return None
        state = bool(raw)
        return (not state) if self._invert else state

    async def async_turn_on(self, **kwargs: Any) -> None:
        raw_target = False if self._invert else True
        await self.coordinator.manager.write_node(self._node_id, raw_target)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        raw_target = True if self._invert else False
        await self.coordinator.manager.write_node(self._node_id, raw_target)
        await self.coordinator.async_request_refresh()
