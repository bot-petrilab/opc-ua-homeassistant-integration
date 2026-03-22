from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_BUTTON_PAYLOAD, CONF_ENDPOINT, NODE_KIND_BUTTON
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
        OpcUaButton(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_BUTTON)
    ]
    async_add_entities(entities)


class OpcUaButton(OpcUaBaseEntity, ButtonEntity):
    """OPC-UA button entity (writes a configured payload on press)."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_BUTTON)
        self._payload = node_cfg.get(CONF_BUTTON_PAYLOAD, True)

    async def async_press(self) -> None:
        await self.coordinator.manager.write_node(self._node_id, self._payload)
        await self.coordinator.async_request_refresh()
