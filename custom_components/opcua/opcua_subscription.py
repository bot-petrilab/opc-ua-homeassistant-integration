from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SubscriptionHandler:
    """Forward asyncua subscription callbacks to the integration callback."""

    def __init__(self, callback: Callable[[str, Any], Awaitable[None] | None]) -> None:
        self._callback = callback

    async def datachange_notification(self, node, val, _data) -> None:
        node_id_obj = getattr(node, "nodeid", node)
        node_id = (
            node_id_obj.to_string()
            if hasattr(node_id_obj, "to_string")
            else str(node_id_obj)
        )
        maybe_awaitable = self._callback(node_id, val)
        if asyncio.iscoroutine(maybe_awaitable):
            await maybe_awaitable


async def establish_subscription(client, node_ids: list[str], callback, logger, endpoint: str):
    """Create a subscription and attach all requested nodes."""
    if not node_ids:
        return None, [], []

    handler = SubscriptionHandler(callback)
    subscription = await client.create_subscription(1000, handler)
    handles: list[Any] = []
    subscribed_node_ids: list[str] = []

    for node_id in node_ids:
        try:
            node = client.get_node(node_id)
            handle = await subscription.subscribe_data_change(node)
            handles.append(handle)
            subscribed_node_ids.append(node_id)
        except Exception as err:
            logger.debug(
                "Subscription setup failed for node %s on %s: %s",
                node_id,
                endpoint,
                err,
            )

    return subscription, handles, subscribed_node_ids
