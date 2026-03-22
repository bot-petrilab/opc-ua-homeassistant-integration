import pytest
from datetime import time
from custom_components.opcua.time import OpcUaTime


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
