#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

from playwright.async_api import async_playwright

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_USER = os.getenv("HA_USER", "admin")
HA_PASS = os.getenv("HA_PASS", "Admin123")
OPC_ENDPOINT_1 = os.getenv("OPC_ENDPOINT_1", "opc.tcp://127.0.0.1:4840")
OPC_ENDPOINT_2 = os.getenv("OPC_ENDPOINT_2", "opc.tcp://127.0.0.1:4842")


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

        async def ensure_opc_entry(endpoint: str, title: str) -> str:
            entries = await call_api("GET", "config/config_entries/entry")
            existing = [
                x
                for x in entries
                if x.get("domain") == "opcua" and ((x.get("data") or {}).get("endpoint") == endpoint)
            ]
            if existing:
                return existing[0]["entry_id"]

            init = await call_api("POST", "config/config_entries/flow", {"handler": "opcua"})
            flow_id = init["flow_id"]
            created = await call_api(
                "POST",
                f"config/config_entries/flow/{flow_id}",
                {
                    "title": title,
                    "endpoint": endpoint,
                    "security_policy": "None",
                    "scan_interval": 2,
                    "validate_on_save": False,
                    "notify_enabled": True,
                    "notify_service": "persistent_notification.create",
                    "notify_title_prefix": "OPC-UA",
                    "notify_keywords": "alarm,warning,fault,error",
                },
            )
            if created.get("type") not in {"create_entry", "abort"}:
                raise RuntimeError(f"Create entry failed for {endpoint}: {created}")

            entries = await call_api("GET", "config/config_entries/entry")
            for row in entries:
                if row.get("domain") == "opcua" and ((row.get("data") or {}).get("endpoint") == endpoint):
                    return row["entry_id"]
            raise RuntimeError(f"Entry not found after create for {endpoint}")

        await page.goto(HA_URL)
        await page.wait_for_timeout(1500)
        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', HA_USER)
            await page.fill('input[name="password"]', HA_PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3500)

        entry1 = await ensure_opc_entry(OPC_ENDPOINT_1, "OPC UA Core Simulator")
        entry2 = await ensure_opc_entry(OPC_ENDPOINT_2, "OPC UA Entity Matrix")

        print(f"BOUND_ENDPOINT_1={OPC_ENDPOINT_1} ENTRY_ID={entry1}")
        print(f"BOUND_ENDPOINT_2={OPC_ENDPOINT_2} ENTRY_ID={entry2}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
