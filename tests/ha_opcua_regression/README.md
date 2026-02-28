# UI Regression Tests (Playwright)

Run these tests after each integration change.

## Covers

- Login + Integrations dashboard
- Add-Integration dialog finds **OPC-UA**
- Config entry create flow
- Options flow features:
  - Discover servers
  - Browse nodes
  - Auto discovery
  - Stack-light profile
  - Light add
- Entity creation + light service toggle

## Run

```bash
cd <repo-root>
python3 -m venv .venv-playwright
.venv-playwright/bin/pip install playwright
.venv-playwright/bin/playwright install chromium

tests/ha_opcua_regression/run.sh
```
