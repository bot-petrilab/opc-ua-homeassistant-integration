import pytest
from custom_components.opcua.notify import OpcUaNotifyEntity


@pytest.mark.asyncio
async def test_notify_send_message(coordinator_all):
    e = OpcUaNotifyEntity(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "N",
            "node_id": "ns=2;s=EntityMatrix.Test.Node",
            "message_node_id": "ns=2;s=EntityMatrix.Text.Value",
            "title_node_id": "ns=2;s=EntityMatrix.Notify.Title",
        },
        coordinator_all,
    )
    await e.async_send_message(message="Hello", title="Warn")
    assert ("ns=2;s=EntityMatrix.Notify.Title", "Warn") in coordinator_all.manager.writes
    assert ("ns=2;s=EntityMatrix.Text.Value", "Hello") in coordinator_all.manager.writes
    assert coordinator_all.refresh_count == 1


@pytest.mark.asyncio
async def test_notify_send_message_falls_back_to_main_node(coordinator_all):
    e = OpcUaNotifyEntity(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {"name": "N", "node_id": "ns=2;s=EntityMatrix.Test.Node"},
        coordinator_all,
    )
    await e.async_send_message(message="Hello")
    assert coordinator_all.manager.writes[-1] == ("ns=2;s=EntityMatrix.Test.Node", "Hello")
