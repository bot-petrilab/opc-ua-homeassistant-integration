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

    class ConfigEntry:
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    class ConfigFlow:
        def __init_subclass__(cls, **kwargs):
            return super().__init_subclass__()

        def __init__(self) -> None:
            self.context: dict[str, Any] = {}
            self.hass = None
            self._unique_id = None
            self._current_entries: list[Any] = []
            self._reauth_entry = None
            self._reconfigure_entry = None

        async def async_set_unique_id(self, unique_id: str) -> None:
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self) -> None:
            return None

        def _async_current_entries(self) -> list[Any]:
            return list(self._current_entries)

        def _get_reauth_entry(self):
            return self._reauth_entry

        def _get_reconfigure_entry(self):
            return self._reconfigure_entry

        def async_show_form(
            self,
            *,
            step_id: str,
            data_schema=None,
            errors=None,
            description_placeholders=None,
        ):
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
                "description_placeholders": description_placeholders,
            }

        def async_show_menu(self, *, step_id: str, menu_options: list[str]):
            return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

        def async_create_entry(self, *, title: str, data: dict[str, Any]):
            return {"type": "create_entry", "title": title, "data": data}

        def async_abort(self, *, reason: str):
            return {"type": "abort", "reason": reason}

        def async_update_reload_and_abort(self, entry, *, data_updates: dict[str, Any]):
            return {
                "type": "abort",
                "reason": "reauth_successful",
                "entry": entry,
                "data_updates": data_updates,
            }

    class OptionsFlow:
        def __init__(self, config_entry=None) -> None:
            self.config_entry = config_entry
            self.hass = None

        def async_show_form(
            self,
            *,
            step_id: str,
            data_schema=None,
            errors=None,
            description_placeholders=None,
        ):
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
                "description_placeholders": description_placeholders,
            }

        def async_show_menu(self, *, step_id: str, menu_options: list[str]):
            return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

        def async_create_entry(self, *, title: str, data: dict[str, Any]):
            return {"type": "create_entry", "title": title, "data": data}

    ce_mod.ConfigEntry = ConfigEntry
    ce_mod.ConfigFlow = ConfigFlow
    ce_mod.ConfigFlowResult = dict
    ce_mod.OptionsFlow = OptionsFlow

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
    helpers_mod = _ensure_module("homeassistant.helpers")
    _ensure_module("homeassistant.helpers.entity_platform").AddEntitiesCallback = object

    er_mod = _ensure_module("homeassistant.helpers.entity_registry")

    class _Registry:
        def __init__(self) -> None:
            self.removed: list[str] = []
            self.entries: list[Any] = []

        def async_remove(self, entity_id: str) -> None:
            self.removed.append(entity_id)

    def async_get(_hass):
        return getattr(_hass, "entity_registry", _Registry())

    def async_entries_for_config_entry(registry, entry_id: str):
        return [
            entry
            for entry in getattr(registry, "entries", [])
            if getattr(entry, "config_entry_id", None) == entry_id
        ]

    er_mod.async_get = async_get
    er_mod.async_entries_for_config_entry = async_entries_for_config_entry

    selector_mod = _ensure_module("homeassistant.helpers.selector")

    @dataclass
    class NumberSelectorConfig:
        min: float | int | None = None
        max: float | int | None = None
        step: float | int | None = None
        mode: str | None = None

    @dataclass
    class SelectSelectorConfig:
        options: list[Any] | tuple[Any, ...]
        multiple: bool = False
        mode: str | None = None

    @dataclass
    class TextSelectorConfig:
        type: str | None = None
        autocomplete: str | None = None

    class NumberSelector:
        def __init__(self, config=None):
            self.config = config

    class SelectSelector:
        def __init__(self, config=None):
            self.config = config

    class TextSelector:
        def __init__(self, config=None):
            self.config = config

    class BooleanSelector:
        def __init__(self, config=None):
            self.config = config

    class SelectSelectorMode(str, Enum):
        DROPDOWN = "dropdown"

    selector_mod.BooleanSelector = BooleanSelector
    selector_mod.NumberSelector = NumberSelector
    selector_mod.NumberSelectorConfig = NumberSelectorConfig
    selector_mod.SelectSelector = SelectSelector
    selector_mod.SelectSelectorConfig = SelectSelectorConfig
    selector_mod.SelectSelectorMode = SelectSelectorMode
    selector_mod.TextSelector = TextSelector
    selector_mod.TextSelectorConfig = TextSelectorConfig

    helpers_mod.entity_registry = er_mod

    diag_mod = _ensure_module("homeassistant.components.diagnostics")

    def async_redact_data(data, to_redact):
        def _walk(value):
            if isinstance(value, dict):
                out = {}
                for k, v in value.items():
                    if str(k).lower() in {str(x).lower() for x in to_redact}:
                        out[k] = "REDACTED"
                    else:
                        out[k] = _walk(v)
                return out
            if isinstance(value, list):
                return [_walk(v) for v in value]
            return value

        return _walk(data)

    diag_mod.async_redact_data = async_redact_data

    ir_mod = _ensure_module("homeassistant.helpers.issue_registry")

    class IssueSeverity(str, Enum):
        ERROR = "error"
        WARNING = "warning"

    def async_create_issue(hass, domain, issue_id, **kwargs):
        issues = getattr(hass, "_issues", [])
        issues.append((domain, issue_id, kwargs))
        hass._issues = issues

    def async_delete_issue(hass, domain, issue_id):
        issues = getattr(hass, "_issues", [])
        hass._issues = [item for item in issues if not (item[0] == domain and item[1] == issue_id)]

    ir_mod.IssueSeverity = IssueSeverity
    ir_mod.async_create_issue = async_create_issue
    ir_mod.async_delete_issue = async_delete_issue

    dr_mod = _ensure_module("homeassistant.helpers.device_registry")

    class DeviceInfo(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    dr_mod.DeviceInfo = DeviceInfo

    uc_mod = _ensure_module("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __init__(self, hass=None, *args, **kwargs):
            self.hass = hass
            self.data = {}
            self.last_update_success = True

        def async_set_updated_data(self, data):
            self.data = data
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

    class LightEntity:
        @property
        def supported_color_modes(self):
            return getattr(self, "_attr_supported_color_modes", None)

        @property
        def min_color_temp_kelvin(self):
            return getattr(self, "_attr_min_color_temp_kelvin", None)

        @property
        def max_color_temp_kelvin(self):
            return getattr(self, "_attr_max_color_temp_kelvin", None)

    light_mod.LightEntity = LightEntity
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

    fan_mod = _ensure_module("homeassistant.components.fan")

    class FanEntityFeature(IntFlag):
        SET_SPEED = 1
        TURN_ON = 16
        TURN_OFF = 32

    fan_mod.FanEntity = object
    fan_mod.FanEntityFeature = FanEntityFeature

    climate_mod = _ensure_module("homeassistant.components.climate")
    climate_mod.ClimateEntity = object

    climate_const_mod = _ensure_module("homeassistant.components.climate.const")

    class HVACMode(str, Enum):
        OFF = "off"
        HEAT = "heat"
        COOL = "cool"
        AUTO = "auto"

    climate_const_mod.HVACMode = HVACMode

    cover_mod = _ensure_module("homeassistant.components.cover")

    class CoverEntityFeature(IntFlag):
        OPEN = 1
        CLOSE = 2
        STOP = 4
        SET_POSITION = 8

    cover_mod.CoverEntity = object
    cover_mod.CoverEntityFeature = CoverEntityFeature
    cover_mod.ATTR_POSITION = "position"


def _install_voluptuous_stubs() -> None:
    vol_mod = _ensure_module("voluptuous")

    class Marker:
        def __init__(self, schema, default=None):
            self.schema = schema
            self.default = default

    class Required(Marker):
        pass

    class Optional(Marker):
        pass

    class Schema:
        def __init__(self, schema):
            self.schema = schema

        def __call__(self, value):
            return value

    vol_mod.Required = Required
    vol_mod.Optional = Optional
    vol_mod.Schema = Schema


def _install_asyncua_stubs() -> None:
    asyncua_mod = _ensure_module("asyncua")

    class _DummyClient:
        def __init__(self, endpoint: str) -> None:
            self.endpoint = endpoint
            self.security = None
            self.username = None
            self.password = None

        async def set_security_string(self, value: str) -> None:
            self.security = value

        def set_user(self, username: str) -> None:
            self.username = username

        def set_password(self, password: str) -> None:
            self.password = password

        async def connect(self) -> None:
            return None

        async def disconnect(self) -> None:
            return None

        def get_node(self, node_id: str):
            raise NotImplementedError(node_id)

    asyncua_mod.Client = _DummyClient
    asyncua_mod.ua = types.SimpleNamespace()


_install_homeassistant_stubs()
_install_voluptuous_stubs()
_install_asyncua_stubs()

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
def mock_hass():
    class _ConfigEntries:
        def __init__(self) -> None:
            self.updated: list[tuple[Any, dict[str, Any] | None, dict[str, Any] | None]] = []
            self.reloaded: list[str] = []

        def async_update_entry(self, entry, *, data=None, options=None) -> None:
            self.updated.append((entry, data, options))
            if data is not None:
                entry.data = data
            if options is not None:
                entry.options = options

        async def async_reload(self, entry_id: str) -> None:
            self.reloaded.append(entry_id)

    class _Hass:
        def __init__(self) -> None:
            self.config_entries = _ConfigEntries()
            self.entity_registry = types.SimpleNamespace(entries=[], removed=[])
            self.entity_registry.async_remove = self.entity_registry.removed.append

    return _Hass()


@pytest.fixture
def mock_config_entry():
    class _Entry:
        def __init__(self) -> None:
            self.entry_id = "entry-1"
            self.data = {
                "endpoint": "opc.tcp://127.0.0.1:4840",
                "security_policy": "None",
                "nodes": [],
            }
            self.options = {}

    return _Entry()


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
