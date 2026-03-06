import pytest
from custom_components.opcua.cover import OpcUaCover

@pytest.mark.asyncio
async def test_cover_set_position(coordinator_all):
    e=OpcUaCover("e","opc.tcp://127.0.0.1:4846",{"name":"CV","node_id":"ns=2;s=EntityMatrix.Cover.Pos","set_position_node_id":"ns=2;s=EntityMatrix.Cover.Pos"},coordinator_all)
    await e.async_set_cover_position(position=44)
    assert coordinator_all.manager.writes[-1]==("ns=2;s=EntityMatrix.Cover.Pos",44)
