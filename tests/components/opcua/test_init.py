from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.opcua import (
    _is_auth_error,
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.opcua.const import (
    CONF_ENDPOINT,
    CONF_NODES,
    CONF_NOTIFY_KEYWORDS,
    CONF_SECURITY_POLICY,
    DEFAULT_NOTIFY_KEYWORDS,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady


class _FakeEntry:
    def __init__(self) -> None:
        self.entry_id = "entry-1"
        self.data = {
            CONF_ENDPOINT: "opc.tcp://127.0.0.1:4846",
            CONF_SECURITY_POLICY: "None",
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

    monkeypatch.setattr(
        "custom_components.opcua.OpcUaClientManager", lambda **kwargs: fake_manager
    )
    monkeypatch.setattr(
        "custom_components.opcua.OpcUaCoordinator", lambda **kwargs: fake_coordinator
    )

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


@pytest.mark.asyncio
async def test_async_setup_returns_true() -> None:
    assert await async_setup(SimpleNamespace(), {}) is True


def test_is_auth_error_detects_expected_markers() -> None:
    assert _is_auth_error(Exception("BadIdentityToken")) is True
    assert _is_auth_error(Exception("authentication failed")) is True
    assert _is_auth_error(Exception("random network error")) is False


@pytest.mark.asyncio
async def test_setup_entry_raises_auth_failed_and_disconnects(monkeypatch) -> None:
    fake_manager = SimpleNamespace(disconnect=AsyncMock())

    class _FailingCoordinator:
        async def async_config_entry_first_refresh(self):
            raise RuntimeError("BadIdentityToken")

    monkeypatch.setattr(
        "custom_components.opcua.OpcUaClientManager", lambda **kwargs: fake_manager
    )
    monkeypatch.setattr(
        "custom_components.opcua.OpcUaCoordinator", lambda **kwargs: _FailingCoordinator()
    )

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
        )
    )
    entry = _FakeEntry()

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, entry)

    fake_manager.disconnect.assert_awaited()


@pytest.mark.asyncio
async def test_setup_entry_raises_not_ready_for_non_auth_errors(monkeypatch) -> None:
    fake_manager = SimpleNamespace(disconnect=AsyncMock())

    class _FailingCoordinator:
        async def async_config_entry_first_refresh(self):
            raise RuntimeError("connection reset")

    monkeypatch.setattr(
        "custom_components.opcua.OpcUaClientManager", lambda **kwargs: fake_manager
    )
    monkeypatch.setattr(
        "custom_components.opcua.OpcUaCoordinator", lambda **kwargs: _FailingCoordinator()
    )

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
        )
    )
    entry = _FakeEntry()

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)

    fake_manager.disconnect.assert_awaited()


@pytest.mark.asyncio
async def test_setup_entry_normalizes_non_list_notify_keywords(monkeypatch) -> None:
    fake_manager = SimpleNamespace(disconnect=AsyncMock())
    fake_coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock())
    coordinator_kwargs: dict[str, object] = {}

    def _fake_coordinator_factory(**kwargs):
        coordinator_kwargs.update(kwargs)
        return fake_coordinator

    monkeypatch.setattr(
        "custom_components.opcua.OpcUaClientManager", lambda **kwargs: fake_manager
    )
    monkeypatch.setattr(
        "custom_components.opcua.OpcUaCoordinator", _fake_coordinator_factory
    )

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_forward_entry_setups=AsyncMock(),
            async_unload_platforms=AsyncMock(return_value=True),
            async_reload=AsyncMock(),
        )
    )
    entry = _FakeEntry()
    entry.data[CONF_NOTIFY_KEYWORDS] = "alarm"

    assert await async_setup_entry(hass, entry)
    assert coordinator_kwargs["notify_keywords"] == [
        str(k).lower() for k in DEFAULT_NOTIFY_KEYWORDS
    ]


@pytest.mark.asyncio
async def test_async_reload_entry_calls_config_entry_reload() -> None:
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_reload=AsyncMock())
    )
    entry = _FakeEntry()

    await async_reload_entry(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with(entry.entry_id)
