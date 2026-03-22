from __future__ import annotations

from datetime import date, datetime, time

import pytest

from custom_components.opcua.date import OpcUaDate
from custom_components.opcua.datetime import OpcUaDateTime
from custom_components.opcua.number import OpcUaNumber
from custom_components.opcua.time import OpcUaTime


def test_coordinator_factory_fixture(coordinator_factory) -> None:
    c = coordinator_factory({"ns=2;s=EntityMatrix.Test.Node": 1})
    assert c.data["ns=2;s=EntityMatrix.Test.Node"] == 1


@pytest.mark.asyncio
async def test_number_write_preserves_int_type(base_node_cfg, coordinator_int) -> None:
    entity = OpcUaNumber(
        "entry-1", "opc.tcp://127.0.0.1:4846", base_node_cfg, coordinator_int
    )

    await entity.async_set_native_value(1234.8)

    assert coordinator_int.manager.writes[-1] == (base_node_cfg["node_id"], 1235)


@pytest.mark.asyncio
async def test_number_write_preserves_float_type(
    base_node_cfg, coordinator_float
) -> None:
    entity = OpcUaNumber(
        "entry-1", "opc.tcp://127.0.0.1:4846", base_node_cfg, coordinator_float
    )

    await entity.async_set_native_value(1234.8)

    node_id, value = coordinator_float.manager.writes[-1]
    assert node_id == base_node_cfg["node_id"]
    assert isinstance(value, float)
    assert value == 1234.8


@pytest.mark.asyncio
async def test_date_write_preserves_datetime_node(
    base_node_cfg, coordinator_datetime
) -> None:
    entity = OpcUaDate(
        "entry-1", "opc.tcp://127.0.0.1:4846", base_node_cfg, coordinator_datetime
    )

    await entity.async_set_value(date(2026, 3, 7))

    node_id, value = coordinator_datetime.manager.writes[-1]
    assert node_id == base_node_cfg["node_id"]
    assert isinstance(value, datetime)
    assert value.date() == date(2026, 3, 7)
    assert value.time() == time(10, 0, 0)


@pytest.mark.asyncio
async def test_time_write_strips_microseconds_for_datetime_node(
    base_node_cfg, coordinator_datetime
) -> None:
    entity = OpcUaTime(
        "entry-1", "opc.tcp://127.0.0.1:4846", base_node_cfg, coordinator_datetime
    )

    await entity.async_set_value(time(13, 54, 22, 538583))

    node_id, value = coordinator_datetime.manager.writes[-1]
    assert node_id == base_node_cfg["node_id"]
    assert isinstance(value, datetime)
    assert value.time() == time(13, 54, 22)


@pytest.mark.asyncio
async def test_datetime_write_keeps_datetime_type(
    base_node_cfg, coordinator_datetime
) -> None:
    entity = OpcUaDateTime(
        "entry-1", "opc.tcp://127.0.0.1:4846", base_node_cfg, coordinator_datetime
    )

    await entity.async_set_value(datetime(2026, 3, 8, 9, 30, 0))

    node_id, value = coordinator_datetime.manager.writes[-1]
    assert node_id == base_node_cfg["node_id"]
    assert isinstance(value, datetime)
    assert value == datetime(2026, 3, 8, 9, 30, 0)
