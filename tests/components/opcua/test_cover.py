import pytest

from custom_components.opcua.cover import OpcUaCover, _as_int


def test_cover_helper_and_properties(coordinator_all):
    assert _as_int("12.6") == 13
    assert _as_int("bad") is None

    e = OpcUaCover(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "CV",
            "node_id": "ns=2;s=EntityMatrix.Cover.Pos",
            "invert_position": True,
            "open_node_id": "ns=2;s=Cover.Open",
            "close_node_id": "ns=2;s=Cover.Close",
            "stop_node_id": "ns=2;s=Cover.Stop",
            "set_position_node_id": "ns=2;s=Cover.SetPos",
        },
        coordinator_all,
    )
    assert e.current_cover_position == 45
    assert e.is_closed is False
    assert int(e._attr_supported_features) > 0


@pytest.mark.asyncio
async def test_cover_open_close_stop_and_set_position_paths(coordinator_all):
    e = OpcUaCover(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "CV",
            "node_id": "ns=2;s=EntityMatrix.Cover.Pos",
            "open_node_id": "ns=2;s=Cover.Open",
            "close_node_id": "ns=2;s=Cover.Close",
            "stop_node_id": "ns=2;s=Cover.Stop",
            "set_position_node_id": "ns=2;s=Cover.SetPos",
        },
        coordinator_all,
    )
    await e.async_open_cover()
    await e.async_close_cover()
    await e.async_stop_cover()
    await e.async_set_cover_position(position=44)

    assert ("ns=2;s=Cover.Open", True) in coordinator_all.manager.writes
    assert ("ns=2;s=Cover.Close", True) in coordinator_all.manager.writes
    assert ("ns=2;s=Cover.Stop", True) in coordinator_all.manager.writes
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=Cover.SetPos", 44)
    assert coordinator_all.refresh_count == 4


@pytest.mark.asyncio
async def test_cover_fallback_target_node_and_invert_position(coordinator_all):
    e = OpcUaCover(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "CV",
            "node_id": "ns=2;s=EntityMatrix.Cover.Pos",
            "target_node_id": "ns=2;s=Cover.Target",
            "invert_position": True,
        },
        coordinator_all,
    )
    await e.async_open_cover()
    await e.async_close_cover()
    await e.async_set_cover_position(position=20)

    assert coordinator_all.manager.writes[0] == ("ns=2;s=Cover.Target", 0)
    assert coordinator_all.manager.writes[1] == ("ns=2;s=Cover.Target", 100)
    assert coordinator_all.manager.writes[2] == ("ns=2;s=Cover.Target", 80)


@pytest.mark.asyncio
async def test_cover_set_position_ignores_missing_position_or_target(coordinator_all):
    e = OpcUaCover(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "CV", "node_id": "ns=2;s=EntityMatrix.Cover.Pos"},
        coordinator_all,
    )
    await e.async_set_cover_position()
    assert coordinator_all.manager.writes == []
