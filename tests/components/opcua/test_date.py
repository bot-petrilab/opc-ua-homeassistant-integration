import pytest
from datetime import date, datetime
from custom_components.opcua.date import OpcUaDate

@pytest.mark.asyncio
async def test_date_set_value_keeps_datetime(coordinator_datetime):
    e=OpcUaDate("e","opc.tcp://127.0.0.1:4846",{"name":"D","node_id":"ns=2;s=EntityMatrix.Test.Node"},coordinator_datetime)
    await e.async_set_value(date(2026,3,8))
    assert isinstance(coordinator_datetime.manager.writes[-1][1], datetime)
