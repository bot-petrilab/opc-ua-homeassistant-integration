import pytest
from custom_components.opcua.select import OpcUaSelect


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
