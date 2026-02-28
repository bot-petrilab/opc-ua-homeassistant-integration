from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_BRIGHTNESS_STEP,
    ATTR_BRIGHTNESS_STEP_PCT,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE,
    ATTR_XY_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ENDPOINT,
    CONF_LIGHT_BRIGHTNESS_NODE_ID,
    CONF_LIGHT_BRIGHTNESS_SCALE,
    CONF_LIGHT_COLOR_TEMP_MAX_KELVIN,
    CONF_LIGHT_COLOR_TEMP_MIN_KELVIN,
    CONF_LIGHT_COLOR_TEMP_NODE_ID,
    CONF_LIGHT_EFFECT_LIST,
    CONF_LIGHT_EFFECT_NODE_ID,
    CONF_LIGHT_FLASH_NODE_ID,
    CONF_LIGHT_HS_HUE_NODE_ID,
    CONF_LIGHT_HS_HUE_SCALE,
    CONF_LIGHT_HS_SAT_NODE_ID,
    CONF_LIGHT_HS_SAT_SCALE,
    CONF_LIGHT_RGB_B_NODE_ID,
    CONF_LIGHT_RGB_G_NODE_ID,
    CONF_LIGHT_RGB_R_NODE_ID,
    CONF_LIGHT_RGB_SCALE,
    CONF_LIGHT_RGBW_B_NODE_ID,
    CONF_LIGHT_RGBW_G_NODE_ID,
    CONF_LIGHT_RGBW_R_NODE_ID,
    CONF_LIGHT_RGBW_W_NODE_ID,
    CONF_LIGHT_RGBWW_B_NODE_ID,
    CONF_LIGHT_RGBWW_CW_NODE_ID,
    CONF_LIGHT_RGBWW_G_NODE_ID,
    CONF_LIGHT_RGBWW_R_NODE_ID,
    CONF_LIGHT_RGBWW_WW_NODE_ID,
    CONF_LIGHT_TRANSITION_NODE_ID,
    CONF_LIGHT_WHITE_NODE_ID,
    CONF_LIGHT_WHITE_SCALE,
    CONF_LIGHT_XY_SCALE,
    CONF_LIGHT_XY_X_NODE_ID,
    CONF_LIGHT_XY_Y_NODE_ID,
    CONF_NODE_INVERT,
    DEFAULT_BRIGHTNESS_SCALE,
    DEFAULT_COLOR_TEMP_MAX_KELVIN,
    DEFAULT_COLOR_TEMP_MIN_KELVIN,
    DEFAULT_HS_HUE_SCALE,
    DEFAULT_HS_SAT_SCALE,
    DEFAULT_RGB_SCALE,
    DEFAULT_WHITE_SCALE,
    DEFAULT_XY_SCALE,
    NODE_KIND_LIGHT,
)
from .entity import OpcUaBaseEntity


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _ha_255_from_scaled(raw: Any, scale: float) -> int | None:
    value = _as_float(raw)
    if value is None or scale <= 0:
        return None
    return int(round(_clamp(value, 0, scale) / scale * 255.0))


