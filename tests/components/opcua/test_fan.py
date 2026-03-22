from __future__ import annotations

import pytest

from custom_components.opcua.fan import OpcUaFan


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
