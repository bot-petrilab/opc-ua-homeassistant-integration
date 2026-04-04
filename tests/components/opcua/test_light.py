from types import SimpleNamespace

import pytest

from homeassistant.components.light import (
    ATTR_BRIGHTNESS_PCT,
    ATTR_BRIGHTNESS_STEP,
    ATTR_BRIGHTNESS_STEP_PCT,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_RGB_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE,
    ATTR_XY_COLOR,
    ColorMode,
)

from custom_components.opcua import light as light_module
from custom_components.opcua.light import (
    OpcUaLight,
    _as_float,
    _clamp,
    _ha_255_from_scaled,
    _scaled_from_ha_255,
)


def test_light_helper_functions() -> None:
    assert _as_float("1.5") == 1.5
    assert _as_float("bad") is None
    assert _clamp(10, 0, 5) == 5
    assert _ha_255_from_scaled(50, 100) == 128
    assert _ha_255_from_scaled(None, 100) is None
    assert _scaled_from_ha_255(255, 100) == 100
    assert _scaled_from_ha_255(255, 0) == 0.0


def test_light_properties_and_supported_modes(coordinator_all):
    coordinator_all.data.update(
        {
            "ns=2;s=L.On": True,
            "ns=2;s=L.Brightness": 128,
            "ns=2;s=L.ColorTemp": 3200,
            "ns=2;s=L.Hue": 180,
            "ns=2;s=L.Sat": 50,
            "ns=2;s=L.R": 255,
            "ns=2;s=L.G": 128,
            "ns=2;s=L.B": 0,
            "ns=2;s=L.RGBW.R": 255,
            "ns=2;s=L.RGBW.G": 0,
            "ns=2;s=L.RGBW.B": 64,
            "ns=2;s=L.RGBW.W": 32,
            "ns=2;s=L.RGBWW.R": 255,
            "ns=2;s=L.RGBWW.G": 0,
            "ns=2;s=L.RGBWW.B": 64,
            "ns=2;s=L.RGBWW.CW": 32,
            "ns=2;s=L.RGBWW.WW": 16,
            "ns=2;s=L.X": 0.25,
            "ns=2;s=L.Y": 0.5,
            "ns=2;s=L.White": 100,
            "ns=2;s=L.Effect": "pulse",
        }
    )
    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=L.On",
            "brightness_node_id": "ns=2;s=L.Brightness",
            "brightness_scale": 255,
            "color_temp_node_id": "ns=2;s=L.ColorTemp",
            "hs_hue_node_id": "ns=2;s=L.Hue",
            "hs_hue_scale": 360,
            "hs_saturation_node_id": "ns=2;s=L.Sat",
            "hs_saturation_scale": 100,
            "rgb_r_node_id": "ns=2;s=L.R",
            "rgb_g_node_id": "ns=2;s=L.G",
            "rgb_b_node_id": "ns=2;s=L.B",
            "rgbw_r_node_id": "ns=2;s=L.RGBW.R",
            "rgbw_g_node_id": "ns=2;s=L.RGBW.G",
            "rgbw_b_node_id": "ns=2;s=L.RGBW.B",
            "rgbw_w_node_id": "ns=2;s=L.RGBW.W",
            "rgbww_r_node_id": "ns=2;s=L.RGBWW.R",
            "rgbww_g_node_id": "ns=2;s=L.RGBWW.G",
            "rgbww_b_node_id": "ns=2;s=L.RGBWW.B",
            "rgbww_cw_node_id": "ns=2;s=L.RGBWW.CW",
            "rgbww_ww_node_id": "ns=2;s=L.RGBWW.WW",
            "xy_x_node_id": "ns=2;s=L.X",
            "xy_y_node_id": "ns=2;s=L.Y",
            "xy_scale": 1,
            "white_node_id": "ns=2;s=L.White",
            "white_scale": 255,
            "effect_node_id": "ns=2;s=L.Effect",
            "effect_list": ["off", "pulse"],
            "transition_node_id": "ns=2;s=L.Transition",
            "flash_node_id": "ns=2;s=L.Flash",
        },
        coordinator_all,
    )

    assert e.is_on is True
    assert e.brightness == 128
    assert e.color_temp_kelvin == 3200
    assert e.hs_color == (180.0, 50.0)
    assert e.rgb_color == (255, 128, 0)
    assert e.rgbw_color == (255, 0, 64, 32)
    assert e.rgbww_color == (255, 0, 64, 32, 16)
    assert e.xy_color == (0.25, 0.5)
    assert e.effect == "pulse"
    assert e._attr_supported_color_modes == {ColorMode.RGBWW}
    assert e._attr_has_entity_name is True


