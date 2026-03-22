from __future__ import annotations

from types import SimpleNamespace

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.opcua.coordinator import OpcUaCoordinator


def test_coordinator_accepts_subsecond_poll_intervals() -> None:
    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 0.0),
        bus=SimpleNamespace(async_fire=lambda *args, **kwargs: None),
        services=SimpleNamespace(async_call=lambda *args, **kwargs: None),
    )
    manager = SimpleNamespace()

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=[],
        scan_interval_seconds=0.5,
        poll_intervals={"fast": 0.5, "normal": 1.2, "slow": 5.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=[],
    )

    assert coordinator.poll_intervals["fast"] == 0.5
    assert coordinator.poll_intervals["normal"] == 1.2
    assert coordinator.poll_intervals["slow"] == 5.0


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_when_endpoint_unavailable() -> None:
    class FailingManager:
        async def read_nodes(self, _node_ids):
            raise RuntimeError("connect timeout")

    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 0.0),
        bus=SimpleNamespace(async_fire=lambda *args, **kwargs: None),
        services=SimpleNamespace(async_call=lambda *args, **kwargs: None),
    )

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=FailingManager(),
        nodes=[{"node_id": "ns=2;s=Home.LivingRoom.Temperature"}],
        scan_interval_seconds=1.0,
        poll_intervals={"normal": 1.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=[],
    )

    with pytest.raises(UpdateFailed, match="unavailable"):
        await coordinator._async_update_data()
