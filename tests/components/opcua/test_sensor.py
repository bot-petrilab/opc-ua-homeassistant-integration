from custom_components.opcua.sensor import OpcUaSensor, _to_float_if_possible


def test_sensor_helper_and_native_value(coordinator_all):
    assert _to_float_if_possible(True) is True
    assert _to_float_if_possible(1) == 1
    assert _to_float_if_possible("1.5") == 1.5
    assert _to_float_if_possible("abc") == "abc"

    e = OpcUaSensor(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "S",
            "node_id": "ns=2;s=EntityMatrix.Process.Temp",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
        },
        coordinator_all,
    )
    assert e.native_value == 21.5
    assert e._attr_native_unit_of_measurement == "°C"
    assert e._attr_device_class == "temperature"
    assert e._attr_state_class == "measurement"


def test_sensor_native_value_string_passthrough(coordinator_factory):
    coord = coordinator_factory({"ns=2;s=S": "abc"})
    e = OpcUaSensor("e", "opc.tcp://127.0.0.1:4846", {"name":"S","node_id":"ns=2;s=S"}, coord)
    assert e.native_value == "abc"
