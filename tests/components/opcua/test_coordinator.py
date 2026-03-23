from __future__ import annotations

from types import SimpleNamespace

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.opcua.const import EVENT_NOTIFICATION
from custom_components.opcua.coordinator import OpcUaCoordinator


def _hass_with_calls(service_impl=None):
    fired: list[tuple[str, dict]] = []
    service_calls: list[tuple[str, str, dict, bool]] = []

    class _Services:
        async def async_call(self, domain, service, payload, blocking=False):
            service_calls.append((domain, service, payload, blocking))
            if service_impl:
                return await service_impl(domain, service, payload, blocking)
            return None

    hass = SimpleNamespace(
        bus=SimpleNamespace(async_fire=lambda event, data: fired.append((event, data))),
        services=_Services(),
    )
    return hass, fired, service_calls


@pytest.mark.asyncio
async def test_coordinator_subscribes_and_returns_initial_snapshot() -> None:
    class Manager:
        def __init__(self):
            self.calls = []

        async def subscribe_nodes(self, node_ids, callback):
            self.calls.append((tuple(node_ids), callback))
            return {"ns=2;s=Temp": 21.0, "ns=2;s=Brightness": 100}

        async def read_nodes(self, node_ids):
            return {node_id: 99 for node_id in node_ids}

    hass, _, _ = _hass_with_calls()
    manager = Manager()
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=manager,
        nodes=[
            {"node_id": "ns=2;s=Temp"},
            {"node_id": "ns=2;s=Light.On", "brightness_node_id": "ns=2;s=Brightness"},
        ],
        scan_interval_seconds=None,
        poll_intervals=None,
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=[],
    )

    out = await coordinator._async_update_data()
    assert out["ns=2;s=Temp"] == 21.0
    assert set(manager.calls[0][0]) == {"ns=2;s=Temp", "ns=2;s=Light.On", "ns=2;s=Brightness"}


@pytest.mark.asyncio
async def test_coordinator_refresh_reads_current_snapshot_after_subscription() -> None:
    class Manager:
        async def subscribe_nodes(self, node_ids, callback):
            return {node_ids[0]: 1}

        async def read_nodes(self, node_ids):
            return {node_ids[0]: 2}

    hass, _, _ = _hass_with_calls()
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=Manager(),
        nodes=[{"node_id": "ns=2;s=Temp"}],
        scan_interval_seconds=None,
        poll_intervals=None,
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=False,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=[],
    )

    await coordinator._async_update_data()
    out = await coordinator._async_update_data()
    assert out == {"ns=2;s=Temp": 2}


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_when_subscription_fails() -> None:
    class FailingManager:
        async def subscribe_nodes(self, _node_ids, _callback):
            raise RuntimeError("connect timeout")

    hass, _, _ = _hass_with_calls()
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=FailingManager(),
        nodes=[{"node_id": "ns=2;s=Home.LivingRoom.Temperature"}],
        scan_interval_seconds=None,
        poll_intervals=None,
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
async def test_subscription_update_emits_event_and_service_call() -> None:
    hass, fired, service_calls = _hass_with_calls()
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=SimpleNamespace(),
        nodes=[{"node_id": "ns=2;s=Alarm", "name": "Alarm Active"}],
        scan_interval_seconds=None,
        poll_intervals=None,
        entry_id="entry-1",
        endpoint="opc.tcp://127.0.0.1:4840",
        notify_enabled=True,
        notify_service="persistent_notification.create",
        notify_title_prefix="OPC-UA",
        notify_keywords=["alarm"],
    )

    coordinator._notification_primed = True
    coordinator._last_values = {"ns=2;s=Alarm": False}

    await coordinator._handle_subscription_update("ns=2;s=Alarm", True)

    assert fired[0][0] == EVENT_NOTIFICATION
    assert fired[0][1]["node_id"] == "ns=2;s=Alarm"
    assert service_calls[0][0] == "persistent_notification"
    assert service_calls[0][1] == "create"


@pytest.mark.asyncio
async def test_process_notifications_skips_when_not_triggered_or_not_candidate() -> None:
    hass, fired, _ = _hass_with_calls()
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=SimpleNamespace(),
        nodes=[{"node_id": "ns=2;s=State", "name": "Status"}],
        scan_interval_seconds=None,
        poll_intervals=None,
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
        hass=SimpleNamespace(bus=None, services=None),
        manager=SimpleNamespace(),
        nodes=[],
        scan_interval_seconds=None,
        poll_intervals=None,
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
async def test_emit_notification_uses_generic_service_payload_and_handles_service_errors(caplog) -> None:
    async def _raise(*_args, **_kwargs):
        raise RuntimeError("send failed")

    hass, fired, _ = _hass_with_calls(service_impl=_raise)
    coordinator = OpcUaCoordinator(
        hass=hass,
        manager=SimpleNamespace(),
        nodes=[],
        scan_interval_seconds=None,
        poll_intervals=None,
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
