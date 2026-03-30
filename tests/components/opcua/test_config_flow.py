from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.opcua.config_flow import (
    OpcUaConfigFlow,
    OpcUaOptionsFlow,
    _browse_option_label,
    _friendly_node_name,
)
from custom_components.opcua.const import (
    CONF_BUTTON_PAYLOAD,
    CONF_CLIENT_CERT_PATH,
    CONF_CLIENT_KEY_PASSWORD,
    CONF_CLIENT_KEY_PATH,
    CONF_CLIMATE_HVAC_MODE_NODE_ID,
    CONF_CLIMATE_MAX_TEMP,
    CONF_CLIMATE_MIN_TEMP,
    CONF_CLIMATE_TEMP_STEP,
    CONF_COVER_CLOSE_NODE_ID,
    CONF_COVER_OPEN_NODE_ID,
    CONF_COVER_SET_POSITION_NODE_ID,
    CONF_COVER_STOP_NODE_ID,
    CONF_FAN_SPEED_NODE_ID,
    CONF_ENDPOINT,
    CONF_LIGHT_BRIGHTNESS_NODE_ID,
    CONF_LIGHT_BRIGHTNESS_SCALE,
    CONF_LIGHT_EFFECT_LIST,
    CONF_LIGHT_EFFECT_NODE_ID,
    CONF_NODE_DEVICE_CLASS,
    CONF_NODE_ICON,
    CONF_NODE_ID,
    CONF_NODE_INVERT,
    CONF_NODE_KIND,
    CONF_NODE_NAME,
    CONF_NODES,
    CONF_NODE_STATE_CLASS,
    CONF_NODE_TARGET_NODE_ID,
    CONF_NODE_UNIT,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_NOTIFY_MESSAGE_NODE_ID,
    CONF_NOTIFY_TITLE_NODE_ID,
    CONF_NUMBER_MAX,
    CONF_NUMBER_MIN,
    CONF_NUMBER_STEP,
    CONF_PASSWORD,
    CONF_SCENE_ACTIVATE_VALUE,
    CONF_SECURITY_POLICY,
    CONF_SELECT_OPTIONS,
    CONF_SERVER_CERT_PATH,
    CONF_TEXT_MAX,
    CONF_USERNAME,
    CONF_VALIDATE_ON_SAVE,
    CONF_WEATHER_CONDITION_NODE_ID,
    CONF_WEATHER_HUMIDITY_NODE_ID,
    CONF_WEATHER_PRESSURE_NODE_ID,
    CONF_WEATHER_WIND_SPEED_NODE_ID,
    DEFAULT_BRIGHTNESS_SCALE,
    DEFAULT_NOTIFY_KEYWORDS,
    NODE_KIND_BINARY_SENSOR,
    NODE_KIND_BUTTON,
    NODE_KIND_LIGHT,
    NODE_KIND_SCENE,
    NODE_KIND_SELECT,
    NODE_KIND_SENSOR,
    NODE_KIND_SWITCH,
)


def test_config_flow_module_is_importable() -> None:
    assert OpcUaConfigFlow.__name__ == "OpcUaConfigFlow"
    assert OpcUaConfigFlow.__mro__[0].__name__ == "OpcUaConfigFlow"


def test_friendly_node_helpers_improve_labels() -> None:
    item = {
        "name": "living_room_temperature",
        "path": "Objects/Home/LivingRoom/Temperature",
        "sample_type": "float",
        "is_writable": False,
    }
    assert _friendly_node_name(item) == "Livingroom – Temperature"
    assert _browse_option_label(item) == "Livingroom – Temperature (float, read-only)"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("step_name", "expected_step_id"),
    [
        ("async_step_init", "init"),
        ("async_step_menu_add_entities", "menu_add_entities"),
        ("async_step_menu_add_entities_advanced", "menu_add_entities_advanced"),
        ("async_step_menu_discovery_tools", "menu_discovery_tools"),
        ("async_step_menu_settings", "menu_settings"),
        ("async_step_add_sensor", "add_sensor"),
        ("async_step_add_binary_sensor", "add_binary_sensor"),
        ("async_step_add_switch", "add_switch"),
        ("async_step_add_light", "add_light"),
        ("async_step_add_button", "add_button"),
        ("async_step_add_climate", "add_climate"),
        ("async_step_add_cover", "add_cover"),
        ("async_step_add_date", "add_date"),
        ("async_step_add_datetime", "add_datetime"),
        ("async_step_add_fan", "add_fan"),
        ("async_step_add_notify", "add_notify"),
        ("async_step_add_number", "add_number"),
        ("async_step_add_scene", "add_scene"),
        ("async_step_add_select", "add_select"),
        ("async_step_add_text", "add_text"),
        ("async_step_add_time", "add_time"),
        ("async_step_add_weather", "add_weather"),
    ],
)
async def test_options_flow_menu_and_form_steps_render(mock_config_entry, step_name, expected_step_id) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    result = await getattr(flow, step_name)()
    assert result["step_id"] == expected_step_id
    assert result["type"] in {"menu", "form"}


