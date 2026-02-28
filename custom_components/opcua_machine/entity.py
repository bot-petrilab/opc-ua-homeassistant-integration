from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OpcUaCoordinator
from .const import CONF_NODE_ID, CONF_NODE_NAME, DOMAIN


class OpcUaBaseEntity(CoordinatorEntity[OpcUaCoordinator]):
    """Base entity for OPC UA nodes."""

    def __init__(
        self,
        entry_id: str,
        endpoint: str,
        node_cfg: dict[str, Any],
        coordinator: OpcUaCoordinator,
        entity_kind: str,
    ) -> None:
        super().__init__(coordinator)
        self._node_cfg = node_cfg
        self._node_id = node_cfg[CONF_NODE_ID]
        self._attr_name = node_cfg[CONF_NODE_NAME]
        self._attr_unique_id = f"{entry_id}:{entity_kind}:{self._node_id}"
        self._attr_icon = node_cfg.get("icon")
        self._endpoint = endpoint
        self._attr_extra_state_attributes = {
            "endpoint": endpoint,
            "node_id": self._node_id,
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self._node_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._endpoint)},
            name=f"OPC UA {self._endpoint}",
            manufacturer="OPC Foundation / PLC Vendor",
            model="OPC UA Endpoint",
        )

    def _raw_value(self) -> Any:
        return self.coordinator.data.get(self._node_id)
