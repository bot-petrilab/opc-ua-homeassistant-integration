from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pytest

from custom_components.opcua.const import (
    CONF_NODE_ID,
    CONF_NODE_NAME,
)


@dataclass
class MockManager:
    writes: list[tuple[str, Any]] = field(default_factory=list)

    async def write_node(self, node_id: str, value: Any) -> None:
        self.writes.append((node_id, value))


@dataclass
class MockCoordinator:
    data: dict[str, Any]
    manager: MockManager = field(default_factory=MockManager)
    refresh_count: int = 0
    last_update_success: bool = True

    async def async_request_refresh(self) -> None:
        self.refresh_count += 1


@pytest.fixture
def base_node_cfg() -> dict[str, Any]:
    return {
        CONF_NODE_NAME: "Test Node",
        CONF_NODE_ID: "ns=2;s=EntityMatrix.Test.Node",
    }


@pytest.fixture
def coordinator_datetime() -> MockCoordinator:
    return MockCoordinator(
        data={
            "ns=2;s=EntityMatrix.Test.Node": datetime(2026, 3, 6, 10, 0, 0),
            "ns=2;s=EntityMatrix.Test.Speed": 42,
        }
    )


@pytest.fixture
def coordinator_int() -> MockCoordinator:
    return MockCoordinator(
        data={
            "ns=2;s=EntityMatrix.Test.Node": 10,
            "ns=2;s=EntityMatrix.Test.Speed": 75,
        }
    )


@pytest.fixture
def coordinator_float() -> MockCoordinator:
    return MockCoordinator(
        data={
            "ns=2;s=EntityMatrix.Test.Node": 10.5,
            "ns=2;s=EntityMatrix.Test.Speed": 55.0,
        }
    )


@pytest.fixture
def coordinator_bool() -> MockCoordinator:
    return MockCoordinator(
        data={
            "ns=2;s=EntityMatrix.Test.Node": False,
            "ns=2;s=EntityMatrix.Test.Speed": 10,
        }
    )
