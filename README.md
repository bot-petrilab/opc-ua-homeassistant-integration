# OPC-UA Custom Integration for Home Assistant

Custom Home Assistant integration (domain: `opcua`) with display name **OPC-UA**.

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

- `testbed/opcua-sim/server.py` provides a rich OPC-UA simulator model.
- `testbed/opcua-sim/server_entity_matrix.py` provides an all-platform matrix model (including advanced platform mappings/options).
- `tests/ha_opcua_regression/setup_entity_matrix_entry.py` can automatically bind the matrix server into Home Assistant and create one entity for each supported platform.

## Tests

- Home Assistant-style component tests (pytest layout): `tests/components/opcua/`
  - `__init__.py`, `conftest.py`, `test_init.py`, `test_*.py`
- Local UI/E2E regression tests: `tests/ha_opcua_regression/README.md`

## CI

GitHub Actions workflow runs:
- JSON validation
- Python compile checks
- OPC-UA smoke test (`tests/ci_smoke.py`)
