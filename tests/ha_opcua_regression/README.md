# HA OPC UA Regression Test (Reusable)

Run after every integration change.

## What it validates

- Login + Integrations dashboard reachable
- Add-Integration dialog finds **OPC-UA**
- Config entry can be created
- Options menu contains expected features
- Discover servers flow works
- Browse nodes flow reaches tree selection menu
- Auto-discovery can scan/apply
- Stack light profile can be applied
- Entities are created for endpoint
- Light service toggle works (`on`/`off`)
- Optional platform matrix test validates KNX-style platform coverage (`button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`)

## Run

```bash
cd /home/user/.openclaw/workspace
tests/ha_opcua_regression/run.sh
```

Optional additional platform matrix test:

```bash
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/platform_coverage_check.py
```

## Env vars (optional)

- `HA_URL` (default `http://localhost:8123`)
- `HA_USER` (default `admin`)
- `HA_PASS` (default `Admin123`)
- `OPC_ENDPOINT` (default `opc.tcp://127.0.0.1:4840`)
- `OUT_DIR` (default `tests/ha_opcua_regression/out`)

## Output

Artifacts per run in timestamp folder:

- `summary.txt`
- `report.json`
- screenshots (`*.png`)
