#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from datetime import date, datetime

from playwright.async_api import async_playwright

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_USER = os.getenv("HA_USER", "admin")
HA_PASS = os.getenv("HA_PASS", "Admin123")


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

        results: list[tuple[str, bool, str]] = []

        async def service_test(
            name: str, domain: str, service: str, data: dict
        ) -> None:
            try:
                await call_api("POST", f"services/{domain}/{service}", data)
                results.append((name, True, "ok"))
            except Exception as err:
                results.append((name, False, str(err)))

        await service_test(
            "number.set_value",
            "number",
            "set_value",
            {"entity_id": "number.matrix_number_speed", "value": 1234},
        )

        await service_test(
            "date.set_value",
            "date",
            "set_value",
            {"entity_id": "date.matrix_date", "date": date.today().isoformat()},
        )

        await service_test(
            "fan.turn_on",
            "fan",
            "turn_on",
            {"entity_id": "fan.matrix_fan"},
        )

        await service_test(
            "time.set_value",
            "time",
            "set_value",
            {
                "entity_id": "time.matrix_time",
                "time": datetime.now().strftime("%H:%M:%S"),
            },
        )

        await page.wait_for_timeout(2000)

        states = await call_api("GET", "states")
        state_map = {s.get("entity_id"): s for s in states if s.get("entity_id")}

        print("SERVICE_RESULTS")
        failed = False
        for name, ok, msg in results:
            print(f"- {name}: {'PASS' if ok else 'FAIL'} {msg}")
            if not ok:
                failed = True

        print("STATE_SNAPSHOT")
        for eid in [
            "number.matrix_number_speed",
            "date.matrix_date",
            "fan.matrix_fan",
            "time.matrix_time",
        ]:
            s = state_map.get(eid, {})
            print(f"- {eid}: state={s.get('state')} attrs={s.get('attributes')}")

        await browser.close()

        if failed:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
