from datetime import datetime, time

import pytest

from custom_components.opcua.time import OpcUaTime, _as_time


def test_time_helper_parsing() -> None:
    assert _as_time(time(13, 54, 22)) == time(13, 54, 22)
    assert _as_time(datetime(2026, 3, 6, 10, 0, 0)) == time(10, 0, 0)
    assert _as_time("13:54:22") == time(13, 54, 22)
    assert _as_time("2026-03-08T09:00:00") == time(9, 0, 0)
    assert _as_time("bad") is None


@pytest.mark.asyncio
async def test_time_set_value_strips_microseconds(coordinator_datetime):
    e = OpcUaTime(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "T", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_datetime,
    )
    await e.async_set_value(time(13, 54, 22, 123456))
    assert coordinator_datetime.manager.writes[-1][1].time().microsecond == 0
    assert e.native_value == time(10, 0, 0)


@pytest.mark.asyncio
async def test_time_set_value_writes_time_or_string(coordinator_factory):
    coord_time = coordinator_factory({"ns=2;s=T": time(1, 2, 3)})
    entity_time = OpcUaTime(
        "e", "opc.tcp://127.0.0.1:4846", {"name": "T", "node_id": "ns=2;s=T"}, coord_time
    )
    await entity_time.async_set_value(time(4, 5, 6, 789))
    assert coord_time.manager.writes[-1] == ("ns=2;s=T", time(4, 5, 6))

    coord_str = coordinator_factory({"ns=2;s=T": "04:05:06"})
    entity_str = OpcUaTime(
        "e", "opc.tcp://127.0.0.1:4846", {"name": "T", "node_id": "ns=2;s=T"}, coord_str
    )
    await entity_str.async_set_value(time(7, 8, 9, 123))
    assert coord_str.manager.writes[-1] == ("ns=2;s=T", "07:08:09")
