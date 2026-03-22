from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.opcua import binary_sensor, button, climate, cover, date, datetime as dt_mod, fan, light, notify, number, scene, select, sensor, switch, text, time as time_mod, weather
from custom_components.opcua.entity import OpcUaBaseEntity


class _Collector:
    def __init__(self) -> None:
        self.entities = []

    def __call__(self, entities) -> None:
        self.entities.extend(list(entities))


class _Coordinator:
    def __init__(self, by_kind, data=None) -> None:
        self._by_kind = by_kind
        self.data = data or {}
        self.last_update_success = True
        self.manager = SimpleNamespace()

    def nodes_by_kind(self, kind):
        return list(self._by_kind.get(kind, []))


def _entry_for_kind(kind: str, node_cfg: dict, data=None):
    coordinator = _Coordinator({kind: [node_cfg]}, data=data or {node_cfg["node_id"]: True})
    runtime = SimpleNamespace(coordinator=coordinator)
    return SimpleNamespace(entry_id="entry-1", data={"endpoint": "opc.tcp://127.0.0.1:4840"}, runtime_data=runtime), coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_creates_entities_for_all_platforms() -> None:
    cases = [
        (sensor, "sensor", {"name": "S", "node_id": "ns=2;s=S"}, sensor.OpcUaSensor),
        (binary_sensor, "binary_sensor", {"name": "BS", "node_id": "ns=2;s=BS"}, binary_sensor.OpcUaBinarySensor),
        (switch, "switch", {"name": "SW", "node_id": "ns=2;s=SW"}, switch.OpcUaSwitch),
        (button, "button", {"name": "BTN", "node_id": "ns=2;s=BTN"}, button.OpcUaButton),
        (number, "number", {"name": "N", "node_id": "ns=2;s=N"}, number.OpcUaNumber),
        (scene, "scene", {"name": "SC", "node_id": "ns=2;s=SC"}, scene.OpcUaScene),
        (select, "select", {"name": "SEL", "node_id": "ns=2;s=SEL", "select_options": ["A"]}, select.OpcUaSelect),
        (text, "text", {"name": "TXT", "node_id": "ns=2;s=TXT"}, text.OpcUaText),
        (date, "date", {"name": "D", "node_id": "ns=2;s=D"}, date.OpcUaDate),
        (dt_mod, "datetime", {"name": "DT", "node_id": "ns=2;s=DT"}, dt_mod.OpcUaDateTime),
        (time_mod, "time", {"name": "T", "node_id": "ns=2;s=T"}, time_mod.OpcUaTime),
        (fan, "fan", {"name": "F", "node_id": "ns=2;s=F"}, fan.OpcUaFan),
        (notify, "notify", {"name": "NO", "node_id": "ns=2;s=NO"}, notify.OpcUaNotifyEntity),
        (weather, "weather", {"name": "W", "node_id": "ns=2;s=W"}, weather.OpcUaWeather),
        (climate, "climate", {"name": "C", "node_id": "ns=2;s=C"}, climate.OpcUaClimate),
        (cover, "cover", {"name": "CV", "node_id": "ns=2;s=CV"}, cover.OpcUaCover),
        (light, "light", {"name": "L", "node_id": "ns=2;s=L"}, light.OpcUaLight),
    ]

    for module, kind, node_cfg, klass in cases:
        entry, _ = _entry_for_kind(kind, node_cfg)
        collector = _Collector()
        await module.async_setup_entry(SimpleNamespace(), entry, collector)
        assert len(collector.entities) == 1
        assert isinstance(collector.entities[0], klass)


def test_base_entity_attributes_availability_and_device_info(coordinator_factory) -> None:
    coordinator = coordinator_factory({"ns=2;s=Node": 1})
    node_cfg = {
        "name": "Node",
        "node_id": "ns=2;s=Node",
        "icon": "mdi:test-tube",
        "device_id": "dev-1",
        "device_name": "Device 1",
        "device_manufacturer": "Acme",
        "device_model": "Model X",
        "device_serial": "SN123",
    }
    entity = OpcUaBaseEntity("entry-1", "opc.tcp://127.0.0.1:4840", node_cfg, coordinator, "sensor")

    assert entity.available is True
    assert entity._attr_unique_id == "entry-1:sensor:ns=2;s=Node"
    assert entity._attr_extra_state_attributes["endpoint"] == "opc.tcp://127.0.0.1:4840"
    assert entity._raw_value() == 1

    info = entity.device_info
    assert info is not None
    assert info["name"] == "Device 1"
    assert info["manufacturer"] == "Acme"
    assert info["model"] == "Model X"
    assert info["serial_number"] == "SN123"

    coordinator.last_update_success = False
    assert entity.available is False


def test_base_entity_device_info_optional_fields(coordinator_factory) -> None:
    coordinator = coordinator_factory({})
    entity = OpcUaBaseEntity(
        "entry-1",
        "opc.tcp://127.0.0.1:4840",
        {"name": "Node", "node_id": "ns=2;s=Node"},
        coordinator,
        "sensor",
    )
    assert entity.device_info is None
