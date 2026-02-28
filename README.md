# OPC-UA Custom Integration for Home Assistant

Custom Home Assistant integration (domain: `opcua_machine`) with display name **OPC-UA**.

## Features

- UI config flow
- Entity platforms: sensor, binary_sensor, switch, light
- OPC-UA server discovery:
  - HA discovery prompt (zeroconf `_opcua-tcp._tcp.local.`)
  - manual discover flow (FindServers/GetEndpoints)
- OPC-UA node browser with tree navigation
- Auto-discovery mapping (native + companion-style heuristics)
- Stack-light profile helper

## Development testbed

`testbed/opcua-sim/server.py` provides a rich OPC-UA simulator model.

## Local UI regression tests

See `tests/ha_opcua_regression/README.md`.

## CI

GitHub Actions workflow runs:
- JSON validation
- Python compile checks
- OPC-UA smoke test (`tests/ci_smoke.py`)
