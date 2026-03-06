from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.opcua import async_setup_entry, async_unload_entry
from custom_components.opcua.const import CONF_ENDPOINT, CONF_NODES, CONF_SCAN_INTERVAL, CONF_SECURITY_POLICY


class _FakeEntry:
    def __init__(self) -> None:
        self.entry_id = "entry-1"
        self.data = {
            CONF_ENDPOINT: "opc.tcp://127.0.0.1:4846",
            CONF_SECURITY_POLICY: "None",
            CONF_SCAN_INTERVAL: 2,
            CONF_NODES: [],
        }
        self.options = {}
        self.runtime_data = None

    def add_update_listener(self, _listener):
        return lambda: None

    def async_on_unload(self, _callback) -> None:
        return None


@pytest.mark.asyncio
async def test_setup_and_unload_entry(monkeypatch) -> None:
    fake_manager = SimpleNamespace(disconnect=AsyncMock())
    fake_coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock())

    monkeypatch.setattr("custom_components.opcua.OpcUaClientManager", lambda **kwargs: fake_manager)
    monkeypatch.setattr("custom_components.opcua.OpcUaCoordinator", lambda **kwargs: fake_coordinator)

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
        )
    )
    entry = _FakeEntry()

    assert await async_setup_entry(hass, entry)
    assert entry.runtime_data is not None

    unload_ok = await async_unload_entry(hass, entry)
    assert unload_ok is True
    fake_manager.disconnect.assert_awaited()
