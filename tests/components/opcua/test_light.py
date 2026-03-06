import pytest
from custom_components.opcua.light import OpcUaLight

@pytest.mark.asyncio
async def test_light_turn_on_writes_nodes(coordinator_all):
    e=OpcUaLight("e","opc.tcp://127.0.0.1:4846",{"name":"L","node_id":"ns=2;s=EntityMatrix.Light.On","brightness_node_id":"ns=2;s=EntityMatrix.Light.Brightness","effect_node_id":"ns=2;s=EntityMatrix.Light.Effect","effect_list":["off","pulse"]},coordinator_all)
    await e.async_turn_on(brightness=180,effect="pulse")
    assert any(w[0]=="ns=2;s=EntityMatrix.Light.On" and w[1] is True for w in coordinator_all.manager.writes)
