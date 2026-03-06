import pytest
from custom_components.opcua.climate import OpcUaClimate
from homeassistant.components.climate.const import HVACMode

@pytest.mark.asyncio
async def test_climate_write_target_and_mode(coordinator_all):
    e=OpcUaClimate("e","opc.tcp://127.0.0.1:4846",{"name":"C","node_id":"ns=2;s=EntityMatrix.Process.Temp","target_node_id":"ns=2;s=EntityMatrix.Process.Target","hvac_mode_node_id":"ns=2;s=EntityMatrix.Process.Mode"},coordinator_all)
    await e.async_set_temperature(temperature=24)
    await e.async_set_hvac_mode(HVACMode.HEAT)
    assert ("ns=2;s=EntityMatrix.Process.Target",24.0) in coordinator_all.manager.writes
