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


def expect(cond: bool, message: str) -> None:
    if not cond:
        raise RuntimeError(message)


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
            return await call_api("POST", "config/config_entries/options/flow", {"handler": entry_id})

        async def opt_step(flow_id: str, payload: dict):
            return await call_api("POST", f"config/config_entries/options/flow/{flow_id}", payload)

        await page.goto(HA_URL)
        await page.wait_for_timeout(1500)
        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', HA_USER)
            await page.fill('input[name="password"]', HA_PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3500)

        # cleanup
        entries = await call_api("GET", "config/config_entries/entry")
        for e in [x for x in entries if str(x.get("domain", "")).startswith("opcua") and x.get("title") == "OPC UA Platform Matrix"]:
            try:
                await call_api("DELETE", f"config/config_entries/entry/{e['entry_id']}")
            except Exception:
                pass

        # create base entry
        init = await call_api("POST", "config/config_entries/flow", {"handler": "opcua"})
        flow_id = init["flow_id"]
        created = await call_api(
            "POST",
            f"config/config_entries/flow/{flow_id}",
            {
                "title": "OPC UA Platform Matrix",
                "endpoint": OPC_ENDPOINT,
                "security_policy": "None",
                "scan_interval": 2,
                "validate_on_save": False,
                "notify_enabled": True,
                "notify_service": "persistent_notification.create",
                "notify_title_prefix": "OPC-UA",
                "notify_keywords": "manualtest,alarm,warning,fault,error",
            },
        )
        expect(created.get("type") in {"create_entry", "abort"}, f"unexpected create result: {created}")

        entries2 = await call_api("GET", "config/config_entries/entry")
        target = [
            x
            for x in entries2
            if x.get("domain") == "opcua"
            and (
                x.get("title") == "OPC UA Platform Matrix"
                or ((x.get("data") or {}).get("endpoint") == OPC_ENDPOINT)
            )
        ]
        if not target:
            target = [x for x in entries2 if x.get("domain") == "opcua"]
        expect(bool(target), "opcua entry not found after creation")
        entry_id = target[0]["entry_id"]

        platform_steps = [
            (
                "add_button",
                {
                    "name": "E2E Button",
                    "node_id": "ns=2;s=Machine.Control.Commands.Acknowledge",
                    "button_payload": "true",
                },
            ),
            (
                "add_climate",
                {
                    "name": "E2E Climate",
                    "node_id": "ns=2;s=Machine.Process.Temperature",
                    "target_node_id": "ns=2;s=Machine.Control.Setpoints.TemperatureSetpoint",
                    "hvac_mode_node_id": "ns=2;s=Machine.Operation.Mode",
                    "min_temp": 7,
                    "max_temp": 35,
                    "temp_step": 0.5,
                },
            ),
            (
                "add_cover",
                {
                    "name": "E2E Cover",
                    "node_id": "ns=2;s=Machine.Assets.Drive.AxisPosition",
                    "set_position_node_id": "ns=2;s=Machine.Assets.Drive.AxisPosition",
                    "invert_position": False,
                },
            ),
            (
                "add_date",
                {
                    "name": "E2E Date",
                    "node_id": "ns=2;s=Machine.Operation.LastStartUtc",
                },
            ),
            (
                "add_datetime",
                {
                    "name": "E2E DateTime",
                    "node_id": "ns=2;s=Machine.Operation.LastStartUtc",
                },
            ),
            (
                "add_fan",
                {
                    "name": "E2E Fan",
                    "node_id": "ns=2;s=Machine.Operation.Running",
                    "speed_node_id": "ns=2;s=Machine.Control.Setpoints.SpeedSetpoint",
                    "invert": False,
                },
            ),
            (
                "add_notify",
                {
                    "name": "E2E Notify",
                    "node_id": "ns=2;s=Machine.Diagnostics.SystemMessage",
                    "message_node_id": "ns=2;s=Machine.Diagnostics.SystemMessage",
                    "title_node_id": "ns=2;s=Machine.Process.BatchId",
                },
            ),
            (
                "add_number",
                {
                    "name": "E2E Number",
                    "node_id": "ns=2;s=Machine.Control.Setpoints.SpeedSetpoint",
                    "number_min": 0,
                    "number_max": 4000,
                    "number_step": 1,
                    "unit_of_measurement": "rpm",
                },
            ),
            (
                "add_scene",
                {
                    "name": "E2E Scene",
                    "node_id": "ns=2;s=Machine.Control.Commands.Start",
                    "scene_activate_value": "true",
                },
            ),
            (
                "add_select",
                {
                    "name": "E2E Select",
                    "node_id": "ns=2;s=Machine.Operation.Mode",
                    "select_options": "Idle,Run,Service",
                },
            ),
            (
                "add_text",
                {
                    "name": "E2E Text",
                    "node_id": "ns=2;s=Machine.Process.RecipeName",
                    "text_max": 255,
                },
            ),
            (
                "add_time",
                {
                    "name": "E2E Time",
                    "node_id": "ns=2;s=Machine.Operation.LastStartUtc",
                },
            ),
            (
                "add_weather",
                {
                    "name": "E2E Weather",
                    "node_id": "ns=2;s=Machine.Process.Temperature",
                    "humidity_node_id": "ns=2;s=Machine.Process.HumidityPct",
                    "pressure_node_id": "ns=2;s=Machine.Process.PressureBar",
                    "wind_speed_node_id": "ns=2;s=Machine.Process.FlowLMin",
                    "condition_node_id": "ns=2;s=Machine.Diagnostics.SystemMessage",
                },
            ),
        ]

        for step_id, payload in platform_steps:
            opt = await start_options_flow(entry_id)
            fid = opt["flow_id"]
            nav = await opt_step(fid, {"next_step_id": step_id})
            expect(nav.get("step_id") == step_id, f"navigation failed for {step_id}: {nav}")
            done = await opt_step(fid, payload)
            expect(done.get("step_id") == "init", f"submit failed for {step_id}: {done}")

        # wait for reloads/entities
        await page.wait_for_timeout(6000)
        states = await call_api("GET", "states")

        needed = {
            "button": "E2E Button",
            "climate": "E2E Climate",
            "cover": "E2E Cover",
            "date": "E2E Date",
            "datetime": "E2E DateTime",
            "fan": "E2E Fan",
            "notify": "E2E Notify",
            "number": "E2E Number",
            "scene": "E2E Scene",
            "select": "E2E Select",
            "text": "E2E Text",
            "time": "E2E Time",
            "weather": "E2E Weather",
        }

        missing: list[str] = []
        for domain, friendly in needed.items():
            found = any(
                str(s.get("entity_id", "")).startswith(f"{domain}.")
                and str((s.get("attributes") or {}).get("friendly_name", "")) == friendly
                for s in states
            )
            if not found:
                missing.append(f"{domain}:{friendly}")

        print("missing", missing)
        print("PLATFORM_COVERAGE_PASS", len(missing) == 0)
        if missing:
            raise SystemExit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
