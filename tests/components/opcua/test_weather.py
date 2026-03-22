from custom_components.opcua.weather import OpcUaWeather, _as_float


def test_weather_helper_and_values(coordinator_all):
    assert _as_float("1.5") == 1.5
    assert _as_float("bad") is None

    e = OpcUaWeather(
        "e",
        "opc.tcp://127.0.0.1:4846",
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
    assert e.native_temperature == 19.0
    assert e.humidity == 40.0
    assert e.native_pressure == 1013.0
    assert e.native_wind_speed == 3.2
    assert e.condition == "sunny"


def test_weather_optional_fields_return_none(coordinator_factory):
    coord = coordinator_factory({"ns=2;s=W.Temp": "bad"})
    e = OpcUaWeather(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "W", "node_id": "ns=2;s=W.Temp"},
        coord,
    )
    assert e.native_temperature is None
    assert e.humidity is None
    assert e.native_pressure is None
    assert e.native_wind_speed is None
    assert e.condition is None
