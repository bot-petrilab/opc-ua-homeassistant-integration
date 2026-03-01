from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_NODE_ID, CONF_NODE_KIND, CONF_NODE_NAME, EVENT_NOTIFICATION
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
        entry_id: str,
        endpoint: str,
        notify_enabled: bool,
        notify_service: str,
        notify_title_prefix: str,
        notify_keywords: list[str],
    ) -> None:
        self.manager = manager
        self.nodes = nodes
        self.entry_id = entry_id
        self.endpoint = endpoint

        self.notify_enabled = notify_enabled
        self.notify_service = notify_service or "persistent_notification.create"
        self.notify_title_prefix = notify_title_prefix or "OPC-UA"
        self.notify_keywords = [k.lower() for k in notify_keywords if k]

        self._last_values: dict[str, Any] = {}
        self._notification_primed = False

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

        data = await self.manager.read_nodes(sorted(node_ids))
        await self._process_notifications(data)
        self._last_values = dict(data)
        return data

    def nodes_by_kind(self, kind: str) -> list[dict[str, Any]]:
        return [node for node in self.nodes if node.get(CONF_NODE_KIND) == kind]

    async def _process_notifications(self, data: dict[str, Any]) -> None:
        if not self._notification_primed:
            self._notification_primed = True
            return

        for node in self.nodes:
            node_id = node.get(CONF_NODE_ID)
            if not node_id:
                continue

            if node_id not in data:
                continue

            prev = self._last_values.get(node_id)
            cur = data.get(node_id)

            if prev == cur:
                continue

            if not self._is_notification_candidate(node):
                continue

            if not self._is_triggered(prev, cur):
                continue

            await self._emit_notification(node, cur)

    def _is_notification_candidate(self, node: dict[str, Any]) -> bool:
        name = str(node.get(CONF_NODE_NAME, "")).lower()
        node_id = str(node.get(CONF_NODE_ID, "")).lower()
        text = f"{name} {node_id}"

        return any(k in text for k in self.notify_keywords)

    @staticmethod
    def _is_triggered(prev: Any, cur: Any) -> bool:
        if isinstance(cur, bool):
            return (prev is not None) and (not bool(prev)) and bool(cur)

        if isinstance(cur, (int, float)):
            prev_num = float(prev) if isinstance(prev, (int, float)) else 0.0
            return cur > 0 and prev_num <= 0

        cur_s = str(cur).strip().lower()
        prev_s = str(prev).strip().lower() if prev is not None else ""
        if cur_s in {"", "ok", "none", "false", "0", "normal"}:
            return False
        return cur_s != prev_s

    async def _emit_notification(self, node: dict[str, Any], value: Any) -> None:
        node_name = str(node.get(CONF_NODE_NAME, "OPC-UA Node"))
        node_id = str(node.get(CONF_NODE_ID, ""))

        event_data = {
            "entry_id": self.entry_id,
            "endpoint": self.endpoint,
            "name": node_name,
            "node_id": node_id,
            "value": value,
        }
        self.hass.bus.async_fire(EVENT_NOTIFICATION, event_data)

        if not self.notify_enabled:
            return

        service = self.notify_service if "." in self.notify_service else "persistent_notification.create"
        domain, service_name = service.split(".", 1)

        title = f"{self.notify_title_prefix}: {node_name}"
        message = (
            f"OPC-UA notification from {self.endpoint}\n"
            f"Node: {node_id}\n"
            f"Value: {value}"
        )

        payload: dict[str, Any]
        if domain == "persistent_notification" and service_name == "create":
            notif_id = f"opcua_{self.entry_id}_{abs(hash(node_id)) % 1000000}"
            payload = {
                "title": title,
                "message": message,
                "notification_id": notif_id,
            }
        else:
            payload = {
                "title": title,
                "message": message,
            }

        try:
            await self.hass.services.async_call(domain, service_name, payload, blocking=False)
        except Exception as err:
            _LOGGER.warning("Failed to send notification via %s: %s", service, err)
