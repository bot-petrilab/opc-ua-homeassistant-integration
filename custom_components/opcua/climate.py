from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CLIMATE_HVAC_MODE_NODE_ID,
    CONF_CLIMATE_MAX_TEMP,
    CONF_CLIMATE_MIN_TEMP,
    CONF_CLIMATE_TEMP_STEP,
    CONF_ENDPOINT,
    CONF_NODE_TARGET_NODE_ID,
    DEFAULT_CLIMATE_MAX_TEMP,
    DEFAULT_CLIMATE_MIN_TEMP,
    DEFAULT_CLIMATE_TEMP_STEP,
    NODE_KIND_CLIMATE,
)
from .entity import OpcUaBaseEntity


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaClimate(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_CLIMATE)
    ]
    async_add_entities(entities)


class OpcUaClimate(OpcUaBaseEntity, ClimateEntity):
    """OPC-UA climate entity."""

    _hvac_modes_supported = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]

    def __init__(
        self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator
    ) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_CLIMATE)
        self._cfg = node_cfg
        self._target_node_id = node_cfg.get(CONF_NODE_TARGET_NODE_ID)
        self._hvac_mode_node_id = node_cfg.get(CONF_CLIMATE_HVAC_MODE_NODE_ID)

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = list(self._hvac_modes_supported)
        self._attr_min_temp = float(
            node_cfg.get(CONF_CLIMATE_MIN_TEMP, DEFAULT_CLIMATE_MIN_TEMP)
        )
        self._attr_max_temp = float(
            node_cfg.get(CONF_CLIMATE_MAX_TEMP, DEFAULT_CLIMATE_MAX_TEMP)
        )
        self._attr_target_temperature_step = float(
            node_cfg.get(CONF_CLIMATE_TEMP_STEP, DEFAULT_CLIMATE_TEMP_STEP)
        )

    @property
    def current_temperature(self) -> float | None:
        return _as_float(self._raw_value())

    @property
    def target_temperature(self) -> float | None:
        if not self._target_node_id:
            return None
        return _as_float(self.coordinator.data.get(self._target_node_id))

    @property
    def hvac_mode(self) -> HVACMode:
        raw = (
            self.coordinator.data.get(self._hvac_mode_node_id)
            if self._hvac_mode_node_id
            else None
        )
        if isinstance(raw, str):
            r = raw.strip().lower()
            for mode in self._hvac_modes_supported:
                if mode.value == r:
                    return mode
        if isinstance(raw, bool):
            return HVACMode.HEAT if raw else HVACMode.OFF
        if isinstance(raw, (int, float)):
            mapped = {
                0: HVACMode.OFF,
                1: HVACMode.HEAT,
                2: HVACMode.COOL,
                3: HVACMode.AUTO,
            }
            return mapped.get(int(raw), HVACMode.HEAT)

        # fallback: infer from target temp presence
        return HVACMode.HEAT if self.target_temperature is not None else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if self._hvac_mode_node_id:
            await self.coordinator.manager.write_node(
                self._hvac_mode_node_id, hvac_mode.value
            )
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if not self._target_node_id:
            return
        value = kwargs.get("temperature")
        if value is None:
            return
        await self.coordinator.manager.write_node(self._target_node_id, float(value))
        await self.coordinator.async_request_refresh()