@pytest.mark.asyncio
async def test_user_step_rejects_invalid_endpoint() -> None:
    flow = OpcUaConfigFlow()

    result = await flow.async_step_user(
        {
            CONF_ENDPOINT: "http://example.com",
            CONF_SECURITY_POLICY: "None",
            CONF_VALIDATE_ON_SAVE: False,
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"][CONF_ENDPOINT] == "invalid_endpoint"


@pytest.mark.asyncio
async def test_user_step_creates_entry_and_normalizes_keywords() -> None:
    flow = OpcUaConfigFlow()

    result = await flow.async_step_user(
        {
            "title": "PLC A",
            CONF_ENDPOINT: "opc.tcp://plc-a:4840",
            CONF_SECURITY_POLICY: "None",
            CONF_VALIDATE_ON_SAVE: False,
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user_notifications"

    result = await flow.async_step_user_notifications(
        {
            CONF_NOTIFY_ENABLED: True,
            CONF_NOTIFY_KEYWORDS: " Alarm, WARN ,  , Fault ",
        }
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "PLC A"
    assert result["data"][CONF_ENDPOINT] == "opc.tcp://plc-a:4840"
    assert result["data"][CONF_NOTIFY_KEYWORDS] == ["alarm", "warn", "fault"]
    assert result["data"][CONF_NODES] == []


@pytest.mark.asyncio
async def test_user_step_aborts_when_endpoint_already_configured() -> None:
    flow = OpcUaConfigFlow()
    flow._current_entries = [
        SimpleNamespace(data={CONF_ENDPOINT: "opc.tcp://plc-a:4840"})
    ]

    result = await flow.async_step_user(
        {
            CONF_ENDPOINT: "opc.tcp://plc-a:4840",
            CONF_SECURITY_POLICY: "None",
            CONF_VALIDATE_ON_SAVE: False,
        }
    )

    assert result == {"type": "abort", "reason": "already_configured"}


@pytest.mark.asyncio
async def test_zeroconf_setup_uses_default_keywords_when_blank() -> None:
    flow = OpcUaConfigFlow()
    flow._discovered_endpoint = "opc.tcp://192.168.1.20:4840"
    flow._discovered_name = "Discovered PLC"

    result = await flow.async_step_zeroconf_setup(
        {
            CONF_SECURITY_POLICY: "None",
            CONF_VALIDATE_ON_SAVE: False,
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "zeroconf_notifications"

    result = await flow.async_step_zeroconf_notifications(
        {
            CONF_NOTIFY_ENABLED: True,
            CONF_NOTIFY_KEYWORDS: "   ",
        }
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Discovered PLC"
    assert result["data"][CONF_NOTIFY_KEYWORDS] == list(DEFAULT_NOTIFY_KEYWORDS)


@pytest.mark.asyncio
async def test_options_add_light_persists_relevant_fields(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    result = await flow.async_step_add_light(
        {
            CONF_NODE_NAME: "Main Light",
            CONF_NODE_ID: "ns=2;s=Light.State",
            CONF_NODE_INVERT: True,
            CONF_LIGHT_BRIGHTNESS_NODE_ID: "ns=2;s=Light.Brightness",
            CONF_LIGHT_BRIGHTNESS_SCALE: 1000,
            CONF_LIGHT_EFFECT_NODE_ID: "ns=2;s=Light.Effect",
            CONF_LIGHT_EFFECT_LIST: "off,blink,party",
        }
    )

    assert result["type"] == "menu"
    assert result["step_id"] == "init"
    node = flow._options[CONF_NODES][0]
    assert node[CONF_NODE_KIND] == NODE_KIND_LIGHT
    assert node[CONF_NODE_ID] == "ns=2;s=Light.State"
    assert node[CONF_NODE_INVERT] is True
    assert node[CONF_LIGHT_BRIGHTNESS_NODE_ID] == "ns=2;s=Light.Brightness"
    assert node[CONF_LIGHT_BRIGHTNESS_SCALE] == 1000.0
    assert node[CONF_LIGHT_EFFECT_NODE_ID] == "ns=2;s=Light.Effect"
    assert node[CONF_LIGHT_EFFECT_LIST] == ["off", "blink", "party"]
    assert mock_hass.config_entries.reloaded == [mock_config_entry.entry_id]


@pytest.mark.asyncio
async def test_options_add_button_and_scene_parse_scalar_payloads(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    await flow.async_step_add_button(
        {
            CONF_NODE_NAME: "Start",
            CONF_NODE_ID: "ns=2;s=Button.Start",
            CONF_BUTTON_PAYLOAD: "42",
        }
    )
    await flow.async_step_add_scene(
        {
            CONF_NODE_NAME: "Night",
            CONF_NODE_ID: "ns=2;s=Scene.Night",
            CONF_SCENE_ACTIVATE_VALUE: "off",
        }
    )

    assert flow._options[CONF_NODES][0][CONF_NODE_KIND] == NODE_KIND_BUTTON
    assert flow._options[CONF_NODES][0][CONF_BUTTON_PAYLOAD] == 42
    assert flow._options[CONF_NODES][1][CONF_NODE_KIND] == NODE_KIND_SCENE
    assert flow._options[CONF_NODES][1][CONF_SCENE_ACTIVATE_VALUE] is False


@pytest.mark.asyncio
async def test_options_add_select_splits_csv_options(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    await flow.async_step_add_select(
        {
            CONF_NODE_NAME: "Mode",
            CONF_NODE_ID: "ns=2;s=Mode",
            CONF_SELECT_OPTIONS: "auto, manual , eco",
        }
    )

    node = flow._options[CONF_NODES][0]
    assert node[CONF_NODE_KIND] == NODE_KIND_SELECT
    assert node[CONF_SELECT_OPTIONS] == ["auto", "manual", "eco"]


@pytest.mark.asyncio
async def test_options_add_various_platforms_persist_expected_fields(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    await flow.async_step_add_sensor(
        {
            CONF_NODE_NAME: "Temp",
            CONF_NODE_ID: "ns=2;s=Temp",
            CONF_NODE_UNIT: "°C",
            CONF_NODE_DEVICE_CLASS: "temperature",
            CONF_NODE_STATE_CLASS: "measurement",
            CONF_NODE_ICON: "mdi:thermometer",
        }
    )
    await flow.async_step_add_binary_sensor(
        {
            CONF_NODE_NAME: "Leak",
            CONF_NODE_ID: "ns=2;s=Leak",
            CONF_NODE_DEVICE_CLASS: "moisture",
            CONF_NODE_ICON: "mdi:water-alert",
            CONF_NODE_INVERT: True,
        }
    )
    await flow.async_step_add_climate(
        {
            CONF_NODE_NAME: "HVAC",
            CONF_NODE_ID: "ns=2;s=Current",
            CONF_NODE_TARGET_NODE_ID: "ns=2;s=Target",
            CONF_CLIMATE_HVAC_MODE_NODE_ID: "ns=2;s=Mode",
            CONF_CLIMATE_MIN_TEMP: 5,
            CONF_CLIMATE_MAX_TEMP: 30,
            CONF_CLIMATE_TEMP_STEP: 0.5,
        }
    )
    await flow.async_step_add_cover(
        {
            CONF_NODE_NAME: "Blind",
            CONF_NODE_ID: "ns=2;s=Pos",
            CONF_NODE_TARGET_NODE_ID: "ns=2;s=Target",
            CONF_COVER_SET_POSITION_NODE_ID: "ns=2;s=SetPos",
            CONF_COVER_OPEN_NODE_ID: "ns=2;s=Open",
            CONF_COVER_CLOSE_NODE_ID: "ns=2;s=Close",
            CONF_COVER_STOP_NODE_ID: "ns=2;s=Stop",
        }
    )
    await flow.async_step_add_date({CONF_NODE_NAME: "Date", CONF_NODE_ID: "ns=2;s=Date"})
    await flow.async_step_add_datetime({CONF_NODE_NAME: "DateTime", CONF_NODE_ID: "ns=2;s=DateTime"})
    await flow.async_step_add_fan(
        {
            CONF_NODE_NAME: "Fan",
            CONF_NODE_ID: "ns=2;s=FanOn",
            CONF_FAN_SPEED_NODE_ID: "ns=2;s=FanSpeed",
            CONF_NODE_INVERT: True,
        }
    )
    await flow.async_step_add_notify(
        {
            CONF_NODE_NAME: "Notifier",
            CONF_NODE_ID: "ns=2;s=Notify",
            CONF_NOTIFY_MESSAGE_NODE_ID: "ns=2;s=NotifyMsg",
            CONF_NOTIFY_TITLE_NODE_ID: "ns=2;s=NotifyTitle",
        }
    )
    await flow.async_step_add_number(
        {
            CONF_NODE_NAME: "Setpoint",
            CONF_NODE_ID: "ns=2;s=Setpoint",
            CONF_NUMBER_MIN: 1,
            CONF_NUMBER_MAX: 9,
            CONF_NUMBER_STEP: 0.5,
            CONF_NODE_UNIT: "bar",
        }
    )
    await flow.async_step_add_text(
        {
            CONF_NODE_NAME: "Message",
            CONF_NODE_ID: "ns=2;s=Text",
            CONF_TEXT_MAX: 64,
        }
    )
    await flow.async_step_add_time({CONF_NODE_NAME: "Start", CONF_NODE_ID: "ns=2;s=Time"})
    await flow.async_step_add_weather(
        {
            CONF_NODE_NAME: "Weather",
            CONF_NODE_ID: "ns=2;s=Weather.Temp",
            CONF_WEATHER_HUMIDITY_NODE_ID: "ns=2;s=Weather.Humidity",
            CONF_WEATHER_PRESSURE_NODE_ID: "ns=2;s=Weather.Pressure",
            CONF_WEATHER_WIND_SPEED_NODE_ID: "ns=2;s=Weather.Wind",
            CONF_WEATHER_CONDITION_NODE_ID: "ns=2;s=Weather.Condition",
        }
    )

    nodes = flow._options[CONF_NODES]
    assert len(nodes) == 12
    assert nodes[0][CONF_NODE_UNIT] == "°C"
    assert nodes[1][CONF_NODE_INVERT] is True
    assert nodes[2][CONF_NODE_TARGET_NODE_ID] == "ns=2;s=Target"
    assert nodes[3][CONF_COVER_OPEN_NODE_ID] == "ns=2;s=Open"
    assert nodes[6][CONF_FAN_SPEED_NODE_ID] == "ns=2;s=FanSpeed"
    assert nodes[7][CONF_NOTIFY_TITLE_NODE_ID] == "ns=2;s=NotifyTitle"
    assert nodes[8][CONF_NUMBER_STEP] == 0.5
    assert nodes[9][CONF_TEXT_MAX] == 64
    assert nodes[10][CONF_NODE_KIND] == "time"
    assert nodes[11][CONF_WEATHER_CONDITION_NODE_ID] == "ns=2;s=Weather.Condition"
    assert mock_hass.config_entries.reloaded


@pytest.mark.asyncio
async def test_auto_discovery_maps_light_and_generic_nodes(monkeypatch, mock_hass, mock_config_entry) -> None:
    browsed = [
        {
            "node_id": "ns=2;s=Light1",
            "parent_node_id": "i=85",
            "node_class": "Object",
            "name": "Light 1",
            "type_definition": "LightType",
        },
        {
            "node_id": "ns=2;s=Light1.State",
            "parent_node_id": "ns=2;s=Light1",
            "node_class": "Variable",
            "name": "State",
            "sample_type": "bool",
            "is_writable": True,
        },
        {
            "node_id": "ns=2;s=Light1.Brightness",
            "parent_node_id": "ns=2;s=Light1",
            "node_class": "Variable",
            "name": "Brightness",
            "sample_type": "int",
            "is_writable": True,
        },
        {
            "node_id": "ns=2;s=Switch1",
            "parent_node_id": "i=85",
            "node_class": "Variable",
            "name": "Pump Enable",
            "sample_type": "bool",
            "is_writable": True,
            "path": "Objects/Pump Enable",
        },
        {
            "node_id": "ns=2;s=Temp1",
            "parent_node_id": "i=85",
            "node_class": "Variable",
            "name": "Temperature",
            "sample_type": "float",
            "is_writable": False,
            "engineering_units": "°C",
            "path": "Objects/Temperature",
        },
        {
            "node_id": "i=2258",
            "parent_node_id": "i=85",
            "node_class": "Variable",
            "name": "ServerStatus",
            "sample_type": "str",
            "is_writable": False,
            "path": "Objects/ServerStatus",
        },
    ]

    class _Manager:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def browse_nodes(self, **kwargs):
            return browsed

        async def disconnect(self):
            return None

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager", _Manager)

    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    result = await flow.async_step_auto_discovery(
        {
            "root_node_id": "i=85",
            "include_readonly": True,
            "include_standard_nodes": False,
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "auto_discovery_review"
    assert result["description_placeholders"]["lights"] == "1"
    assert result["description_placeholders"]["switches"] == "1"
    assert result["description_placeholders"]["sensors"] == "1"
    assert "Light 1" in result["description_placeholders"]["sample"]
    assert len(flow._discovery_cache) == 3
    assert {node[CONF_NODE_KIND] for node in flow._discovery_cache} == {
        NODE_KIND_LIGHT,
        NODE_KIND_SWITCH,
        NODE_KIND_SENSOR,
    }

    light = next(
        node for node in flow._discovery_cache if node[CONF_NODE_KIND] == NODE_KIND_LIGHT
    )
    assert light[CONF_NODE_ID] == "ns=2;s=Light1.State"
    assert light[CONF_LIGHT_BRIGHTNESS_NODE_ID] == "ns=2;s=Light1.Brightness"
    assert (
        CONF_LIGHT_BRIGHTNESS_SCALE not in light
        or light[CONF_LIGHT_BRIGHTNESS_SCALE] == DEFAULT_BRIGHTNESS_SCALE
    )


@pytest.mark.asyncio
async def test_auto_discovery_review_apply_appends_unique_nodes(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass
    flow._discovery_cache = [
        {CONF_NODE_KIND: NODE_KIND_SENSOR, CONF_NODE_NAME: "Temp", CONF_NODE_ID: "ns=2;s=Temp"},
        {CONF_NODE_KIND: NODE_KIND_SWITCH, CONF_NODE_NAME: "Pump", CONF_NODE_ID: "ns=2;s=Pump"},
    ]
    flow._options[CONF_NODES] = [
        {CONF_NODE_KIND: NODE_KIND_SENSOR, CONF_NODE_NAME: "Temp", CONF_NODE_ID: "ns=2;s=Temp"}
    ]

    result = await flow.async_step_auto_discovery_review({"apply": True})

    assert result["type"] == "menu"
    assert result["step_id"] == "init"
    assert len(flow._options[CONF_NODES]) == 2
    assert flow._options[CONF_NODES][1][CONF_NODE_ID] == "ns=2;s=Pump"


@pytest.mark.asyncio
async def test_discover_servers_flow_updates_entry_and_handles_errors(monkeypatch, mock_hass, mock_config_entry) -> None:
    async def _discover(url, include_network=False):
        assert url == "opc.tcp://127.0.0.1:4840"
        assert include_network is True
        return [
            {
                "application_name": "Test Server",
                "endpoint_url": "opc.tcp://127.0.0.1:4841",
                "security_policy": "None",
                "security_mode": "None",
                "supported_now": True,
            }
        ]

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager.discover_servers", _discover)

    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass

    result = await flow.async_step_discover_servers(
        {"discovery_url": "opc.tcp://127.0.0.1:4840", "include_network": True}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "discover_servers_select"

    result = await flow.async_step_discover_servers_select({"selected": "0"})
    assert result["type"] == "menu"
    assert mock_config_entry.data[CONF_ENDPOINT] == "opc.tcp://127.0.0.1:4841"
    assert mock_hass.config_entries.reloaded == [mock_config_entry.entry_id]

    async def _discover_fail(url, include_network=False):
        raise RuntimeError("nope")

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager.discover_servers", _discover_fail)
    result = await flow.async_step_discover_servers(
        {"discovery_url": "opc.tcp://127.0.0.1:4840", "include_network": False}
    )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_browse_add_switch_adds_selected_variable(mock_hass, mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)
    flow.hass = mock_hass
    flow._browse_root_node_id = "i=85"
    flow._browse_current_parent = "i=85"
    flow._browse_cache = [
        {
            "node_id": "ns=2;s=Folder",
            "parent_node_id": "i=85",
            "node_class": "Object",
            "name": "Folder",
            "sample_type": "",
            "is_writable": False,
            "path": "Objects/Folder",
        },
        {
            "node_id": "ns=2;s=Switch2",
            "parent_node_id": "i=85",
            "node_class": "Variable",
            "name": "Enable",
            "sample_type": "bool",
            "is_writable": True,
            "path": "Objects/Enable",
        },
    ]

    result = await flow.async_step_browse_add_switch({"node_ids": ["ns=2;s=Switch2"]})

    assert result["type"] == "form"
    assert result["step_id"] == "browse_add_switch"
    node = flow._options[CONF_NODES][0]
    assert node[CONF_NODE_KIND] == NODE_KIND_SWITCH
    assert node[CONF_NODE_NAME] == "Enable"
    assert node[CONF_NODE_ID] == "ns=2;s=Switch2"


def test_map_discovered_item_classifies_basic_types(mock_config_entry) -> None:
    flow = OpcUaOptionsFlow(mock_config_entry)

    assert flow._map_discovered_item(
        {
            "node_id": "ns=2;s=BoolRO",
            "node_class": "Variable",
            "name": "Door",
            "sample_type": "bool",
            "is_writable": False,
        },
        include_readonly=True,
    )[CONF_NODE_KIND] == NODE_KIND_BINARY_SENSOR

    assert flow._map_discovered_item(
        {
            "node_id": "ns=2;s=BoolRW",
            "node_class": "Variable",
            "name": "Pump",
            "sample_type": "bool",
            "is_writable": True,
        },
        include_readonly=True,
    )[CONF_NODE_KIND] == NODE_KIND_SWITCH

    sensor = flow._map_discovered_item(
        {
            "node_id": "ns=2;s=Temp",
            "node_class": "Variable",
            "name": "Temperature",
            "sample_type": "float",
            "is_writable": False,
            "path": "Objects/Temperature",
            "engineering_units": "°C",
        },
        include_readonly=True,
    )
    assert sensor[CONF_NODE_KIND] == NODE_KIND_SENSOR
    assert sensor["unit_of_measurement"] == "°C"
    assert sensor["device_class"] == "temperature"
    assert sensor["state_class"] == "measurement"

    motion = flow._map_discovered_item(
        {
            "node_id": "ns=2;s=Motion",
            "node_class": "Variable",
            "name": "Motion Detected",
            "sample_type": "bool",
            "is_writable": False,
        },
        include_readonly=True,
    )
    assert motion[CONF_NODE_KIND] == NODE_KIND_BINARY_SENSOR
    assert motion["device_class"] == "motion"


@pytest.mark.asyncio
async def test_zeroconf_aborts_without_host_or_port() -> None:
    flow = OpcUaConfigFlow()
    result = await flow.async_step_zeroconf(SimpleNamespace(host="", port=0, name="X"))
    assert result == {"type": "abort", "reason": "cannot_connect"}


@pytest.mark.asyncio
async def test_zeroconf_confirm_without_endpoint_aborts() -> None:
    flow = OpcUaConfigFlow()
    result = await flow.async_step_zeroconf_confirm()
    assert result == {"type": "abort", "reason": "cannot_connect"}


@pytest.mark.asyncio
async def test_user_step_with_secure_policy_goes_to_auth_step() -> None:
    flow = OpcUaConfigFlow()
    result = await flow.async_step_user(
        {
            "title": "PLC A",
            CONF_ENDPOINT: "opc.tcp://plc-a:4840",
            CONF_SECURITY_POLICY: "Basic256Sha256_SignAndEncrypt",
            CONF_VALIDATE_ON_SAVE: False,
        }
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user_auth"


@pytest.mark.asyncio
async def test_reauth_confirm_returns_form_when_entry_present() -> None:
    flow = OpcUaConfigFlow()
    flow._reauth_entry = SimpleNamespace(
        data={CONF_ENDPOINT: "opc.tcp://host:4840", CONF_SECURITY_POLICY: "None"}
    )

    result = await flow.async_step_reauth_confirm()
    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"


@pytest.mark.asyncio
async def test_reauth_confirm_success_updates_entry(monkeypatch) -> None:
    class _Manager:
        async def ensure_connected(self):
            return None

        async def disconnect(self):
            return None

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager", lambda **kwargs: _Manager())

    entry = SimpleNamespace(data={CONF_ENDPOINT: "opc.tcp://host:4840"})
    flow = OpcUaConfigFlow()
    flow._reauth_entry = entry

    result = await flow.async_step_reauth_confirm(
        {
            CONF_SECURITY_POLICY: "None",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pw",
            CONF_CLIENT_CERT_PATH: "",
            CONF_CLIENT_KEY_PATH: "",
            CONF_SERVER_CERT_PATH: "",
            CONF_CLIENT_KEY_PASSWORD: "",
        }
    )
    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
    assert result["data_updates"][CONF_USERNAME] == "user"


@pytest.mark.asyncio
async def test_reauth_confirm_failure_sets_error(monkeypatch) -> None:
    class _Manager:
        async def ensure_connected(self):
            raise RuntimeError("boom")

        async def disconnect(self):
            return None

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager", lambda **kwargs: _Manager())

    flow = OpcUaConfigFlow()
    flow._reauth_entry = SimpleNamespace(data={CONF_ENDPOINT: "opc.tcp://host:4840", CONF_SECURITY_POLICY: "None"})
    result = await flow.async_step_reauth_confirm({CONF_SECURITY_POLICY: "None"})
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_reconfigure_success_updates_entry(monkeypatch) -> None:
    class _Manager:
        async def ensure_connected(self):
            return None

        async def disconnect(self):
            return None

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager", lambda **kwargs: _Manager())

    entry = SimpleNamespace(data={CONF_ENDPOINT: "opc.tcp://old:4840", CONF_SECURITY_POLICY: "None"})
    flow = OpcUaConfigFlow()
    flow._reconfigure_entry = entry

    result = await flow.async_step_reconfigure(
        {
            CONF_ENDPOINT: "opc.tcp://new:4840",
            CONF_SECURITY_POLICY: "None",
            CONF_USERNAME: "u",
            CONF_PASSWORD: "p",
            CONF_CLIENT_CERT_PATH: "",
            CONF_CLIENT_KEY_PATH: "",
            CONF_SERVER_CERT_PATH: "",
            CONF_CLIENT_KEY_PASSWORD: "",
        }
    )
    assert result["type"] == "abort"
    assert result["data_updates"][CONF_ENDPOINT] == "opc.tcp://new:4840"


@pytest.mark.asyncio
async def test_reconfigure_failure_sets_error(monkeypatch) -> None:
    class _Manager:
        async def ensure_connected(self):
            raise RuntimeError("boom")

        async def disconnect(self):
            return None

    monkeypatch.setattr("custom_components.opcua.config_flow.OpcUaClientManager", lambda **kwargs: _Manager())

    flow = OpcUaConfigFlow()
    flow._reconfigure_entry = SimpleNamespace(data={CONF_ENDPOINT: "opc.tcp://old:4840", CONF_SECURITY_POLICY: "None"})
    result = await flow.async_step_reconfigure({CONF_ENDPOINT: "opc.tcp://new:4840", CONF_SECURITY_POLICY: "None"})
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"
