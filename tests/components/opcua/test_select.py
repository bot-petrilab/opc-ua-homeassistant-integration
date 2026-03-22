import pytest
from custom_components.opcua.select import OpcUaSelect


def test_select_current_option(coordinator_all):
    e = OpcUaSelect(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "SEL",
            "node_id": "ns=2;s=EntityMatrix.Select.Mode",
            "select_options": ["Auto", "Manual"],
        },
        coordinator_all,
    )
    assert e.current_option == "Auto"
    assert e._attr_options == ["Auto", "Manual"]

    coord = type(coordinator_all)(data={"ns=2;s=EntityMatrix.Select.Mode": "Other"})
    coord.manager = coordinator_all.manager
    coord.refresh_count = 0
    coord.last_update_success = True
    e_other = OpcUaSelect(
        "e", "opc.tcp://127.0.0.1:4846", {"name":"SEL","node_id":"ns=2;s=EntityMatrix.Select.Mode","select_options":["Auto"]}, coord
    )
    assert e_other.current_option is None


@pytest.mark.asyncio
async def test_select_option(coordinator_all):
    e = OpcUaSelect(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "SEL",
            "node_id": "ns=2;s=EntityMatrix.Select.Mode",
            "select_options": ["Auto", "Manual"],
        },
        coordinator_all,
    )
    await e.async_select_option("Manual")
    assert coordinator_all.manager.writes[-1] == (
        "ns=2;s=EntityMatrix.Select.Mode",
        "Manual",
    )
