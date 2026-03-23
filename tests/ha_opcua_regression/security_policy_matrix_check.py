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
                      let e = null;
                      try { e = JSON.parse(JSON.stringify(err)); } catch(_) { e = String(err); }
                      return JSON.stringify({ok:false,err:e});
                    }
                }""",
                {"m": method, "p": path, "d": data},
            )
            obj = json.loads(raw)
            if not obj.get("ok"):
                raise RuntimeError(f"API {method} {path} failed: {obj.get('err')}")
            return obj["out"]

        async def cleanup_entries() -> None:
            entries = await api("GET", "config/config_entries/entry")
            for e in [x for x in entries if x.get("domain") == "opcua"]:
                try:
                    await api("DELETE", f"config/config_entries/entry/{e['entry_id']}")
                except Exception:
                    pass

        async def start_user_flow() -> dict:
            for _ in range(3):
                init = await api(
                    "POST", "config/config_entries/flow", {"handler": "opcua"}
                )
                if (
                    init.get("type") == "abort"
                    and init.get("reason") == "already_in_progress"
                ):
                    flow_id = init.get("flow_id")
                    if flow_id:
                        try:
                            await api("DELETE", f"config/config_entries/flow/{flow_id}")
                        except Exception:
                            pass
                    continue
                return init
            return init

        async def submit_and_find_entry(payload: dict) -> tuple[dict, str | None]:
            init = await start_user_flow()
            flow_id = init.get("flow_id")
            if init.get("step_id") != "user" or not flow_id:
                raise RuntimeError(f"Unexpected flow init response: {init}")

            result = await api("POST", f"config/config_entries/flow/{flow_id}", payload)
            created_entry_id = (
                ((result.get("result") or {}).get("entry_id"))
                if isinstance(result, dict)
                else None
            )
            if created_entry_id:
                return result, created_entry_id

            entries = await api("GET", "config/config_entries/entry")
            created = [
                x
                for x in entries
                if x.get("domain") == "opcua"
                and ((x.get("data") or {}).get("endpoint") == payload.get("endpoint"))
            ]
            return result, (created[0]["entry_id"] if created else None)

        cases: list[tuple[str, dict, str]] = [
            (
                "none_create",
                {
                    "title": "Security None",
                    "endpoint": ENDPOINT,
                    "security_policy": "None",
                        "validate_on_save": False,
                },
                "create",
            ),
            (
                "sign_missing_cert_key",
                {
                    "title": "Security Sign Missing",
                    "endpoint": ENDPOINT,
                    "security_policy": "Basic256Sha256_Sign",
                        "validate_on_save": False,
                },
                "errors_required",
            ),
            (
                "signencrypt_missing_cert_key",
                {
                    "title": "Security SignEnc Missing",
                    "endpoint": ENDPOINT,
                    "security_policy": "Basic256Sha256_SignAndEncrypt",
                        "validate_on_save": False,
                },
                "errors_required",
            ),
            (
                "sign_create_with_paths",
                {
                    "title": "Security Sign",
                    "endpoint": ENDPOINT,
                    "security_policy": "Basic256Sha256_Sign",
                    "client_cert_path": "/tmp/opcua-client-cert.pem",
                    "client_key_path": "/tmp/opcua-client-key.pem",
                        "validate_on_save": False,
                },
                "create",
            ),
            (
                "signencrypt_create_with_paths",
                {
                    "title": "Security SignEnc",
                    "endpoint": ENDPOINT,
                    "security_policy": "Basic256Sha256_SignAndEncrypt",
                    "client_cert_path": "/tmp/opcua-client-cert.pem",
                    "client_key_path": "/tmp/opcua-client-key.pem",
                    "server_cert_path": "/tmp/opcua-server-cert.pem",
                        "validate_on_save": False,
                },
                "create",
            ),
        ]

        failures: list[str] = []

        for name, payload, expected in cases:
            await cleanup_entries()
            result, entry_id = await submit_and_find_entry(payload)

            if expected == "create":
                if result.get("type") not in {"create_entry", "abort"} or not entry_id:
                    failures.append(
                        f"{name}: expected create_entry/abort+entry, got result={result} entry_id={entry_id}"
                    )
                else:
                    await api("DELETE", f"config/config_entries/entry/{entry_id}")
            elif expected == "errors_required":
                errs = result.get("errors") or {}
                if (
                    errs.get("client_cert_path") != "required"
                    or errs.get("client_key_path") != "required"
                ):
                    failures.append(
                        f"{name}: expected required cert/key errors, got {result}"
                    )

        if failures:
            for f in failures:
                print(f)
            raise RuntimeError("security_policy_matrix_check: FAIL")

        print("security_policy_matrix_check: PASS")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