def test_light_invert_and_scaled_write_value_preserves_numeric_types(coordinator_all, coordinator_factory):
    coordinator_all.data.update({"ns=2;s=Inv.On": False, "ns=2;s=Inv.Brightness": 10})
    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "Inv",
            "node_id": "ns=2;s=Inv.On",
            "invert": True,
            "brightness_node_id": "ns=2;s=Inv.Brightness",
            "brightness_scale": 100,
        },
        coordinator_all,
    )
    assert e.is_on is True
    assert e._scaled_write_value("brightness_node_id", 128, 100) == 50

    coord_bool = coordinator_factory({"ns=2;s=Bri": True})
    e_bool = OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {"name": "L", "node_id": "ns=2;s=On", "brightness_node_id": "ns=2;s=Bri", "brightness_scale": 100}, coord_bool)
    assert e_bool._scaled_write_value("brightness_node_id", 128, 100) == 50

    coord_float = coordinator_factory({"ns=2;s=Bri": 1.5})
    e_float = OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {"name": "L", "node_id": "ns=2;s=On", "brightness_node_id": "ns=2;s=Bri", "brightness_scale": 100}, coord_float)
    assert e_float._scaled_write_value("brightness_node_id", 128, 100) == 50.19607843137255


@pytest.mark.asyncio
async def test_light_turn_on_writes_nodes(coordinator_all):
    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=EntityMatrix.Light.On",
            "brightness_node_id": "ns=2;s=EntityMatrix.Light.Brightness",
            "effect_node_id": "ns=2;s=EntityMatrix.Light.Effect",
            "effect_list": ["off", "pulse"],
        },
        coordinator_all,
    )
    await e.async_turn_on(brightness=180, effect="pulse")
    assert any(
        w[0] == "ns=2;s=EntityMatrix.Light.On" and w[1] is True
        for w in coordinator_all.manager.writes
    )


