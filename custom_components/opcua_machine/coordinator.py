from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_NODE_ID, CONF_NODE_KIND
from .opcua_client import OpcUaClientManager

_LOGGER = logging.getLogger(__name__)


class OpcUaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate periodic reads from one OPC UA endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: OpcUaClientManager,
        nodes: list[dict[str, Any]],
        scan_interval_seconds: int,
    ) -> None:
        self.manager = manager
        self.nodes = nodes

        super().__init__(
            hass,
            _LOGGER,
            name="opcua_machine",
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        node_ids: set[str] = set()
        for node in self.nodes:
            for key, value in node.items():
                if not isinstance(value, str):
                    continue
                if key == CONF_NODE_ID or key.endswith("_node_id"):
                    node_ids.add(value)

        if not node_ids:
            return {}
        return await self.manager.read_nodes(sorted(node_ids))

    def nodes_by_kind(self, kind: str) -> list[dict[str, Any]]:
        return [node for node in self.nodes if node.get(CONF_NODE_KIND) == kind]
