#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os

from asyncua import Client
from playwright.async_api import async_playwright

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_USER = os.getenv("HA_USER", "admin")
HA_PASS = os.getenv("HA_PASS", "Admin123")
ENDPOINT = os.getenv("OPC_ENDPOINT", "opc.tcp://127.0.0.1:4840")
ALARM_NODE = "ns=2;s=Machine.Operation.Alarm"


async def set_alarm(value: bool) -> None:
    c = Client(ENDPOINT)
    await c.connect()
    try:
        node = c.get_node(ALARM_NODE)
        await node.write_value(value)
    finally:
        await c.disconnect()


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

        await page.goto(HA_URL)
        await page.wait_for_timeout(1500)
        if await page.locator('input[name="username"]').count() > 0:
            await page.fill('input[name="username"]', HA_USER)
            await page.fill('input[name="password"]', HA_PASS)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3500)

        # clean old test entries
        entries = await call_api("GET", "config/config_entries/entry")
        for e in [
            x
            for x in entries
            if str(x.get("domain", "")).startswith("opcua")
            and x.get("title") == "OPC-UA Notify Test"
        ]:
            try:
                await call_api("DELETE", f"config/config_entries/entry/{e['entry_id']}")
            except Exception:
                pass

        # create new entry with notify enabled
        init = await call_api(
            "POST", "config/config_entries/flow", {"handler": "opcua"}
        )
        flow_id = init["flow_id"]
        created = await call_api(
            "POST",
            f"config/config_entries/flow/{flow_id}",
            {
                "title": "OPC-UA Notify Test",
                "endpoint": ENDPOINT,
                "security_policy": "None",
                "scan_interval": 1,
                "validate_on_save": False,
                "notify_enabled": True,
                "notify_service": "persistent_notification.create",
                "notify_title_prefix": "OPC-UA",
                "notify_keywords": "alarm,warning,fault,error",
            },
        )
        if created.get("type") not in {"create_entry", "abort"}:
            raise RuntimeError(f"Unexpected create result: {created}")

        entries2 = await call_api("GET", "config/config_entries/entry")
        entry = next(
            x
            for x in entries2
            if x.get("domain") == "opcua" and x.get("title") == "OPC-UA Notify Test"
        )
        entry_id = entry["entry_id"]

        # add alarm binary sensor node
        opt_init = await call_api(
            "POST", "config/config_entries/options/flow", {"handler": entry_id}
        )
        fid = opt_init["flow_id"]
        await call_api(
            "POST",
            f"config/config_entries/options/flow/{fid}",
            {"next_step_id": "add_binary_sensor"},
        )
        await call_api(
            "POST",
            f"config/config_entries/options/flow/{fid}",
            {
                "name": "Alarm Notify Node",
                "node_id": ALARM_NODE,
                "device_class": "problem",
                "invert": False,
            },
        )

        # baseline states
        states_before = await call_api("GET", "states")
        notif_before = [
            s
            for s in states_before
            if s.get("entity_id", "").startswith("persistent_notification.")
        ]

        # trigger false -> true
        await set_alarm(False)
        await asyncio.sleep(1.5)
        await set_alarm(True)
        await asyncio.sleep(2.5)

        states_after = await call_api("GET", "states")
        notif_after = [
            s
            for s in states_after
            if s.get("entity_id", "").startswith("persistent_notification.")
        ]

        # find a matching notification message
        matched = []
        for s in notif_after:
            attrs = s.get("attributes") or {}
            msg = str(attrs.get("message") or "")
            if ALARM_NODE in msg and ENDPOINT in msg:
                matched.append(s.get("entity_id"))

        ok_count = len(notif_after) >= len(notif_before)
        ok_match = len(matched) > 0

        print("notification_count_before", len(notif_before))
        print("notification_count_after", len(notif_after))
        print("matched_notifications", matched)
        print("NOTIFICATION_TEST_PASS", bool(ok_count and ok_match))

        if not (ok_count and ok_match):
            raise SystemExit(1)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
