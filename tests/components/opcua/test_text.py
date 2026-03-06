import pytest
from custom_components.opcua.text import OpcUaText

@pytest.mark.asyncio
async def test_text_set_value(coordinator_all):
    e=OpcUaText("e","opc.tcp://127.0.0.1:4846",{"name":"T","node_id":"ns=2;s=EntityMatrix.Text.Value","text_max":64},coordinator_all)
    await e.async_set_value("Recipe-Z")
    assert coordinator_all.manager.writes[-1]==("ns=2;s=EntityMatrix.Text.Value","Recipe-Z")
