#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

from playwright.async_api import async_playwright

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_USER = os.getenv("HA_USER", "admin")
HA_PASS = os.getenv("HA_PASS", "Admin123")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4840")
TITLE = os.getenv("OPC_TITLE", "OPC UA Entity Matrix")


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(45000)

        async def call_api(method: str, path: str, data=None):
            raw = await page.evaluate(
                """async (args) => {
                  const ha = document.querySelector('home-assistant');
                  try {
                    const out = await ha.hass.callApi(args.method, args.path, args.data || undefined);
                    return JSON.stringify({ok: true, out});
                  } catch (err) {
                    let e = null;
                    try { e = JSON.parse(JSON.stringify(err)); } catch (_) { e = String(err); }
                    return JSON.stringify({ok: false, err: e});
                  }
                }""",
                {"method": method, "path": path, "data": data},
            )
            obj = json.loads(raw)
            if not obj.get("ok"):
                raise RuntimeError(f"API {method} {path} failed: {obj.get('err')}")
            return obj.get("out")

        async def start_options_flow(entry_id: str):
            return await call_api(
                "POST", "config/config_entries/options/flow", {"handler": entry_id}
            )

        async def opt_step(flow_id: str, payload: dict):
            return await call_api(
                "POST", f"config/config_entries/options/flow/{flow_id}", payload
            )

        async def add_platform(
            entry_id: str, step_id: str, payload: dict, *, advanced: bool
        ) -> None:
            opt = await start_options_flow(entry_id)
            fid = opt["flow_id"]
            menu = await opt_step(fid, {"next_step_id": "menu_add_entities"})
            if menu.get("step_id") != "menu_add_entities":
                raise RuntimeError(f"menu_add_entities failed for {step_id}: {menu}")
            if advanced:
                menu = await opt_step(
                    fid, {"next_step_id": "menu_add_entities_advanced"}
                )
                if menu.get("step_id") != "menu_add_entities_advanced":
                    raise RuntimeError(
                        f"menu_add_entities_advanced failed for {step_id}: {menu}"
                    )
            nav = await opt_step(fid, {"next_step_id": step_id})
            if nav.get("step_id") != step_id:
                raise RuntimeError(f"Navigation failed for {step_id}: {nav}")
            done = await opt_step(fid, payload)
            if done.get("step_id") != "init":
                raise RuntimeError(f"Submit failed for {step_id}: {done}")

        await page.goto(HA_URL)
        await page.wait_for_timeout(1500)
        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', HA_USER)
            await page.fill('input[name="password"]', HA_PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3500)

        # Cleanup old target entries first
        entries = await call_api("GET", "config/config_entries/entry")
        for e in [
            x
            for x in entries
            if x.get("domain") == "opcua"
            and (
                x.get("title") == TITLE
                or ((x.get("data") or {}).get("endpoint") == OPC_ENDPOINT)
            )
        ]:
            try:
                await call_api("DELETE", f"config/config_entries/entry/{e['entry_id']}")
            except Exception:
                pass

        # Create config entry
        init = await call_api(
            "POST", "config/config_entries/flow", {"handler": "opcua"}
        )
        flow_id = init["flow_id"]
        created = await call_api(
            "POST",
            f"config/config_entries/flow/{flow_id}",
            {
                "title": TITLE,
                "endpoint": OPC_ENDPOINT,
                "security_policy": "None",
                "scan_interval": 2,
                "validate_on_save": False,
                "notify_enabled": True,
                "notify_service": "persistent_notification.create",
                "notify_title_prefix": "OPC-UA Matrix",
                "notify_keywords": "alarm,warning,fault,error,matrix",
            },
        )
        if created.get("type") not in {"create_entry", "abort"}:
            raise RuntimeError(f"Unexpected create result: {created}")

        entries = await call_api("GET", "config/config_entries/entry")
        target = [
            x
            for x in entries
            if x.get("domain") == "opcua"
            and (
                x.get("title") == TITLE
                or ((x.get("data") or {}).get("endpoint") == OPC_ENDPOINT)
            )
        ]
        if not target:
            raise RuntimeError("Failed to find created OPC UA entry")
        entry_id = target[0]["entry_id"]

        platforms: list[tuple[str, dict, bool]] = [
            (
                "add_sensor",
                {
                    "name": "Matrix Sensor Temperature",
                    "node_id": "ns=2;s=EntityMatrix.Process.Temperature",
                    "unit_of_measurement": "°C",
                    "device_class": "temperature",
                    "state_class": "measurement",
                    "icon": "mdi:thermometer",
                },
                False,
            ),
            (
                "add_binary_sensor",
                {
                    "name": "Matrix Binary Alarm",
                    "node_id": "ns=2;s=EntityMatrix.Operation.Alarm",
                    "device_class": "problem",
                    "invert": False,
                    "icon": "mdi:alert",
                },
                False,
            ),
            (
                "add_switch",
                {
                    "name": "Matrix Switch Running",
                    "node_id": "ns=2;s=EntityMatrix.Operation.Running",
                    "invert": False,
                    "icon": "mdi:power",
                },
                False,
            ),
            (
                "add_light",
                {
                    "name": "Matrix Light Rainbow Pro",
                    "node_id": "ns=2;s=Home.Lights.RainbowPro.State",
                    "invert": False,
                    "brightness_node_id": "ns=2;s=Home.Lights.RainbowPro.Brightness",
                    "brightness_scale": 255,
                    "color_temp_node_id": "ns=2;s=Home.Lights.RainbowPro.ColorTempKelvin",
                    "color_temp_min_kelvin": 2000,
                    "color_temp_max_kelvin": 6500,
                    "hs_hue_node_id": "ns=2;s=Home.Lights.RainbowPro.Hue",
                    "hs_saturation_node_id": "ns=2;s=Home.Lights.RainbowPro.Saturation",
                    "hs_hue_scale": 360,
                    "hs_saturation_scale": 100,
                    "rgb_r_node_id": "ns=2;s=Home.Lights.RainbowPro.R",
                    "rgb_g_node_id": "ns=2;s=Home.Lights.RainbowPro.G",
                    "rgb_b_node_id": "ns=2;s=Home.Lights.RainbowPro.B",
                    "rgb_scale": 255,
                    "rgbw_r_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBW_R",
                    "rgbw_g_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBW_G",
                    "rgbw_b_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBW_B",
                    "rgbw_w_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBW_W",
                    "rgbww_r_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBWW_R",
                    "rgbww_g_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBWW_G",
                    "rgbww_b_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBWW_B",
                    "rgbww_cw_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBWW_CW",
                    "rgbww_ww_node_id": "ns=2;s=Home.Lights.RainbowPro.RGBWW_WW",
                    "white_node_id": "ns=2;s=Home.Lights.RainbowPro.White",
                    "white_scale": 255,
                    "xy_x_node_id": "ns=2;s=Home.Lights.RainbowPro.X",
                    "xy_y_node_id": "ns=2;s=Home.Lights.RainbowPro.Y",
                    "xy_scale": "1.0",
                    "effect_node_id": "ns=2;s=Home.Lights.RainbowPro.Effect",
                    "effect_list": "off,rainbow,pulse,random",
                    "transition_node_id": "ns=2;s=Home.Lights.RainbowPro.Transition",
                    "flash_node_id": "ns=2;s=Home.Lights.RainbowPro.Flash",
                    "icon": "mdi:lightbulb-group",
                },
                False,
            ),
            (
                "add_number",
                {
                    "name": "Matrix Number Speed",
                    "node_id": "ns=2;s=EntityMatrix.Process.SpeedSetpoint",
                    "number_min": 0,
                    "number_max": 4000,
                    "number_step": 1,
                    "unit_of_measurement": "rpm",
                    "icon": "mdi:speedometer",
                },
                False,
            ),
            (
                "add_select",
                {
                    "name": "Matrix Select Mode",
                    "node_id": "ns=2;s=EntityMatrix.Operation.Mode",
                    "select_options": "Idle,Run,Service",
                    "icon": "mdi:tune-variant",
                },
                False,
            ),
            (
                "add_text",
                {
                    "name": "Matrix Text Recipe",
                    "node_id": "ns=2;s=EntityMatrix.Process.RecipeName",
                    "text_max": 128,
                    "icon": "mdi:form-textbox",
                },
                False,
            ),
            (
                "add_button",
                {
                    "name": "Matrix Button Start",
                    "node_id": "ns=2;s=EntityMatrix.Control.Commands.Start",
                    "button_payload": "true",
                    "icon": "mdi:gesture-tap-button",
                },
                False,
            ),
            (
                "add_climate",
                {
                    "name": "Matrix Climate",
                    "node_id": "ns=2;s=EntityMatrix.Process.Temperature",
                    "target_node_id": "ns=2;s=EntityMatrix.Process.TemperatureSetpoint",
                    "hvac_mode_node_id": "ns=2;s=EntityMatrix.Operation.Mode",
                    "min_temp": 16,
                    "max_temp": 30,
                    "temp_step": 0.5,
                    "icon": "mdi:thermostat",
                },
                True,
            ),
            (
                "add_cover",
                {
                    "name": "Matrix Cover",
                    "node_id": "ns=2;s=EntityMatrix.Control.Cover.Position",
                    "set_position_node_id": "ns=2;s=EntityMatrix.Control.Cover.Position",
                    "open_node_id": "ns=2;s=EntityMatrix.Control.Commands.Open",
                    "close_node_id": "ns=2;s=EntityMatrix.Control.Commands.Close",
                    "invert_position": False,
                    "icon": "mdi:blinds",
                },
                True,
            ),
            (
                "add_fan",
                {
                    "name": "Matrix Fan",
                    "node_id": "ns=2;s=EntityMatrix.Operation.Running",
                    "speed_node_id": "ns=2;s=EntityMatrix.Process.SpeedSetpoint",
                    "invert": False,
                    "icon": "mdi:fan",
                },
                True,
            ),
            (
                "add_scene",
                {
                    "name": "Matrix Scene",
                    "node_id": "ns=2;s=EntityMatrix.Control.Commands.SceneActivate",
                    "scene_activate_value": "true",
                    "icon": "mdi:palette",
                },
                True,
            ),
            (
                "add_date",
                {
                    "name": "Matrix Date",
                    "node_id": "ns=2;s=EntityMatrix.Operation.LastStartUtc",
                    "icon": "mdi:calendar",
                },
                True,
            ),
            (
                "add_datetime",
                {
                    "name": "Matrix DateTime",
                    "node_id": "ns=2;s=EntityMatrix.Operation.LastStartUtc",
                    "icon": "mdi:calendar-clock",
                },
                True,
            ),
            (
                "add_time",
                {
                    "name": "Matrix Time",
                    "node_id": "ns=2;s=EntityMatrix.Operation.LastStartUtc",
                    "icon": "mdi:clock-outline",
                },
                True,
            ),
            (
                "add_weather",
                {
                    "name": "Matrix Weather",
                    "node_id": "ns=2;s=EntityMatrix.Process.Temperature",
                    "humidity_node_id": "ns=2;s=EntityMatrix.Process.Humidity",
                    "pressure_node_id": "ns=2;s=EntityMatrix.Process.Pressure",
                    "wind_speed_node_id": "ns=2;s=EntityMatrix.Process.WindSpeed",
                    "condition_node_id": "ns=2;s=EntityMatrix.Weather.Condition",
                    "icon": "mdi:weather-partly-cloudy",
                },
                True,
            ),
            (
                "add_notify",
                {
                    "name": "Matrix Notify",
                    "node_id": "ns=2;s=EntityMatrix.Diagnostics.Message",
                    "message_node_id": "ns=2;s=EntityMatrix.Diagnostics.Message",
                    "title_node_id": "ns=2;s=EntityMatrix.Diagnostics.Title",
                    "icon": "mdi:message-alert",
                },
                True,
            ),
        ]

        for step_id, payload, advanced in platforms:
            await add_platform(entry_id, step_id, payload, advanced=advanced)

        await page.wait_for_timeout(12000)
        states = await call_api("GET", "states")
        names = {
            str((s.get("attributes") or {}).get("friendly_name", "")) for s in states
        }

        missing = []
        for _step_id, payload, _ in platforms:
            expected_name = payload["name"]
            if expected_name not in names:
                missing.append(expected_name)

        matrix_states = [
            s.get("entity_id")
            for s in states
            if "matrix"
            in str((s.get("attributes") or {}).get("friendly_name", "")).lower()
        ]

        print(f"ENTRY_ID={entry_id}")
        print(f"ENDPOINT={OPC_ENDPOINT}")
        print(f"MATRIX_STATE_COUNT={len(matrix_states)}")
        print(f"MATRIX_STATES_SAMPLE={matrix_states[:20]}")
        print(f"MISSING={missing}")
        if missing:
            raise SystemExit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
