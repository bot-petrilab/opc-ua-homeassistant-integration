from __future__ import annotations

import ast
from pathlib import Path


def _load_config_flow_source() -> str:
    path = Path(__file__).resolve().parents[3] / "custom_components" / "opcua" / "config_flow.py"
    return path.read_text(encoding="utf-8")


def _get_async_methods(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            names.add(node.name)
    return names


def test_options_flow_has_all_add_methods() -> None:
    source = _load_config_flow_source()
    methods = _get_async_methods(source)

    expected = {
        "async_step_add_sensor",
        "async_step_add_binary_sensor",
        "async_step_add_switch",
        "async_step_add_light",
        "async_step_add_button",
        "async_step_add_climate",
        "async_step_add_cover",
        "async_step_add_date",
        "async_step_add_datetime",
        "async_step_add_fan",
        "async_step_add_notify",
        "async_step_add_number",
        "async_step_add_scene",
        "async_step_add_select",
        "async_step_add_text",
        "async_step_add_time",
        "async_step_add_weather",
    }
    assert expected.issubset(methods)


def test_options_flow_has_all_browse_add_methods() -> None:
    source = _load_config_flow_source()
    methods = _get_async_methods(source)

    expected = {
        "async_step_browse_add_sensor",
        "async_step_browse_add_binary_sensor",
        "async_step_browse_add_switch",
        "async_step_browse_add_light",
        "async_step_browse_add_button",
        "async_step_browse_add_climate",
        "async_step_browse_add_cover",
        "async_step_browse_add_date",
        "async_step_browse_add_datetime",
        "async_step_browse_add_fan",
        "async_step_browse_add_notify",
        "async_step_browse_add_number",
        "async_step_browse_add_scene",
        "async_step_browse_add_select",
        "async_step_browse_add_text",
        "async_step_browse_add_time",
        "async_step_browse_add_weather",
    }
    assert expected.issubset(methods)


def test_options_menu_lists_base_and_advanced_platforms() -> None:
    source = _load_config_flow_source()

    base_menu_items = [
        "add_sensor",
        "add_binary_sensor",
        "add_switch",
        "add_light",
        "add_number",
        "add_select",
        "add_text",
        "add_button",
        "menu_add_entities_advanced",
    ]
    adv_menu_items = [
        "add_climate",
        "add_cover",
        "add_fan",
        "add_scene",
        "add_date",
        "add_datetime",
        "add_time",
        "add_weather",
        "add_notify",
    ]

    for item in base_menu_items + adv_menu_items:
        assert f'"{item}"' in source