@pytest.mark.asyncio
async def test_light_turn_on_supports_multiple_color_modes_and_meta_options(coordinator_factory):
    coordinator = coordinator_factory(
        {
            "ns=2;s=Light.On": False,
            "ns=2;s=Light.Brightness": 0,
            "ns=2;s=Light.Hue": 0.0,
            "ns=2;s=Light.Sat": 0.0,
            "ns=2;s=Light.R": 0,
            "ns=2;s=Light.G": 0,
            "ns=2;s=Light.B": 0,
            "ns=2;s=Light.RGBW.R": 0,
            "ns=2;s=Light.RGBW.G": 0,
            "ns=2;s=Light.RGBW.B": 0,
            "ns=2;s=Light.RGBW.W": 0,
            "ns=2;s=Light.RGBWW.R": 0,
            "ns=2;s=Light.RGBWW.G": 0,
            "ns=2;s=Light.RGBWW.B": 0,
            "ns=2;s=Light.RGBWW.CW": 0,
            "ns=2;s=Light.RGBWW.WW": 0,
            "ns=2;s=Light.X": 0.0,
            "ns=2;s=Light.Y": 0.0,
            "ns=2;s=Light.White": 0,
        }
    )
    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=Light.On",
            "brightness_node_id": "ns=2;s=Light.Brightness",
            "brightness_scale": 255,
            "hs_hue_node_id": "ns=2;s=Light.Hue",
            "hs_hue_scale": 360,
            "hs_saturation_node_id": "ns=2;s=Light.Sat",
            "hs_saturation_scale": 100,
            "rgb_r_node_id": "ns=2;s=Light.R",
            "rgb_g_node_id": "ns=2;s=Light.G",
            "rgb_b_node_id": "ns=2;s=Light.B",
            "rgbw_r_node_id": "ns=2;s=Light.RGBW.R",
            "rgbw_g_node_id": "ns=2;s=Light.RGBW.G",
            "rgbw_b_node_id": "ns=2;s=Light.RGBW.B",
            "rgbw_w_node_id": "ns=2;s=Light.RGBW.W",
            "rgbww_r_node_id": "ns=2;s=Light.RGBWW.R",
            "rgbww_g_node_id": "ns=2;s=Light.RGBWW.G",
            "rgbww_b_node_id": "ns=2;s=Light.RGBWW.B",
            "rgbww_cw_node_id": "ns=2;s=Light.RGBWW.CW",
            "rgbww_ww_node_id": "ns=2;s=Light.RGBWW.WW",
            "xy_x_node_id": "ns=2;s=Light.X",
            "xy_y_node_id": "ns=2;s=Light.Y",
            "xy_scale": 1,
            "white_node_id": "ns=2;s=Light.White",
            "white_scale": 255,
            "effect_node_id": "ns=2;s=Light.Effect",
            "transition_node_id": "ns=2;s=Light.Transition",
            "flash_node_id": "ns=2;s=Light.Flash",
        },
        coordinator,
    )

    await e.async_turn_on(**{ATTR_BRIGHTNESS_PCT: 50, ATTR_HS_COLOR: (120, 25), ATTR_TRANSITION: 1.5, ATTR_FLASH: "short"})
    await e.async_turn_on(**{ATTR_RGB_COLOR: (1, 2, 3)})
    await e.async_turn_on(**{ATTR_RGBW_COLOR: (4, 5, 6, 7)})
    await e.async_turn_on(**{ATTR_RGBWW_COLOR: (8, 9, 10, 11, 12)})
    await e.async_turn_on(**{ATTR_XY_COLOR: (0.1, 0.2)})
    await e.async_turn_on(**{ATTR_WHITE: 13})

    writes = dict(coordinator.manager.writes)
    assert writes["ns=2;s=Light.Transition"] == 1.5
    assert writes["ns=2;s=Light.Flash"] == "short"
    assert writes["ns=2;s=Light.Hue"] == 120.0
    assert writes["ns=2;s=Light.Sat"] == 25.0
    assert writes["ns=2;s=Light.R"] == 1
    assert writes["ns=2;s=Light.RGBW.W"] == 7
    assert writes["ns=2;s=Light.RGBWW.WW"] == 12
    assert writes["ns=2;s=Light.X"] == 0.1
    assert writes["ns=2;s=Light.White"] == 13
    assert coordinator.refresh_count >= 1


@pytest.mark.asyncio
async def test_light_async_setup_entry_creates_entity() -> None:
    class _Coordinator:
        def nodes_by_kind(self, kind):
            assert kind == "light"
            return [{"name": "L", "node_id": "ns=2;s=L"}]

    entry = SimpleNamespace(
        entry_id="entry-1",
        data={"endpoint": "opc.tcp://127.0.0.1:4846"},
        runtime_data=SimpleNamespace(coordinator=_Coordinator()),
    )
    collected = []
    await light_module.async_setup_entry(SimpleNamespace(), entry, lambda ents: collected.extend(list(ents)))
    assert len(collected) == 1
    assert isinstance(collected[0], OpcUaLight)


