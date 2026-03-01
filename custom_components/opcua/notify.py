from __future__ import annotations

from typing import Any

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_NOTIFY_MESSAGE_NODE_ID,
    CONF_NOTIFY_TITLE_NODE_ID,
    NODE_KIND_NOTIFY,
)
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
        OpcUaNotifyEntity(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_NOTIFY)
    ]
    async_add_entities(entities)


class OpcUaNotifyEntity(OpcUaBaseEntity, NotifyEntity):
    """OPC-UA notify entity (writes title/message to configured nodes)."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_NOTIFY)
        self._cfg = node_cfg

    async def async_send_message(self, message: str = "", title: str | None = None, **kwargs: Any) -> None:
        message_node_id = self._cfg.get(CONF_NOTIFY_MESSAGE_NODE_ID) or self._node_id
        title_node_id = self._cfg.get(CONF_NOTIFY_TITLE_NODE_ID)

        if title is not None and title_node_id:
            await self.coordinator.manager.write_node(title_node_id, str(title))
        await self.coordinator.manager.write_node(message_node_id, str(message))
        await self.coordinator.async_request_refresh()
