import pytest
from custom_components.opcua.button import OpcUaButton


@pytest.mark.asyncio
async def test_button_press(coordinator_all):
    e = OpcUaButton(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "BTN",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "button_payload": "go",
        },
        coordinator_all,
    )
    await e.async_press()
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", "go")
    assert coordinator_all.refresh_count == 1


@pytest.mark.asyncio
async def test_button_default_payload_true(coordinator_all):
    e = OpcUaButton(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "BTN", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_all,
    )
    await e.async_press()
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", True)
