from __future__ import annotations

from typing import Any

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_WEATHER_CONDITION_NODE_ID,
    CONF_WEATHER_HUMIDITY_NODE_ID,
    CONF_WEATHER_PRESSURE_NODE_ID,
    CONF_WEATHER_WIND_SPEED_NODE_ID,
    NODE_KIND_WEATHER,
)
from .entity import OpcUaBaseEntity


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaWeather(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_WEATHER)
    ]
    async_add_entities(entities)


class OpcUaWeather(OpcUaBaseEntity, WeatherEntity):
    """OPC-UA weather entity."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_WEATHER)
        self._cfg = node_cfg
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    @property
    def native_temperature(self) -> float | None:
        return _as_float(self._raw_value())

    @property
    def humidity(self) -> float | None:
        node_id = self._cfg.get(CONF_WEATHER_HUMIDITY_NODE_ID)
        if not node_id:
            return None
        return _as_float(self.coordinator.data.get(node_id))

    @property
    def native_pressure(self) -> float | None:
        node_id = self._cfg.get(CONF_WEATHER_PRESSURE_NODE_ID)
        if not node_id:
            return None
        return _as_float(self.coordinator.data.get(node_id))

    @property
    def native_wind_speed(self) -> float | None:
        node_id = self._cfg.get(CONF_WEATHER_WIND_SPEED_NODE_ID)
        if not node_id:
            return None
        return _as_float(self.coordinator.data.get(node_id))

    @property
    def condition(self) -> str | None:
        node_id = self._cfg.get(CONF_WEATHER_CONDITION_NODE_ID)
        if not node_id:
            return None
        raw = self.coordinator.data.get(node_id)
        if raw is None:
            return None
        return str(raw).strip().lower() or None
