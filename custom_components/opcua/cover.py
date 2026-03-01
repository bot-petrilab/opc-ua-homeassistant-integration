from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COVER_CLOSE_NODE_ID,
    CONF_COVER_INVERT_POSITION,
    CONF_COVER_OPEN_NODE_ID,
    CONF_COVER_SET_POSITION_NODE_ID,
    CONF_COVER_STOP_NODE_ID,
    CONF_ENDPOINT,
    CONF_NODE_TARGET_NODE_ID,
    NODE_KIND_COVER,
)
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
        OpcUaCover(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_COVER)
    ]
    async_add_entities(entities)


class OpcUaCover(OpcUaBaseEntity, CoverEntity):
    """OPC-UA cover entity."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_COVER)
        self._cfg = node_cfg
        self._target_node_id = node_cfg.get(CONF_NODE_TARGET_NODE_ID)
        self._set_position_node_id = node_cfg.get(CONF_COVER_SET_POSITION_NODE_ID)
        self._open_node_id = node_cfg.get(CONF_COVER_OPEN_NODE_ID)
        self._close_node_id = node_cfg.get(CONF_COVER_CLOSE_NODE_ID)
        self._stop_node_id = node_cfg.get(CONF_COVER_STOP_NODE_ID)
        self._invert_position = bool(node_cfg.get(CONF_COVER_INVERT_POSITION, False))

        feats = CoverEntityFeature(0)
        if self._open_node_id:
            feats |= CoverEntityFeature.OPEN
        if self._close_node_id:
            feats |= CoverEntityFeature.CLOSE
        if self._stop_node_id:
            feats |= CoverEntityFeature.STOP
        if self._set_position_node_id or self._target_node_id:
            feats |= CoverEntityFeature.SET_POSITION
        self._attr_supported_features = feats

    @property
    def current_cover_position(self) -> int | None:
        raw = self._raw_value()
        pos = _as_int(raw)
        if pos is None:
            return None
        pos = max(0, min(100, pos))
        return 100 - pos if self._invert_position else pos

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos <= 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        if self._open_node_id:
            await self.coordinator.manager.write_node(self._open_node_id, True)
        elif self._set_position_node_id or self._target_node_id:
            node = self._set_position_node_id or self._target_node_id
            await self.coordinator.manager.write_node(node, 0 if self._invert_position else 100)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        if self._close_node_id:
            await self.coordinator.manager.write_node(self._close_node_id, True)
        elif self._set_position_node_id or self._target_node_id:
            node = self._set_position_node_id or self._target_node_id
            await self.coordinator.manager.write_node(node, 100 if self._invert_position else 0)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        if self._stop_node_id:
            await self.coordinator.manager.write_node(self._stop_node_id, True)
            await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        if ATTR_POSITION not in kwargs:
            return
        node = self._set_position_node_id or self._target_node_id
        if not node:
            return
        pos = int(kwargs[ATTR_POSITION])
        raw = 100 - pos if self._invert_position else pos
        await self.coordinator.manager.write_node(node, raw)
        await self.coordinator.async_request_refresh()
