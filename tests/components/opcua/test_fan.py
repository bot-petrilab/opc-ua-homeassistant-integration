from __future__ import annotations

import pytest

from custom_components.opcua.fan import OpcUaFan, _as_int


def test_fan_helper_and_properties(coordinator_bool) -> None:
    assert _as_int("42.2") == 42
    assert _as_int("bad") is None

    node_cfg = {
        "name": "Matrix Fan",
        "node_id": "ns=2;s=EntityMatrix.Test.Node",
        "speed_node_id": "ns=2;s=EntityMatrix.Test.Speed",
        "invert": True,
    }
    entity = OpcUaFan("entry-1", "opc.tcp://127.0.0.1:4846", node_cfg, coordinator_bool)

    assert entity.is_on is True
    assert entity.percentage == 10
    assert int(entity._attr_supported_features) > 0


@pytest.mark.asyncio
async def test_fan_turn_on_accepts_preset_mode_and_sets_speed(coordinator_bool) -> None:
    node_cfg = {
        "name": "Matrix Fan",
        "node_id": "ns=2;s=EntityMatrix.Operation.Running",
        "speed_node_id": "ns=2;s=EntityMatrix.Test.Speed",
        "invert": False,
    }
    entity = OpcUaFan("entry-1", "opc.tcp://127.0.0.1:4846", node_cfg, coordinator_bool)

    await entity.async_turn_on(percentage=80, preset_mode=None)

    assert coordinator_bool.manager.writes[0] == (
        "ns=2;s=EntityMatrix.Operation.Running",
        True,
    )
    assert coordinator_bool.manager.writes[1] == ("ns=2;s=EntityMatrix.Test.Speed", 80)
    assert coordinator_bool.refresh_count == 1


@pytest.mark.asyncio
async def test_fan_turn_off_writes_false(coordinator_bool) -> None:
    node_cfg = {
        "name": "Matrix Fan",
        "node_id": "ns=2;s=EntityMatrix.Operation.Running",
        "invert": False,
    }
    entity = OpcUaFan("entry-1", "opc.tcp://127.0.0.1:4846", node_cfg, coordinator_bool)

    await entity.async_turn_off()

    assert coordinator_bool.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Operation.Running",
        False,
    )


@pytest.mark.asyncio
async def test_fan_turn_off_inverted_and_set_percentage_clamps(coordinator_bool) -> None:
    node_cfg = {
        "name": "Matrix Fan",
        "node_id": "ns=2;s=EntityMatrix.Operation.Running",
        "speed_node_id": "ns=2;s=EntityMatrix.Test.Speed",
        "invert": True,
    }
    entity = OpcUaFan("entry-1", "opc.tcp://127.0.0.1:4846", node_cfg, coordinator_bool)

    await entity.async_turn_off()
    await entity.async_set_percentage(150)

    assert coordinator_bool.manager.writes[0] == (
        "ns=2;s=EntityMatrix.Operation.Running",
        True,
    )
    assert coordinator_bool.manager.writes[1] == ("ns=2;s=EntityMatrix.Test.Speed", 100)


@pytest.mark.asyncio
async def test_fan_set_percentage_ignores_missing_speed_node(coordinator_bool) -> None:
    node_cfg = {
        "name": "Matrix Fan",
        "node_id": "ns=2;s=EntityMatrix.Operation.Running",
        "invert": False,
    }
    entity = OpcUaFan("entry-1", "opc.tcp://127.0.0.1:4846", node_cfg, coordinator_bool)
    await entity.async_set_percentage(50)
    assert coordinator_bool.manager.writes == []
