from custom_components.opcua.binary_sensor import OpcUaBinarySensor


def test_binary_sensor_state(coordinator_all):
    e = OpcUaBinarySensor(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "B", "node_id": "ns=2;s=EntityMatrix.Test.Node", "invert": False},
        coordinator_all,
    )
    assert e.is_on is True
