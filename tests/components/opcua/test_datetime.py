from datetime import datetime

import pytest

from custom_components.opcua.datetime import OpcUaDateTime, _as_datetime


def test_datetime_helper_parsing() -> None:
    now = datetime(2026, 3, 8, 9, 0, 0)
    assert _as_datetime(now) == now
    assert _as_datetime("2026-03-08T09:00:00") == now
    assert _as_datetime("bad") is None


@pytest.mark.asyncio
async def test_datetime_set_value(coordinator_datetime):
    e = OpcUaDateTime(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "DT", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_datetime,
    )
    val = datetime(2026, 3, 8, 9, 0, 0)
    await e.async_set_value(val)
    assert coordinator_datetime.manager.writes[-1][1] == val
    assert e.native_value == datetime(2026, 3, 6, 10, 0, 0)


@pytest.mark.asyncio
async def test_datetime_set_value_serializes_non_datetime_current(coordinator_factory):
    coord = coordinator_factory({"ns=2;s=DT": "2026-03-06T10:00:00"})
    e = OpcUaDateTime(
        "e", "opc.tcp://127.0.0.1:4846", {"name": "DT", "node_id": "ns=2;s=DT"}, coord
    )
    val = datetime(2026, 3, 8, 9, 0, 0)
    await e.async_set_value(val)
    assert coord.manager.writes[-1] == ("ns=2;s=DT", "2026-03-08T09:00:00")
