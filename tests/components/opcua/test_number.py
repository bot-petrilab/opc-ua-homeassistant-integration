import pytest
from custom_components.opcua.number import OpcUaNumber

@pytest.mark.asyncio
async def test_number_set_native_value(coordinator_int):
    e=OpcUaNumber("e","opc.tcp://127.0.0.1:4846",{"name":"N","node_id":"ns=2;s=EntityMatrix.Test.Node"},coordinator_int)
    await e.async_set_native_value(12.2)
    assert coordinator_int.manager.writes[-1]==("ns=2;s=EntityMatrix.Test.Node",12)
