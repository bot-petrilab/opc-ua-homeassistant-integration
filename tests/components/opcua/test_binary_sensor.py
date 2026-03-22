from custom_components.opcua.binary_sensor import OpcUaBinarySensor


def test_binary_sensor_state(coordinator_all):
    e = OpcUaBinarySensor(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "B", "node_id": "ns=2;s=EntityMatrix.Test.Node", "invert": False, "device_class": "problem"},
        coordinator_all,
    )
    assert e.is_on is True
    assert e._attr_device_class == "problem"



def test_binary_sensor_inverted_and_none(coordinator_factory):
    coord = coordinator_factory({"ns=2;s=B": False})
    e = OpcUaBinarySensor(
        "e", "opc.tcp://127.0.0.1:4846", {"name":"B","node_id":"ns=2;s=B","invert":True}, coord
    )
    assert e.is_on is True

    coord_none = coordinator_factory({})
    e_none = OpcUaBinarySensor(
        "e", "opc.tcp://127.0.0.1:4846", {"name":"B","node_id":"ns=2;s=B"}, coord_none
    )
    assert e_none.is_on is None
