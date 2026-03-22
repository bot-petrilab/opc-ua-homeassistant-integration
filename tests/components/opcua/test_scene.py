import pytest
from custom_components.opcua.scene import OpcUaScene


@pytest.mark.asyncio
async def test_scene_activate(coordinator_all):
    e = OpcUaScene(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "SC",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "scene_activate_value": True,
        },
        coordinator_all,
    )
    await e.async_activate()
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", True)
