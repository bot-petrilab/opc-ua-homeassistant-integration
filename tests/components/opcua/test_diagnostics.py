from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.opcua.diagnostics import async_get_config_entry_diagnostics
from custom_components.opcua.const import CONF_NODES


@pytest.mark.asyncio
async def test_diagnostics_redacts_sensitive_fields() -> None:
    entry = SimpleNamespace(
        entry_id="entry-1",
        title="OPC UA Test",
        state="loaded",
        data={
            "endpoint": "opc.tcp://127.0.0.1:4840",
            "username": "admin",
            "password": "secret",
            "client_key_password": "topsecret",
        },
        options={CONF_NODES: [{"name": "Temp", "node_id": "ns=2;s=Temp"}]},
    )

    out = await async_get_config_entry_diagnostics(SimpleNamespace(), entry)

    assert out["data"]["password"] == "REDACTED"
    assert out["data"]["username"] == "REDACTED"
    assert out["data"]["client_key_password"] == "REDACTED"
    assert out["node_count"] == 1
