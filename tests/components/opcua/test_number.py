import pytest
from custom_components.opcua.number import OpcUaNumber, _to_float


def test_number_helper_and_native_value(coordinator_int):
    assert _to_float("12.2") == 12.2
    assert _to_float("bad") is None
    e = OpcUaNumber(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "N", "node_id": "ns=2;s=EntityMatrix.Test.Node", "number_min": 1, "number_max": 9, "number_step": 0.5},
        coordinator_int,
    )
    assert e.native_value == 10.0
    assert e._attr_native_min_value == 1.0
    assert e._attr_native_max_value == 9.0
    assert e._attr_native_step == 0.5


@pytest.mark.asyncio
async def test_number_set_native_value(coordinator_int):
    e = OpcUaNumber(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "N", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_int,
    )
    await e.async_set_native_value(12.2)
    assert coordinator_int.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", 12)


@pytest.mark.asyncio
async def test_number_set_native_value_preserves_bool_float_and_default(coordinator_factory):
    coord_bool = coordinator_factory({"ns=2;s=N": True})
    entity_bool = OpcUaNumber("e", "opc.tcp://127.0.0.1:4846", {"name":"N","node_id":"ns=2;s=N"}, coord_bool)
    await entity_bool.async_set_native_value(0)
    assert coord_bool.manager.writes[-1] == ("ns=2;s=N", False)

    coord_float = coordinator_factory({"ns=2;s=N": 1.5})
    entity_float = OpcUaNumber("e", "opc.tcp://127.0.0.1:4846", {"name":"N","node_id":"ns=2;s=N"}, coord_float)
    await entity_float.async_set_native_value(2.25)
    assert coord_float.manager.writes[-1] == ("ns=2;s=N", 2.25)

    coord_other = coordinator_factory({"ns=2;s=N": "x"})
    entity_other = OpcUaNumber("e", "opc.tcp://127.0.0.1:4846", {"name":"N","node_id":"ns=2;s=N"}, coord_other)
    await entity_other.async_set_native_value(3.5)
    assert coord_other.manager.writes[-1] == ("ns=2;s=N", 3.5)
