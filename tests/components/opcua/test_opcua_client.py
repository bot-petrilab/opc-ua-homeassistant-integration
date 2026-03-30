from __future__ import annotations

import pytest

from custom_components.opcua.opcua_client import OpcUaClientManager


class _FakeNode:
    def __init__(self, node_id: str, client) -> None:
        self.nodeid = type("NodeId", (), {"to_string": lambda self: node_id})()
        self._node_id = node_id
        self._client = client

    async def read_value(self):
        value = self._client.values.get(self._node_id)
        if isinstance(value, Exception):
            raise value
        return value

    async def write_value(self, value):
        self._client.writes.append((self._node_id, value))


class _FakeSubscription:
    def __init__(self, client, handler) -> None:
        self.client = client
        self.handler = handler
        self.unsubscribed = []
        self.deleted = False

    async def subscribe_data_change(self, node):
        handle = f"handle:{node.nodeid.to_string()}"
        self.client.subscribed.append(node.nodeid.to_string())
        return handle

    async def unsubscribe(self, handles):
        self.unsubscribed.extend(handles)

    async def delete(self):
        self.deleted = True


class _FakeClient:
    instances = []

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.security = None
        self.username = None
        self.password = None
        self.values = {"ns=2;s=Temp": 21.0, "ns=2;s=Bool": True}
        self.writes = []
        self.subscribed = []
        self.connect_calls = 0
        self.disconnect_calls = 0
        self.connect_fail_once = False
        self.fail_reads_once = False
        self.subscription = None
        _FakeClient.instances.append(self)

    async def set_security_string(self, value: str) -> None:
        self.security = value

    def set_user(self, username: str) -> None:
        self.username = username

    def set_password(self, password: str) -> None:
        self.password = password

    async def connect(self) -> None:
        self.connect_calls += 1
        if self.connect_fail_once:
            self.connect_fail_once = False
            raise RuntimeError("connect failed")

    async def disconnect(self) -> None:
        self.disconnect_calls += 1

    def get_node(self, node_id: str):
        return _FakeNode(node_id, self)

    async def create_subscription(self, _interval: int, handler):
        self.subscription = _FakeSubscription(self, handler)
        return self.subscription


@pytest.fixture(autouse=True)
def _reset_fake_client(monkeypatch):
    _FakeClient.instances = []
    monkeypatch.setattr("custom_components.opcua.opcua_client.Client", _FakeClient)


@pytest.mark.asyncio
async def test_subscribe_nodes_reads_initial_snapshot_and_subscribes() -> None:
    updates = []

    async def _callback(node_id: str, value):
        updates.append((node_id, value))

    manager = OpcUaClientManager(endpoint="opc.tcp://127.0.0.1:4840", security_policy="None", username=None, password=None)
    initial = await manager.subscribe_nodes(["ns=2;s=Temp", "ns=2;s=Bool"], _callback)

    assert initial == {"ns=2;s=Temp": 21.0, "ns=2;s=Bool": True}
    client = _FakeClient.instances[-1]
    assert client.subscribed == ["ns=2;s=Temp", "ns=2;s=Bool"]

    await client.subscription.handler.datachange_notification(client.get_node("ns=2;s=Temp"), 22.0, None)
    assert updates == [("ns=2;s=Temp", 22.0)]


@pytest.mark.asyncio
async def test_read_failure_preserves_subscription_configuration_for_reconnect() -> None:
    manager = OpcUaClientManager(endpoint="opc.tcp://127.0.0.1:4840", security_policy="None", username=None, password=None)

    async def _callback(_node_id: str, _value):
        return None

    await manager.subscribe_nodes(["ns=2;s=Temp"], _callback)
    first_client = _FakeClient.instances[-1]
    first_client.values = RuntimeError("bad")  # not used directly, just to keep reference

    await manager.disconnect(preserve_subscription=True)
    await manager.ensure_connected()
    second_client = _FakeClient.instances[-1]

    assert second_client is not first_client
    assert second_client.subscribed == ["ns=2;s=Temp"]


@pytest.mark.asyncio
async def test_disconnect_clears_or_preserves_subscription_as_requested() -> None:
    manager = OpcUaClientManager(endpoint="opc.tcp://127.0.0.1:4840", security_policy="None", username=None, password=None)

    async def _callback(_node_id: str, _value):
        return None

    await manager.subscribe_nodes(["ns=2;s=Temp"], _callback)
    assert manager._desired_subscription_node_ids == ["ns=2;s=Temp"]

    await manager.disconnect(preserve_subscription=True)
    assert manager._desired_subscription_node_ids == ["ns=2;s=Temp"]

    await manager.ensure_connected()
    await manager.disconnect()
    assert manager._desired_subscription_node_ids == []
    assert manager._subscription_callback is None


@pytest.mark.asyncio
async def test_partial_subscription_failure_keeps_successful_handles(monkeypatch) -> None:
    class PartialClient(_FakeClient):
        async def create_subscription(self, _interval: int, handler):
            sub = await super().create_subscription(_interval, handler)
            original = sub.subscribe_data_change

            async def _wrapped(node):
                if node.nodeid.to_string() == "ns=2;s=Bad":
                    raise RuntimeError("subscribe failed")
                return await original(node)

            sub.subscribe_data_change = _wrapped
            return sub

    monkeypatch.setattr("custom_components.opcua.opcua_client.Client", PartialClient)
    manager = OpcUaClientManager(endpoint="opc.tcp://127.0.0.1:4840", security_policy="None", username=None, password=None)

    async def _callback(_node_id: str, _value):
        return None

    await manager.subscribe_nodes(["ns=2;s=Temp", "ns=2;s=Bad"], _callback)
    assert manager._subscription_handles == ["handle:ns=2;s=Temp"]
    assert manager._subscribed_node_ids == ["ns=2;s=Temp", "ns=2;s=Bad"]
