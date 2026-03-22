from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, CONF_SCENE_ACTIVATE_VALUE, NODE_KIND_SCENE
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
        OpcUaScene(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_SCENE)
    ]
    async_add_entities(entities)


class OpcUaScene(OpcUaBaseEntity, Scene):
    """OPC-UA scene entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_SCENE)
        self._activate_value = node_cfg.get(CONF_SCENE_ACTIVATE_VALUE, True)

    async def async_activate(self, **kwargs: Any) -> None:
        await self.coordinator.manager.write_node(self._node_id, self._activate_value)
        await self.coordinator.async_request_refresh()
