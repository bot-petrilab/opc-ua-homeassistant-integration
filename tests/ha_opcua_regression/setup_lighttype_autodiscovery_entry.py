#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

from playwright.async_api import async_playwright

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_USER = os.getenv("HA_USER", "admin")
HA_PASS = os.getenv("HA_PASS", "Admin123")
OPC_ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4842")
TITLE = os.getenv("OPC_TITLE", "OPC UA LightType Discovery")


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

        async def call_ws(msg):
            raw = await page.evaluate(
                """async (msg) => {
                  const ha = document.querySelector('home-assistant');
                  try {
                    const out = await ha.hass.callWS(msg);
                    return JSON.stringify({ok: true, out});
                  } catch (err) {
                    let e = null;
                    try { e = JSON.parse(JSON.stringify(err)); } catch (_) { e = String(err); }
                    return JSON.stringify({ok: false, err: e});
                  }
                }""",
                msg,
            )
            obj = json.loads(raw)
            if not obj.get("ok"):
                raise RuntimeError(f"WS failed: {obj.get('err')}")
            return obj.get("out")

        async def start_options_flow(entry_id: str):
            return await call_api(
                "POST", "config/config_entries/options/flow", {"handler": entry_id}
            )

        async def opt_step(flow_id: str, payload: dict):
            return await call_api(
                "POST", f"config/config_entries/options/flow/{flow_id}", payload
            )

        await page.goto(HA_URL)
        await page.wait_for_timeout(1500)
        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', HA_USER)
            await page.fill('input[name="password"]', HA_PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3500)

        # Cleanup previous runs
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

        # Create base integration entry
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
                "validate_on_save": False,
            },
        )
        if created.get("type") == "form" and created.get("step_id") == "user_notifications":
            created = await call_api(
                "POST",
                f"config/config_entries/flow/{flow_id}",
                {
                    "notify_enabled": True,
                    "notify_service": "persistent_notification.create",
                    "notify_title_prefix": "OPC-UA LightType",
                    "notify_keywords": "light,alarm,warning,fault,error",
                },
            )
        if created.get("type") not in {"create_entry", "abort"}:
            raise RuntimeError(f"Unexpected create result: {created}")

        entry_id = None
        if created.get("type") == "create_entry":
            result = created.get("result") or {}
            entry_id = result.get("entry_id") if isinstance(result, dict) else None

        if not entry_id:
            await page.wait_for_timeout(1500)
            entries = await call_api("GET", "config/config_entries/entry")
            target = [
                x
                for x in entries
                if x.get("domain") == "opcua"
                and x.get("title") == TITLE
            ]
            if not target:
                target = [
                    x
                    for x in entries
                    if x.get("domain") == "opcua"
                    and x.get("title") == "OPC UA Entity Matrix"
                ]
            if not target:
                target = [x for x in entries if x.get("domain") == "opcua"]
            if not target:
                raise RuntimeError("Failed to find created or reusable OPC UA entry")
            entry_id = target[0]["entry_id"]

        # Run options flow -> auto discovery and apply discovered entities
        opt = await start_options_flow(entry_id)
        fid = opt["flow_id"]

        menu = await opt_step(fid, {"next_step_id": "menu_discovery_tools"})
        if menu.get("step_id") != "menu_discovery_tools":
            raise RuntimeError(f"menu_discovery_tools failed: {menu}")

        auto_form = await opt_step(fid, {"next_step_id": "auto_discovery"})
        if auto_form.get("step_id") != "auto_discovery":
            raise RuntimeError(f"auto_discovery navigation failed: {auto_form}")

        review = await opt_step(
            fid,
            {
                "root_node_id": "i=85",
                "include_readonly": True,
                "include_standard_nodes": False,
            },
        )
        if review.get("step_id") != "auto_discovery_review":
            raise RuntimeError(f"auto_discovery run failed: {review}")

        done = await opt_step(fid, {"apply": True})
        if done.get("step_id") != "init":
            raise RuntimeError(f"auto_discovery_review apply failed: {done}")

        await page.wait_for_timeout(8000)

        states = await call_api("GET", "states")
        devices = await call_ws({"type": "config/device_registry/list"})

        # robust check for this integration: friendly names from simulator objects
        expected = {"Matrix Main", "Corridor", "Rainbow Pro"}
        found = {
            str((s.get("attributes") or {}).get("friendly_name", ""))
            for s in states
            if str(s.get("entity_id", "")).startswith("light.")
        }
        expected_devices = {"Panel 01", "RGB Controller 01"}
        found_devices = {
            str(d.get("name_by_user") or d.get("name") or "")
            for d in devices
            if str(d.get("manufacturer") or "") == "Petri Automation"
        }

        missing = sorted(list(expected - found))
        missing_devices = sorted(list(expected_devices - found_devices))

        print(f"ENTRY_ID={entry_id}")
        print(f"ENDPOINT={OPC_ENDPOINT}")
        print(f"FOUND_LIGHTS={sorted(list(found))}")
        print(f"FOUND_DEVICES={sorted(list(found_devices))}")
        print(f"MISSING={missing}")
        print(f"MISSING_DEVICES={missing_devices}")

        if missing or missing_devices:
            raise SystemExit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
