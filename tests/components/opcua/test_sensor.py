from custom_components.opcua.sensor import OpcUaSensor


def test_sensor_native_value(coordinator_all):
    e = OpcUaSensor(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "S", "node_id": "ns=2;s=EntityMatrix.Process.Temp"},
        coordinator_all,
    )
    assert e.native_value == 21.5