def test_light_mode_selection_and_empty_property_paths(coordinator_factory):
    coord = coordinator_factory({"ns=2;s=On": True})
    base = {"name": "L", "node_id": "ns=2;s=On"}

    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "rgbw_r_node_id": "r", "rgbw_w_node_id": "w"}, coord)._attr_supported_color_modes == {ColorMode.RGBW}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "rgb_r_node_id": "r", "rgb_b_node_id": "b"}, coord)._attr_supported_color_modes == {ColorMode.RGB}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "hs_hue_node_id": "h", "hs_saturation_node_id": "s"}, coord)._attr_supported_color_modes == {ColorMode.HS}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "xy_x_node_id": "x", "xy_y_node_id": "y"}, coord)._attr_supported_color_modes == {ColorMode.XY}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "color_temp_node_id": "ct"}, coord)._attr_supported_color_modes == {ColorMode.COLOR_TEMP}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "white_node_id": "w"}, coord)._attr_supported_color_modes == {ColorMode.WHITE}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", {**base, "brightness_node_id": "bri"}, coord)._attr_supported_color_modes == {ColorMode.BRIGHTNESS}
    assert OpcUaLight("e", "opc.tcp://127.0.0.1:4846", base, coord)._attr_supported_color_modes == {ColorMode.ONOFF}

    empty = OpcUaLight("e", "opc.tcp://127.0.0.1:4846", base, coord)
    assert empty._node_value("missing") is None
    assert empty.color_mode == ColorMode.ONOFF
    assert empty.color_temp_kelvin is None
    assert empty.hs_color is None
    assert empty.rgb_color is None
    assert empty.rgbw_color is None
    assert empty.rgbww_color is None
    assert empty.xy_color is None
    assert empty.effect is None
    coord_none = coordinator_factory({})
    none_state = OpcUaLight("e", "opc.tcp://127.0.0.1:4846", base, coord_none)
    assert none_state.is_on is None


@pytest.mark.asyncio
async def test_light_turn_on_brightness_step_color_temp_and_effect_paths(coordinator_factory):
    coordinator = coordinator_factory(
        {
            "ns=2;s=Light.On": False,
            "ns=2;s=Light.Brightness": 10,
            "ns=2;s=Light.ColorTemp": 3000,
            "ns=2;s=Light.Effect": "off",
        }
    )
    e_brightness = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=Light.On",
            "brightness_node_id": "ns=2;s=Light.Brightness",
            "brightness_scale": 255,
        },
        coordinator,
    )
    await e_brightness.async_turn_on(**{ATTR_BRIGHTNESS_STEP: 20})
    assert e_brightness.color_mode == ColorMode.BRIGHTNESS
    await e_brightness.async_turn_on(**{ATTR_BRIGHTNESS_STEP_PCT: 10})

    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=Light.On",
            "brightness_node_id": "ns=2;s=Light.Brightness",
            "brightness_scale": 255,
            "color_temp_node_id": "ns=2;s=Light.ColorTemp",
            "color_temp_min_kelvin": 2000,
            "color_temp_max_kelvin": 4000,
            "effect_node_id": "ns=2;s=Light.Effect",
        },
        coordinator,
    )
    await e.async_turn_on(**{ATTR_COLOR_TEMP_KELVIN: 9999})
    await e.async_turn_on(**{ATTR_EFFECT: "pulse"})

    writes = coordinator.manager.writes
    assert ("ns=2;s=Light.Brightness", 30) in writes
    assert any(node == "ns=2;s=Light.Brightness" and isinstance(val, int) for node, val in writes)
    assert ("ns=2;s=Light.ColorTemp", 4000) in writes
    assert ("ns=2;s=Light.Effect", "pulse") in writes
    assert e.color_mode == ColorMode.COLOR_TEMP


@pytest.mark.asyncio
async def test_light_turn_off_respects_invert_and_meta_options(coordinator_factory):
    coordinator = coordinator_factory({"ns=2;s=Light.On": True})
    e = OpcUaLight(
        "e",
        "opc.tcp://127.0.0.1:4846",
        {
            "name": "L",
            "node_id": "ns=2;s=Light.On",
            "invert": True,
            "transition_node_id": "ns=2;s=Light.Transition",
            "flash_node_id": "ns=2;s=Light.Flash",
        },
        coordinator,
    )
    await e.async_turn_off(**{ATTR_TRANSITION: 2, ATTR_FLASH: "long"})
    assert coordinator.manager.writes[0] == ("ns=2;s=Light.Transition", 2.0)
    assert coordinator.manager.writes[1] == ("ns=2;s=Light.Flash", "long")
    assert coordinator.manager.writes[2] == ("ns=2;s=Light.On", True)
    assert coordinator.refresh_count == 1
