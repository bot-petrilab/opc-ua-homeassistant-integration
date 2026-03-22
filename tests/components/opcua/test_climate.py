import pytest
from custom_components.opcua.climate import OpcUaClimate, _as_float
from homeassistant.components.climate.const import HVACMode


def test_climate_helper_and_properties(coordinator_all):
    assert _as_float("12.5") == 12.5
    assert _as_float("bad") is None

    e = OpcUaClimate(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "C",
            "node_id": "ns=2;s=EntityMatrix.Process.Temp",
            "target_node_id": "ns=2;s=EntityMatrix.Process.Target",
            "hvac_mode_node_id": "ns=2;s=EntityMatrix.Process.Mode",
            "min_temp": 5,
            "max_temp": 30,
            "temp_step": 0.5,
        },
        coordinator_all,
    )
    assert e.current_temperature == 21.5
    assert e.target_temperature == 23.0
    assert e.hvac_mode == HVACMode.AUTO
    assert e._attr_min_temp == 5.0
    assert e._attr_max_temp == 30.0
    assert e._attr_target_temperature_step == 0.5


@pytest.mark.asyncio
async def test_climate_write_target_and_mode(coordinator_all):
    e = OpcUaClimate(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "C",
            "node_id": "ns=2;s=EntityMatrix.Process.Temp",
            "target_node_id": "ns=2;s=EntityMatrix.Process.Target",
            "hvac_mode_node_id": "ns=2;s=EntityMatrix.Process.Mode",
        },
        coordinator_all,
    )
    await e.async_set_temperature(temperature=24)
    await e.async_set_hvac_mode(HVACMode.HEAT)
    assert ("ns=2;s=EntityMatrix.Process.Target", 24.0) in coordinator_all.manager.writes
    assert ("ns=2;s=EntityMatrix.Process.Mode", "heat") in coordinator_all.manager.writes


def test_climate_hvac_mode_fallbacks(coordinator_factory):
    coord_bool = coordinator_factory({"ns=2;s=C": 20.0, "ns=2;s=M": True, "ns=2;s=T": 21.0})
    e_bool = OpcUaClimate("e", "opc.tcp://127.0.0.1:4846", {"name":"C","node_id":"ns=2;s=C","target_node_id":"ns=2;s=T","hvac_mode_node_id":"ns=2;s=M"}, coord_bool)
    assert e_bool.hvac_mode == HVACMode.HEAT

    coord_num = coordinator_factory({"ns=2;s=C": 20.0, "ns=2;s=M": 2, "ns=2;s=T": 21.0})
    e_num = OpcUaClimate("e", "opc.tcp://127.0.0.1:4846", {"name":"C","node_id":"ns=2;s=C","target_node_id":"ns=2;s=T","hvac_mode_node_id":"ns=2;s=M"}, coord_num)
    assert e_num.hvac_mode == HVACMode.COOL

    coord_default = coordinator_factory({"ns=2;s=C": 20.0, "ns=2;s=T": 21.0})
    e_default = OpcUaClimate("e", "opc.tcp://127.0.0.1:4846", {"name":"C","node_id":"ns=2;s=C","target_node_id":"ns=2;s=T"}, coord_default)
    assert e_default.hvac_mode == HVACMode.HEAT

    coord_off = coordinator_factory({"ns=2;s=C": 20.0})
    e_off = OpcUaClimate("e", "opc.tcp://127.0.0.1:4846", {"name":"C","node_id":"ns=2;s=C"}, coord_off)
    assert e_off.hvac_mode == HVACMode.OFF


@pytest.mark.asyncio
async def test_climate_set_temperature_ignores_missing_target(coordinator_all):
    e = OpcUaClimate(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "C", "node_id": "ns=2;s=EntityMatrix.Process.Temp"},
        coordinator_all,
    )
    await e.async_set_temperature()
    assert coordinator_all.manager.writes == []
