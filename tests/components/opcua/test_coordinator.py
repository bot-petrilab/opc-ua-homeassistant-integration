from __future__ import annotations

from types import SimpleNamespace

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.opcua.const import EVENT_NOTIFICATION
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


@pytest.mark.asyncio
async def test_process_notifications_emits_event_and_service_call() -> None:
    fired: list[tuple[str, dict]] = []
    service_calls: list[tuple[str, str, dict, bool]] = []

    class _Services:
        async def async_call(self, domain, service, payload, blocking=False):
            service_calls.append((domain, service, payload, blocking))

    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 0.0),
        bus=SimpleNamespace(async_fire=lambda event, data: fired.append((event, data))),
        services=_Services(),
    )
    manager = SimpleNamespace()

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=[{"node_id": "ns=2;s=Alarm", "name": "Alarm Active"}],
        scan_interval_seconds=1.0,
        poll_intervals={"normal": 1.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=True,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=["alarm"],
    )

    coordinator._notification_primed = True
    coordinator._last_values = {"ns=2;s=Alarm": False}

    await coordinator._process_notifications({"ns=2;s=Alarm": True})

    assert fired[0][0] == EVENT_NOTIFICATION
    assert fired[0][1]["node_id"] == "ns=2;s=Alarm"
    assert service_calls[0][0] == "persistent_notification"
    assert service_calls[0][1] == "create"
    assert "Alarm Active" in service_calls[0][2]["title"]


@pytest.mark.asyncio
async def test_process_notifications_skips_when_not_triggered_or_not_candidate() -> None:
    fired: list[tuple[str, dict]] = []

    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 0.0),
        bus=SimpleNamespace(async_fire=lambda event, data: fired.append((event, data))),
        services=SimpleNamespace(async_call=lambda *args, **kwargs: None),
    )

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=SimpleNamespace(),
        nodes=[{"node_id": "ns=2;s=State", "name": "Status"}],
        scan_interval_seconds=1.0,
        poll_intervals={"normal": 1.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=True,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=["alarm"],
    )

    coordinator._notification_primed = True
    coordinator._last_values = {"ns=2;s=State": False}

    await coordinator._process_notifications({"ns=2;s=State": True})
    assert fired == []


def test_is_triggered_handles_bool_numeric_and_text() -> None:
    assert OpcUaCoordinator._is_triggered(False, True) is True
    assert OpcUaCoordinator._is_triggered(True, True) is False
    assert OpcUaCoordinator._is_triggered(0, 2) is True
    assert OpcUaCoordinator._is_triggered(1, 2) is False
    assert OpcUaCoordinator._is_triggered("ok", "fault") is True
    assert OpcUaCoordinator._is_triggered("fault", "fault") is False
    assert OpcUaCoordinator._is_triggered("ok", "normal") is False


def test_is_notification_candidate_matches_name_or_node_id() -> None:
    coordinator = OpcUaCoordinator(
        hass=SimpleNamespace(loop=SimpleNamespace(time=lambda: 0.0), bus=None, services=None),
        manager=SimpleNamespace(),
        nodes=[],
        scan_interval_seconds=1.0,
        poll_intervals={"normal": 1.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=["alarm", "fault"],
    )

    assert coordinator._is_notification_candidate({"name": "Alarm Active", "node_id": "ns=2;s=A"}) is True
    assert coordinator._is_notification_candidate({"name": "State", "node_id": "ns=2;s=FaultSignal"}) is True
    assert coordinator._is_notification_candidate({"name": "State", "node_id": "ns=2;s=Normal"}) is False


@pytest.mark.asyncio
async def test_update_data_returns_last_values_when_no_nodes_due() -> None:
    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 1.0),
        bus=SimpleNamespace(async_fire=lambda *args, **kwargs: None),
        services=SimpleNamespace(async_call=lambda *args, **kwargs: None),
    )
    manager = SimpleNamespace(read_nodes=None)

    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=[{"node_id": "ns=2;s=Temp", "poll_profile": "normal"}],
        scan_interval_seconds=5.0,
        poll_intervals={"normal": 5.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=[],
    )
    coordinator._last_values = {"ns=2;s=Temp": 21.0}
    coordinator._node_last_polled = {"ns=2;s=Temp": 0.0}

    out = await coordinator._async_update_data()
    assert out == {"ns=2;s=Temp": 21.0}


@pytest.mark.asyncio
async def test_emit_notification_uses_generic_service_payload_and_handles_service_errors(caplog) -> None:
    class _Services:
        async def async_call(self, domain, service, payload, blocking=False):
            raise RuntimeError("send failed")

    fired: list[tuple[str, dict]] = []
    hass = SimpleNamespace(
        loop=SimpleNamespace(time=lambda: 0.0),
        bus=SimpleNamespace(async_fire=lambda event, data: fired.append((event, data))),
        services=_Services(),
    )
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=SimpleNamespace(),
        nodes=[],
        scan_interval_seconds=1.0,
        poll_intervals={"normal": 1.0},
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=True,
        notify_service="notify.mobile_app",
        notify_title_prefix="OPC-UA",
        notify_keywords=["alarm"],
    )

    await coordinator._emit_notification({"name": "Alarm", "node_id": "ns=2;s=Alarm"}, True)

    assert fired[0][0] == EVENT_NOTIFICATION
    assert "Failed to send notification via notify.mobile_app" in caplog.text
