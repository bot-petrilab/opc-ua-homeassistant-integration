from __future__ import annotations

from datetime import date, datetime, time

import pytest

from custom_components.opcua.binary_sensor import OpcUaBinarySensor
from custom_components.opcua.button import OpcUaButton
from custom_components.opcua.climate import OpcUaClimate
from custom_components.opcua.cover import OpcUaCover
from custom_components.opcua.date import OpcUaDate
from custom_components.opcua.datetime import OpcUaDateTime
from custom_components.opcua.fan import OpcUaFan
from custom_components.opcua.light import OpcUaLight
from custom_components.opcua.notify import OpcUaNotifyEntity
from custom_components.opcua.number import OpcUaNumber
from custom_components.opcua.scene import OpcUaScene
from custom_components.opcua.select import OpcUaSelect
from custom_components.opcua.sensor import OpcUaSensor
from custom_components.opcua.switch import OpcUaSwitch
from custom_components.opcua.text import OpcUaText
from custom_components.opcua.time import OpcUaTime
from custom_components.opcua.weather import OpcUaWeather


@pytest.mark.asyncio
async def test_sensor_binary_switch_button_scene_select_text_weather_notify_light_cover_climate(
    coordinator_all,
) -> None:
    endpoint = "opc.tcp://127.0.0.1:4846"

    sensor = OpcUaSensor(
        "e1",
        endpoint,
        {"name": "S", "node_id": "ns=2;s=EntityMatrix.Process.Temp"},
        coordinator_all,
    )
    assert sensor.native_value == 21.5

    b_sensor = OpcUaBinarySensor(
        "e1",
        endpoint,
        {"name": "BS", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_all,
    )
    assert b_sensor.is_on is True

    switch = OpcUaSwitch(
        "e1",
        endpoint,
        {"name": "SW", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_all,
    )
    await switch.async_turn_off()
    assert coordinator_all.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Test.Node",
        False,
    )

    button = OpcUaButton(
        "e1",
        endpoint,
        {
            "name": "BTN",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "button_payload": True,
        },
        coordinator_all,
    )
    await button.async_press()
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", True)

    scene = OpcUaScene(
        "e1",
        endpoint,
        {
            "name": "SC",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "scene_activate_value": "go",
        },
        coordinator_all,
    )
    await scene.async_activate()
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", "go")

    select = OpcUaSelect(
        "e1",
        endpoint,
        {
            "name": "SEL",
            "node_id": "ns=2;s=EntityMatrix.Select.Mode",
            "select_options": ["Auto", "Manual"],
        },
        coordinator_all,
    )
    assert select.current_option == "Auto"
    await select.async_select_option("Manual")
    assert coordinator_all.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Select.Mode",
        "Manual",
    )

    text = OpcUaText(
        "e1",
        endpoint,
        {"name": "TXT", "node_id": "ns=2;s=EntityMatrix.Text.Value", "text_max": 64},
        coordinator_all,
    )
    assert text.native_value == "Recipe-A"
    await text.async_set_value("Recipe-B")
    assert coordinator_all.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Text.Value",
        "Recipe-B",
    )

    weather = OpcUaWeather(
        "e1",
        endpoint,
        {
            "name": "W",
            "node_id": "ns=2;s=EntityMatrix.Weather.Temp",
            "humidity_node_id": "ns=2;s=EntityMatrix.Weather.Humidity",
            "pressure_node_id": "ns=2;s=EntityMatrix.Weather.Pressure",
            "wind_speed_node_id": "ns=2;s=EntityMatrix.Weather.Wind",
            "condition_node_id": "ns=2;s=EntityMatrix.Weather.Condition",
        },
        coordinator_all,
    )
    assert weather.native_temperature == 19.0
    assert weather.humidity == 40.0
    assert weather.condition == "sunny"

    notify = OpcUaNotifyEntity(
        "e1",
        endpoint,
        {
            "name": "N",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "message_node_id": "ns=2;s=EntityMatrix.Text.Value",
            "title_node_id": "ns=2;s=EntityMatrix.Notify.Title",
        },
        coordinator_all,
    )
    await notify.async_send_message(message="hello", title="t1")
    assert ("ns=2;s=EntityMatrix.Notify.Title", "t1") in coordinator_all.manager.writes
    assert ("ns=2;s=EntityMatrix.Text.Value", "hello") in coordinator_all.manager.writes

    light = OpcUaLight(
        "e1",
        endpoint,
        {
            "name": "L",
            "node_id": "ns=2;s=EntityMatrix.Light.On",
            "brightness_node_id": "ns=2;s=EntityMatrix.Light.Brightness",
            "effect_node_id": "ns=2;s=EntityMatrix.Light.Effect",
            "effect_list": ["off", "pulse"],
        },
        coordinator_all,
    )
    await light.async_turn_on(brightness=200, effect="pulse")
    assert any(
        w[0] == "ns=2;s=EntityMatrix.Light.On" and w[1] is True
        for w in coordinator_all.manager.writes
    )

    cover = OpcUaCover(
        "e1",
        endpoint,
        {
            "name": "C",
            "node_id": "ns=2;s=EntityMatrix.Cover.Pos",
            "set_position_node_id": "ns=2;s=EntityMatrix.Cover.Pos",
        },
        coordinator_all,
    )
    await cover.async_set_cover_position(position=33)
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Cover.Pos", 33)

    climate = OpcUaClimate(
        "e1",
        endpoint,
        {
            "name": "CL",
            "node_id": "ns=2;s=EntityMatrix.Process.Temp",
            "target_node_id": "ns=2;s=EntityMatrix.Process.Target",
            "hvac_mode_node_id": "ns=2;s=EntityMatrix.Process.Mode",
        },
        coordinator_all,
    )
    assert climate.current_temperature == 21.5
    await climate.async_set_temperature(temperature=24)
    assert coordinator_all.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Process.Target",
        24.0,
    )


@pytest.mark.asyncio
async def test_date_time_datetime_number_and_fan_write_paths(
    base_node_cfg, coordinator_datetime, coordinator_int
) -> None:
    endpoint = "opc.tcp://127.0.0.1:4846"

    date_entity = OpcUaDate("e1", endpoint, base_node_cfg, coordinator_datetime)
    await date_entity.async_set_value(date(2026, 3, 7))
    assert isinstance(coordinator_datetime.manager.writes[-1][1], datetime)

    time_entity = OpcUaTime("e1", endpoint, base_node_cfg, coordinator_datetime)
    await time_entity.async_set_value(time(13, 54, 22, 999999))
    assert coordinator_datetime.manager.writes[-1][1].time() == time(13, 54, 22)

    dt_entity = OpcUaDateTime("e1", endpoint, base_node_cfg, coordinator_datetime)
    await dt_entity.async_set_value(datetime(2026, 3, 8, 9, 30, 0))
    assert coordinator_datetime.manager.writes[-1][1] == datetime(2026, 3, 8, 9, 30, 0)

    num_entity = OpcUaNumber("e1", endpoint, base_node_cfg, coordinator_int)
    await num_entity.async_set_native_value(12.6)
    assert coordinator_int.manager.writes[-1] == (base_node_cfg["node_id"], 13)

    fan = OpcUaFan(
        "e1",
        endpoint,
        {
            "name": "F",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "speed_node_id": "ns=2;s=EntityMatrix.Test.Speed",
        },
        coordinator_int,
    )
    await fan.async_turn_on(percentage=80, preset_mode=None)
    assert ("ns=2;s=EntityMatrix.Test.Node", True) in coordinator_int.manager.writes
