from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.opcua.config_flow import OpcUaConfigFlow, OpcUaOptionsFlow
from custom_components.opcua.const import (
    CONF_BUTTON_PAYLOAD,
    CONF_ENDPOINT,
    CONF_LIGHT_BRIGHTNESS_NODE_ID,
    CONF_LIGHT_BRIGHTNESS_SCALE,
    CONF_LIGHT_EFFECT_LIST,
    CONF_LIGHT_EFFECT_NODE_ID,
    CONF_NODE_ID,
    CONF_NODE_INVERT,
    CONF_NODE_KIND,
    CONF_NODE_NAME,
    CONF_NODES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_KEYWORDS,
    CONF_SCAN_INTERVAL,
    CONF_SCENE_ACTIVATE_VALUE,
    CONF_SECURITY_POLICY,
    CONF_SELECT_OPTIONS,
    CONF_VALIDATE_ON_SAVE,
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


@pytest.mark.asyncio
async def test_user_step_rejects_invalid_endpoint() -> None:
    flow = OpcUaConfigFlow()

    result = await flow.async_step_user(
        {
            CONF_ENDPOINT: "http://example.com",
            CONF_SECURITY_POLICY: "None",
            CONF_SCAN_INTERVAL: 2,
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
            CONF_NOTIFY_ENABLED: True,
            CONF_NOTIFY_KEYWORDS: " Alarm, WARN ,  , Fault ",
            CONF_SCAN_INTERVAL: 1.5,
            CONF_VALIDATE_ON_SAVE: False,
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
            CONF_SCAN_INTERVAL: 2,
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
            CONF_NOTIFY_ENABLED: True,
            CONF_NOTIFY_KEYWORDS: "   ",
            CONF_SCAN_INTERVAL: 2,
            CONF_VALIDATE_ON_SAVE: False,
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
