from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENDPOINT, CONF_SELECT_OPTIONS, NODE_KIND_SELECT
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
        OpcUaSelect(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_SELECT)
    ]
    async_add_entities(entities)


class OpcUaSelect(OpcUaBaseEntity, SelectEntity):
    """OPC-UA select entity."""

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_SELECT)
        options_raw = node_cfg.get(CONF_SELECT_OPTIONS, [])
        if not isinstance(options_raw, list):
            options_raw = []
        self._options = [str(v) for v in options_raw if str(v).strip()]
        self._attr_options = self._options

    @property
    def current_option(self) -> str | None:
        raw = self._raw_value()
        if raw is None:
            return None
        value = str(raw)
        if self._options and value not in self._options:
            return None
        return value

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.manager.write_node(self._node_id, option)
        await self.coordinator.async_request_refresh()
