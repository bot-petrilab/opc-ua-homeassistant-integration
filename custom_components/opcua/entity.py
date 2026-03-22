from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OpcUaCoordinator
from .const import (
    CONF_NODE_DEVICE_ID,
    CONF_NODE_DEVICE_MANUFACTURER,
    CONF_NODE_DEVICE_MODEL,
    CONF_NODE_DEVICE_NAME,
    CONF_NODE_DEVICE_SERIAL,
    CONF_NODE_ID,
    CONF_NODE_NAME,
    DOMAIN,
)


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
        self._attr_has_entity_name = True
        self._endpoint = endpoint
        self._attr_extra_state_attributes = {
            "endpoint": endpoint,
            "node_id": self._node_id,
        }

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self._node_id in self.coordinator.data
        )

    @property
    def device_info(self) -> DeviceInfo | None:
        raw_device_id = self._node_cfg.get(CONF_NODE_DEVICE_ID)
        if not raw_device_id:
            return None

        device_id = str(raw_device_id)
        device_name = str(self._node_cfg.get(CONF_NODE_DEVICE_NAME) or device_id)
        manufacturer = str(
            self._node_cfg.get(CONF_NODE_DEVICE_MANUFACTURER)
            or "OPC Foundation / PLC Vendor"
        )
        model = str(self._node_cfg.get(CONF_NODE_DEVICE_MODEL) or "OPC UA Endpoint")

        info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._endpoint}|{device_id}")},
            name=device_name,
            manufacturer=manufacturer,
            model=model,
        )

        serial = self._node_cfg.get(CONF_NODE_DEVICE_SERIAL)
        if serial:
            info["serial_number"] = str(serial)

        return info

    def _raw_value(self) -> Any:
        return self.coordinator.data.get(self._node_id)