def _scaled_from_ha_255(brightness_255: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return _clamp(float(brightness_255), 0.0, 255.0) / 255.0 * scale


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    endpoint = entry.data[CONF_ENDPOINT]
    entities = [
        OpcUaLight(entry.entry_id, endpoint, node_cfg, coordinator)
        for node_cfg in coordinator.nodes_by_kind(NODE_KIND_LIGHT)
    ]
    async_add_entities(entities)


class OpcUaLight(OpcUaBaseEntity, LightEntity):
    """Advanced OPC UA Light entity (all common optional HA light features)."""

    def __init__(self, entry_id: str, endpoint: str, node_cfg: dict[str, Any], coordinator) -> None:
        super().__init__(entry_id, endpoint, node_cfg, coordinator, NODE_KIND_LIGHT)
        self._cfg = node_cfg
        self._invert = bool(node_cfg.get(CONF_NODE_INVERT, False))

        self._brightness_scale = float(node_cfg.get(CONF_LIGHT_BRIGHTNESS_SCALE, DEFAULT_BRIGHTNESS_SCALE))
        self._rgb_scale = float(node_cfg.get(CONF_LIGHT_RGB_SCALE, DEFAULT_RGB_SCALE))
        self._white_scale = float(node_cfg.get(CONF_LIGHT_WHITE_SCALE, DEFAULT_WHITE_SCALE))
        self._hs_hue_scale = float(node_cfg.get(CONF_LIGHT_HS_HUE_SCALE, DEFAULT_HS_HUE_SCALE))
        self._hs_sat_scale = float(node_cfg.get(CONF_LIGHT_HS_SAT_SCALE, DEFAULT_HS_SAT_SCALE))
        self._xy_scale = float(node_cfg.get(CONF_LIGHT_XY_SCALE, DEFAULT_XY_SCALE))

        self._attr_min_color_temp_kelvin = int(
            node_cfg.get(CONF_LIGHT_COLOR_TEMP_MIN_KELVIN, DEFAULT_COLOR_TEMP_MIN_KELVIN)
        )
        self._attr_max_color_temp_kelvin = int(
            node_cfg.get(CONF_LIGHT_COLOR_TEMP_MAX_KELVIN, DEFAULT_COLOR_TEMP_MAX_KELVIN)
        )

        self._effect_list: list[str] = list(node_cfg.get(CONF_LIGHT_EFFECT_LIST, []))
        if self._effect_list:
            self._attr_effect_list = self._effect_list

        features = LightEntityFeature(0)
        if node_cfg.get(CONF_LIGHT_EFFECT_NODE_ID):
            features |= LightEntityFeature.EFFECT
        if node_cfg.get(CONF_LIGHT_TRANSITION_NODE_ID):
            features |= LightEntityFeature.TRANSITION
        if node_cfg.get(CONF_LIGHT_FLASH_NODE_ID):
            features |= LightEntityFeature.FLASH
        self._attr_supported_features = features

        supported: set[ColorMode] = set()
        if node_cfg.get(CONF_LIGHT_RGBWW_R_NODE_ID) and node_cfg.get(CONF_LIGHT_RGBWW_WW_NODE_ID):
            supported.add(ColorMode.RGBWW)
        if node_cfg.get(CONF_LIGHT_RGBW_R_NODE_ID) and node_cfg.get(CONF_LIGHT_RGBW_W_NODE_ID):
            supported.add(ColorMode.RGBW)
        if node_cfg.get(CONF_LIGHT_RGB_R_NODE_ID) and node_cfg.get(CONF_LIGHT_RGB_B_NODE_ID):
            supported.add(ColorMode.RGB)
        if node_cfg.get(CONF_LIGHT_HS_HUE_NODE_ID) and node_cfg.get(CONF_LIGHT_HS_SAT_NODE_ID):
            supported.add(ColorMode.HS)
        if node_cfg.get(CONF_LIGHT_XY_X_NODE_ID) and node_cfg.get(CONF_LIGHT_XY_Y_NODE_ID):
            supported.add(ColorMode.XY)
        if node_cfg.get(CONF_LIGHT_COLOR_TEMP_NODE_ID):
            supported.add(ColorMode.COLOR_TEMP)
        if node_cfg.get(CONF_LIGHT_WHITE_NODE_ID):
            supported.add(ColorMode.WHITE)
        if node_cfg.get(CONF_LIGHT_BRIGHTNESS_NODE_ID):
            supported.add(ColorMode.BRIGHTNESS)
        if not supported:
            supported.add(ColorMode.ONOFF)

        self._attr_supported_color_modes = supported
        self._last_color_mode: ColorMode = next(iter(supported))

    def _node_value(self, key: str) -> Any:
        node_id = self._cfg.get(key)
        if not node_id:
            return None
        return self.coordinator.data.get(node_id)

    @property
    def is_on(self) -> bool | None:
        raw = self._raw_value()
        if raw is None:
            return None
        state = bool(raw)
        return (not state) if self._invert else state

    @property
    def color_mode(self) -> ColorMode | None:
        return self._last_color_mode

    @property
    def brightness(self) -> int | None:
        raw = self._node_value(CONF_LIGHT_BRIGHTNESS_NODE_ID)
        return _ha_255_from_scaled(raw, self._brightness_scale)

    @property
    def color_temp_kelvin(self) -> int | None:
        value = _as_float(self._node_value(CONF_LIGHT_COLOR_TEMP_NODE_ID))
        if value is None:
            return None
        return int(round(value))

    @property
    def hs_color(self) -> tuple[float, float] | None:
        hue_raw = _as_float(self._node_value(CONF_LIGHT_HS_HUE_NODE_ID))
        sat_raw = _as_float(self._node_value(CONF_LIGHT_HS_SAT_NODE_ID))
        if hue_raw is None or sat_raw is None:
            return None
        hue = _clamp(hue_raw / max(self._hs_hue_scale, 1e-6) * 360.0, 0.0, 360.0)
        sat = _clamp(sat_raw / max(self._hs_sat_scale, 1e-6) * 100.0, 0.0, 100.0)
        return (hue, sat)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        vals = [
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGB_R_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGB_G_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGB_B_NODE_ID), self._rgb_scale),
        ]
        if any(v is None for v in vals):
            return None
        return (vals[0], vals[1], vals[2])

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        vals = [
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBW_R_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBW_G_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBW_B_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBW_W_NODE_ID), self._white_scale),
        ]
        if any(v is None for v in vals):
            return None
        return (vals[0], vals[1], vals[2], vals[3])

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        vals = [
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBWW_R_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBWW_G_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBWW_B_NODE_ID), self._rgb_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBWW_CW_NODE_ID), self._white_scale),
            _ha_255_from_scaled(self._node_value(CONF_LIGHT_RGBWW_WW_NODE_ID), self._white_scale),
        ]
        if any(v is None for v in vals):
            return None
        return (vals[0], vals[1], vals[2], vals[3], vals[4])

    @property
    def xy_color(self) -> tuple[float, float] | None:
        x_raw = _as_float(self._node_value(CONF_LIGHT_XY_X_NODE_ID))
        y_raw = _as_float(self._node_value(CONF_LIGHT_XY_Y_NODE_ID))
        if x_raw is None or y_raw is None:
            return None
        scale = max(self._xy_scale, 1e-6)
        return (_clamp(x_raw / scale, 0.0, 1.0), _clamp(y_raw / scale, 0.0, 1.0))

    @property
    def effect(self) -> str | None:
        raw = self._node_value(CONF_LIGHT_EFFECT_NODE_ID)
        if raw is None:
            return None
        return str(raw)

    async def _write_if_configured(self, key: str, value: Any) -> None:
        node_id = self._cfg.get(key)
        if node_id:
            await self.coordinator.manager.write_node(node_id, value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        # Meta options
        if ATTR_TRANSITION in kwargs:
            await self._write_if_configured(CONF_LIGHT_TRANSITION_NODE_ID, float(kwargs[ATTR_TRANSITION]))
        if ATTR_FLASH in kwargs:
            await self._write_if_configured(CONF_LIGHT_FLASH_NODE_ID, str(kwargs[ATTR_FLASH]))

        # Brightness family
        target_brightness = kwargs.get(ATTR_BRIGHTNESS)
        if target_brightness is None and ATTR_BRIGHTNESS_PCT in kwargs:
            target_brightness = int(round(float(kwargs[ATTR_BRIGHTNESS_PCT]) / 100.0 * 255.0))

        current_brightness = self.brightness if self.brightness is not None else 0
        if ATTR_BRIGHTNESS_STEP in kwargs:
            target_brightness = int(_clamp(current_brightness + int(kwargs[ATTR_BRIGHTNESS_STEP]), 0, 255))
        if ATTR_BRIGHTNESS_STEP_PCT in kwargs:
            step = float(kwargs[ATTR_BRIGHTNESS_STEP_PCT]) / 100.0 * 255.0
            target_brightness = int(_clamp(current_brightness + step, 0, 255))

        if target_brightness is not None and self._cfg.get(CONF_LIGHT_BRIGHTNESS_NODE_ID):
            await self._write_if_configured(
                CONF_LIGHT_BRIGHTNESS_NODE_ID,
                _scaled_from_ha_255(target_brightness, self._brightness_scale),
            )
            if ColorMode.BRIGHTNESS in self.supported_color_modes:
                self._last_color_mode = ColorMode.BRIGHTNESS

        # Color temp
        if ATTR_COLOR_TEMP_KELVIN in kwargs and self._cfg.get(CONF_LIGHT_COLOR_TEMP_NODE_ID):
            temp = int(kwargs[ATTR_COLOR_TEMP_KELVIN])
            temp = int(_clamp(temp, self.min_color_temp_kelvin, self.max_color_temp_kelvin))
            await self._write_if_configured(CONF_LIGHT_COLOR_TEMP_NODE_ID, temp)
            self._last_color_mode = ColorMode.COLOR_TEMP

        # HS
        if ATTR_HS_COLOR in kwargs:
            hs = kwargs[ATTR_HS_COLOR]
            if (
                isinstance(hs, (tuple, list))
                and len(hs) == 2
                and self._cfg.get(CONF_LIGHT_HS_HUE_NODE_ID)
                and self._cfg.get(CONF_LIGHT_HS_SAT_NODE_ID)
            ):
                hue = _clamp(float(hs[0]), 0.0, 360.0)
                sat = _clamp(float(hs[1]), 0.0, 100.0)
                await self._write_if_configured(
                    CONF_LIGHT_HS_HUE_NODE_ID,
                    hue / 360.0 * self._hs_hue_scale,
                )
                await self._write_if_configured(
                    CONF_LIGHT_HS_SAT_NODE_ID,
                    sat / 100.0 * self._hs_sat_scale,
                )
                self._last_color_mode = ColorMode.HS

        # RGB
        if ATTR_RGB_COLOR in kwargs and all(
            self._cfg.get(k)
            for k in [CONF_LIGHT_RGB_R_NODE_ID, CONF_LIGHT_RGB_G_NODE_ID, CONF_LIGHT_RGB_B_NODE_ID]
        ):
            r, g, b = kwargs[ATTR_RGB_COLOR]
            await self._write_if_configured(CONF_LIGHT_RGB_R_NODE_ID, _scaled_from_ha_255(r, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGB_G_NODE_ID, _scaled_from_ha_255(g, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGB_B_NODE_ID, _scaled_from_ha_255(b, self._rgb_scale))
            self._last_color_mode = ColorMode.RGB

        # RGBW
        if ATTR_RGBW_COLOR in kwargs and all(
            self._cfg.get(k)
            for k in [
                CONF_LIGHT_RGBW_R_NODE_ID,
                CONF_LIGHT_RGBW_G_NODE_ID,
                CONF_LIGHT_RGBW_B_NODE_ID,
                CONF_LIGHT_RGBW_W_NODE_ID,
            ]
        ):
            r, g, b, w = kwargs[ATTR_RGBW_COLOR]
            await self._write_if_configured(CONF_LIGHT_RGBW_R_NODE_ID, _scaled_from_ha_255(r, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBW_G_NODE_ID, _scaled_from_ha_255(g, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBW_B_NODE_ID, _scaled_from_ha_255(b, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBW_W_NODE_ID, _scaled_from_ha_255(w, self._white_scale))
            self._last_color_mode = ColorMode.RGBW

        # RGBWW
        if ATTR_RGBWW_COLOR in kwargs and all(
            self._cfg.get(k)
            for k in [
                CONF_LIGHT_RGBWW_R_NODE_ID,
                CONF_LIGHT_RGBWW_G_NODE_ID,
                CONF_LIGHT_RGBWW_B_NODE_ID,
                CONF_LIGHT_RGBWW_CW_NODE_ID,
                CONF_LIGHT_RGBWW_WW_NODE_ID,
            ]
        ):
            r, g, b, cw, ww = kwargs[ATTR_RGBWW_COLOR]
            await self._write_if_configured(CONF_LIGHT_RGBWW_R_NODE_ID, _scaled_from_ha_255(r, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBWW_G_NODE_ID, _scaled_from_ha_255(g, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBWW_B_NODE_ID, _scaled_from_ha_255(b, self._rgb_scale))
            await self._write_if_configured(CONF_LIGHT_RGBWW_CW_NODE_ID, _scaled_from_ha_255(cw, self._white_scale))
            await self._write_if_configured(CONF_LIGHT_RGBWW_WW_NODE_ID, _scaled_from_ha_255(ww, self._white_scale))
            self._last_color_mode = ColorMode.RGBWW

        # XY
        if ATTR_XY_COLOR in kwargs and all(
            self._cfg.get(k) for k in [CONF_LIGHT_XY_X_NODE_ID, CONF_LIGHT_XY_Y_NODE_ID]
        ):
            x, y = kwargs[ATTR_XY_COLOR]
            await self._write_if_configured(CONF_LIGHT_XY_X_NODE_ID, _clamp(float(x), 0.0, 1.0) * self._xy_scale)
            await self._write_if_configured(CONF_LIGHT_XY_Y_NODE_ID, _clamp(float(y), 0.0, 1.0) * self._xy_scale)
            self._last_color_mode = ColorMode.XY

        # White
        if ATTR_WHITE in kwargs and self._cfg.get(CONF_LIGHT_WHITE_NODE_ID):
            await self._write_if_configured(
                CONF_LIGHT_WHITE_NODE_ID,
                _scaled_from_ha_255(float(kwargs[ATTR_WHITE]), self._white_scale),
            )
            self._last_color_mode = ColorMode.WHITE

        # Effect
        if ATTR_EFFECT in kwargs and self._cfg.get(CONF_LIGHT_EFFECT_NODE_ID):
            await self._write_if_configured(CONF_LIGHT_EFFECT_NODE_ID, str(kwargs[ATTR_EFFECT]))

        # Finally switch on
        raw_target = False if self._invert else True
        await self.coordinator.manager.write_node(self._node_id, raw_target)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if ATTR_TRANSITION in kwargs:
            await self._write_if_configured(CONF_LIGHT_TRANSITION_NODE_ID, float(kwargs[ATTR_TRANSITION]))
        if ATTR_FLASH in kwargs:
            await self._write_if_configured(CONF_LIGHT_FLASH_NODE_ID, str(kwargs[ATTR_FLASH]))

        raw_target = True if self._invert else False
        await self.coordinator.manager.write_node(self._node_id, raw_target)
        await self.coordinator.async_request_refresh()
