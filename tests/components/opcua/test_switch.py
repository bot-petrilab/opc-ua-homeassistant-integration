import pytest
from custom_components.opcua.switch import OpcUaSwitch


def test_switch_state_and_invert(coordinator_all):
    e = OpcUaSwitch(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "SW", "node_id": "ns=2;s=EntityMatrix.Test.Node", "invert": False},
        coordinator_all,
    )
    assert e.is_on is True

    e_inv = OpcUaSwitch(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "SW", "node_id": "ns=2;s=EntityMatrix.Test.Node", "invert": True},
        coordinator_all,
    )
    assert e_inv.is_on is False


@pytest.mark.asyncio
async def test_switch_turn_on_off(coordinator_all):
    e = OpcUaSwitch(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "SW", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_all,
    )
    await e.async_turn_on()
    await e.async_turn_off()
    assert ("ns=2;s=EntityMatrix.Test.Node", True) in coordinator_all.manager.writes
    assert ("ns=2;s=EntityMatrix.Test.Node", False) in coordinator_all.manager.writes
    assert coordinator_all.refresh_count == 2
