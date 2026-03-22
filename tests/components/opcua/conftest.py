from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntFlag
import sys
import types
from typing import Any

import pytest


def _ensure_module(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


def _install_homeassistant_stubs() -> None:
    _ensure_module("homeassistant")

    # homeassistant.const
    const_mod = _ensure_module("homeassistant.const")

    class Platform(str, Enum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"
        LIGHT = "light"
        BUTTON = "button"
        CLIMATE = "climate"
        COVER = "cover"
        DATE = "date"
        DATETIME = "datetime"
        FAN = "fan"
        NOTIFY = "notify"
        NUMBER = "number"
        SCENE = "scene"
        SELECT = "select"
        TEXT = "text"
        TIME = "time"
        WEATHER = "weather"

    class UnitOfTemperature(str, Enum):
        CELSIUS = "°C"

    class UnitOfPressure(str, Enum):
        HPA = "hPa"

    class UnitOfSpeed(str, Enum):
        METERS_PER_SECOND = "m/s"

    const_mod.Platform = Platform
    const_mod.UnitOfTemperature = UnitOfTemperature
    const_mod.UnitOfPressure = UnitOfPressure
    const_mod.UnitOfSpeed = UnitOfSpeed
    const_mod.CONF_PASSWORD = "password"
    const_mod.CONF_USERNAME = "username"

    # homeassistant.config_entries
    ce_mod = _ensure_module("homeassistant.config_entries")

    class ConfigEntry:  # minimal generic-like placeholder
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    ce_mod.ConfigEntry = ConfigEntry

    # homeassistant.core
    core_mod = _ensure_module("homeassistant.core")

    class HomeAssistant:
        pass

    core_mod.HomeAssistant = HomeAssistant

    # homeassistant.exceptions
    ex_mod = _ensure_module("homeassistant.exceptions")

    class ConfigEntryNotReady(Exception):
        pass

    class ConfigEntryAuthFailed(Exception):
        pass

    ex_mod.ConfigEntryNotReady = ConfigEntryNotReady
    ex_mod.ConfigEntryAuthFailed = ConfigEntryAuthFailed

    # helpers
    _ensure_module("homeassistant.helpers")
    _ensure_module("homeassistant.helpers.entity_platform").AddEntitiesCallback = object

    dr_mod = _ensure_module("homeassistant.helpers.device_registry")

    @dataclass
    class DeviceInfo:
        identifiers: set[tuple[str, str]]
        name: str
        manufacturer: str
        model: str

    dr_mod.DeviceInfo = DeviceInfo

    uc_mod = _ensure_module("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __init__(self, *args, **kwargs):
            self.data = {}
            self.last_update_success = True

        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    class UpdateFailed(Exception):
        pass

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    uc_mod.DataUpdateCoordinator = DataUpdateCoordinator
    uc_mod.UpdateFailed = UpdateFailed
    uc_mod.CoordinatorEntity = CoordinatorEntity

    # Component base classes
    _ensure_module("homeassistant.components")

    _ensure_module("homeassistant.components.sensor").SensorEntity = object
    _ensure_module("homeassistant.components.binary_sensor").BinarySensorEntity = object
    _ensure_module("homeassistant.components.switch").SwitchEntity = object
    _ensure_module("homeassistant.components.button").ButtonEntity = object
    _ensure_module("homeassistant.components.number").NumberEntity = object
    _ensure_module("homeassistant.components.scene").Scene = object
    _ensure_module("homeassistant.components.select").SelectEntity = object
    _ensure_module("homeassistant.components.text").TextEntity = object
    _ensure_module("homeassistant.components.date").DateEntity = object
    _ensure_module("homeassistant.components.datetime").DateTimeEntity = object
    _ensure_module("homeassistant.components.time").TimeEntity = object
    _ensure_module("homeassistant.components.notify").NotifyEntity = object
    _ensure_module("homeassistant.components.weather").WeatherEntity = object

    # Light
    light_mod = _ensure_module("homeassistant.components.light")

    class ColorMode(str, Enum):
        ONOFF = "onoff"
        BRIGHTNESS = "brightness"
        COLOR_TEMP = "color_temp"
        HS = "hs"
        RGB = "rgb"
        RGBW = "rgbw"
        RGBWW = "rgbww"
        XY = "xy"
        WHITE = "white"

    class LightEntityFeature(IntFlag):
        EFFECT = 1
        FLASH = 2
        TRANSITION = 4

    light_mod.LightEntity = object
    light_mod.ColorMode = ColorMode
    light_mod.LightEntityFeature = LightEntityFeature
    for attr in [
        "ATTR_BRIGHTNESS",
        "ATTR_BRIGHTNESS_PCT",
        "ATTR_BRIGHTNESS_STEP",
        "ATTR_BRIGHTNESS_STEP_PCT",
        "ATTR_COLOR_TEMP_KELVIN",
        "ATTR_EFFECT",
        "ATTR_FLASH",
        "ATTR_HS_COLOR",
        "ATTR_RGB_COLOR",
        "ATTR_RGBW_COLOR",
        "ATTR_RGBWW_COLOR",
        "ATTR_TRANSITION",
        "ATTR_WHITE",
        "ATTR_XY_COLOR",
    ]:
        setattr(light_mod, attr, attr.lower())

    # Fan
    fan_mod = _ensure_module("homeassistant.components.fan")

    class FanEntityFeature(IntFlag):
        SET_SPEED = 1
        TURN_ON = 16
        TURN_OFF = 32

    fan_mod.FanEntity = object
    fan_mod.FanEntityFeature = FanEntityFeature

    # Climate
    climate_mod = _ensure_module("homeassistant.components.climate")
    climate_mod.ClimateEntity = object

    climate_const_mod = _ensure_module("homeassistant.components.climate.const")

    class HVACMode(str, Enum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        AUTO = "auto"

    climate_const_mod.HVACMode = HVACMode

    # Cover
    cover_mod = _ensure_module("homeassistant.components.cover")

    class CoverEntityFeature(IntFlag):
        OPEN = 1
        CLOSE = 2
        STOP = 4
        SET_POSITION = 8

    cover_mod.CoverEntity = object
    cover_mod.CoverEntityFeature = CoverEntityFeature
    cover_mod.ATTR_POSITION = "position"


_install_homeassistant_stubs()

from custom_components.opcua.const import CONF_NODE_ID, CONF_NODE_NAME  # noqa: E402


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
def coordinator_factory():
    def _build(data: dict[str, Any]) -> MockCoordinator:
        return MockCoordinator(data=dict(data))

    return _build


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


@pytest.fixture
def coordinator_all() -> MockCoordinator:
    return MockCoordinator(
        data={
            "ns=2;s=EntityMatrix.Test.Node": True,
            "ns=2;s=EntityMatrix.Process.Temp": 21.5,
            "ns=2;s=EntityMatrix.Process.Target": 23.0,
            "ns=2;s=EntityMatrix.Process.Mode": "auto",
            "ns=2;s=EntityMatrix.Cover.Pos": 55,
            "ns=2;s=EntityMatrix.Select.Mode": "Auto",
            "ns=2;s=EntityMatrix.Text.Value": "Recipe-A",
            "ns=2;s=EntityMatrix.Weather.Temp": 19.0,
            "ns=2;s=EntityMatrix.Weather.Humidity": 40,
            "ns=2;s=EntityMatrix.Weather.Pressure": 1013,
            "ns=2;s=EntityMatrix.Weather.Wind": 3.2,
            "ns=2;s=EntityMatrix.Weather.Condition": "sunny",
            "ns=2;s=EntityMatrix.Notify.Title": "Title",
            "ns=2;s=EntityMatrix.Light.On": True,
            "ns=2;s=EntityMatrix.Light.Brightness": 128,
            "ns=2;s=EntityMatrix.Light.Effect": "off",
        }
    )
