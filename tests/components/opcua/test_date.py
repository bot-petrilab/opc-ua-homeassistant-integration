from datetime import date, datetime

import pytest

from custom_components.opcua.date import OpcUaDate, _as_date


def test_date_helper_parsing() -> None:
    assert _as_date(date(2026, 3, 8)) == date(2026, 3, 8)
    assert _as_date(datetime(2026, 3, 8, 9, 0, 0)) == date(2026, 3, 8)
    assert _as_date("2026-03-08") == date(2026, 3, 8)
    assert _as_date("bad") is None


@pytest.mark.asyncio
async def test_date_set_value_keeps_datetime(coordinator_datetime):
    e = OpcUaDate(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "D", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_datetime,
    )
    await e.async_set_value(date(2026, 3, 8))
    assert isinstance(coordinator_datetime.manager.writes[-1][1], datetime)
    assert e.native_value == date(2026, 3, 6)


@pytest.mark.asyncio
async def test_date_set_value_writes_date_or_string(coordinator_factory):
    coord_date = coordinator_factory({"ns=2;s=Date": date(2026, 3, 6)})
    entity_date = OpcUaDate(
        "e", "opc.tcp://127.0.0.1:4846", {"name": "D", "node_id": "ns=2;s=Date"}, coord_date
    )
    await entity_date.async_set_value(date(2026, 3, 9))
    assert coord_date.manager.writes[-1] == ("ns=2;s=Date", date(2026, 3, 9))

    coord_str = coordinator_factory({"ns=2;s=Date": "2026-03-06"})
    entity_str = OpcUaDate(
        "e", "opc.tcp://127.0.0.1:4846", {"name": "D", "node_id": "ns=2;s=Date"}, coord_str
    )
    await entity_str.async_set_value(date(2026, 3, 10))
    assert coord_str.manager.writes[-1] == ("ns=2;s=Date", "2026-03-10")
