import pytest
from datetime import datetime
from custom_components.opcua.datetime import OpcUaDateTime

@pytest.mark.asyncio
async def test_datetime_set_value(coordinator_datetime):
    e=OpcUaDateTime("e","opc.tcp://127.0.0.1:4846",{"name":"DT","node_id":"ns=2;s=EntityMatrix.Test.Node"},coordinator_datetime)
    val=datetime(2026,3,8,9,0,0)
    await e.async_set_value(val)
    assert coordinator_datetime.manager.writes[-1][1]==val
