#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

from playwright.async_api import async_playwright

URL = os.getenv("HA_URL", "http://localhost:8123")
USER = os.getenv("HA_USER", "admin")
PASS = os.getenv("HA_PASS", "Admin123")
ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4840")
TITLE = "OPC UA AddRemove Test"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(45000)

        await page.goto(URL)
        await page.wait_for_timeout(1200)

        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', USER)
            await page.fill('input[name="password"]', PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)

        async def api(method: str, path: str, data=None):
            raw = await page.evaluate(
                """async (a) => {
                    const ha = document.querySelector('home-assistant');
                    try {
                      const out = await ha.hass.callApi(a.m, a.p, a.d || undefined);
                      return JSON.stringify({ok:true,out});
                    } catch (err) {
                      return JSON.stringify({ok:false,err});
                    }
                }""",
                {"m": method, "p": path, "d": data},
            )
            obj = json.loads(raw)
            if not obj.get("ok"):
                raise RuntimeError(f"API {method} {path} failed: {obj.get('err')}")
            return obj["out"]

        # Cleanup before test (all opcua entries to avoid endpoint uniqueness collisions)
        entries = await api("GET", "config/config_entries/entry")
        for e in [x for x in entries if x.get("domain") == "opcua"]:
            await api("DELETE", f"config/config_entries/entry/{e['entry_id']}")

        # Add integration
        init = await api("POST", "config/config_entries/flow", {"handler": "opcua"})
        flow_id = init.get("flow_id")
        if init.get("step_id") != "user" or not flow_id:
            raise RuntimeError(f"Unexpected flow init response: {init}")

        result = await api(
            "POST",
            f"config/config_entries/flow/{flow_id}",
            {
                "title": TITLE,
                "endpoint": ENDPOINT,
                "security_policy": "None",
                "scan_interval": 2,
                "validate_on_save": False,
                "notify_enabled": True,
                "notify_service": "persistent_notification.create",
                "notify_title_prefix": "OPC-UA",
                "notify_keywords": "manualtest,alarm,warning,fault,error",
            },
        )
        if result.get("type") not in {"create_entry", "abort"}:
            raise RuntimeError(f"Flow submit failed: {result}")

        entries_after_add = await api("GET", "config/config_entries/entry")
        created = [
            x for x in entries_after_add
            if x.get("domain") == "opcua" and ((x.get("title") == TITLE) or ((x.get("data") or {}).get("endpoint") == ENDPOINT))
        ]
        if not created:
            raise RuntimeError("OPC UA entry was not created")

        entry_id = created[0]["entry_id"]

        # Delete integration
        await api("DELETE", f"config/config_entries/entry/{entry_id}")

        entries_after_del = await api("GET", "config/config_entries/entry")
        still_there = [x for x in entries_after_del if x.get("entry_id") == entry_id]
        if still_there:
            raise RuntimeError("OPC UA entry still exists after delete")

        print("add_remove_config_entry: PASS")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
