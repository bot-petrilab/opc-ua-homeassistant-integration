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

        # Cleanup previous runs
        entries = await call_api("GET", "config/config_entries/entry")
        for e in [
            x
            for x in entries
            if x.get("domain") == "opcua"
            and (x.get("title") == TITLE or ((x.get("data") or {}).get("endpoint") == OPC_ENDPOINT))
        ]:
            try:
                await call_api("DELETE", f"config/config_entries/entry/{e['entry_id']}")
            except Exception:
                pass

        # Create base integration entry
        init = await call_api("POST", "config/config_entries/flow", {"handler": "opcua"})
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
                "notify_title_prefix": "OPC-UA LightType",
                "notify_keywords": "light,alarm,warning,fault,error",
            },
        )
        if created.get("type") not in {"create_entry", "abort"}:
            raise RuntimeError(f"Unexpected create result: {created}")

        entries = await call_api("GET", "config/config_entries/entry")
        target = [
            x
            for x in entries
            if x.get("domain") == "opcua"
            and (x.get("title") == TITLE or ((x.get("data") or {}).get("endpoint") == OPC_ENDPOINT))
        ]
        if not target:
            raise RuntimeError("Failed to find created OPC UA entry")
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

        # robust check for this integration: friendly names from simulator objects
        expected = {"Matrix Main", "Corridor"}
        found = {
            str((s.get("attributes") or {}).get("friendly_name", ""))
            for s in states
            if str(s.get("entity_id", "")).startswith("light.")
        }

        missing = sorted(list(expected - found))

        print(f"ENTRY_ID={entry_id}")
        print(f"ENDPOINT={OPC_ENDPOINT}")
        print(f"FOUND_LIGHTS={sorted(list(found))}")
        print(f"MISSING={missing}")

        if missing:
            raise SystemExit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
