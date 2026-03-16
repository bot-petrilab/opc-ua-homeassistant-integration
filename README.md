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

There are two standard test servers plus security-focused test servers:

- `testbed/opcua-sim/server_all_entities.py` (port `4840`): all data types + all entity types supported by the integration
- `testbed/opcua-sim/server_device_split.py` (port `4842`): data types + light objects split across multiple devices (`DeviceType` / `LightType` via HasTypeDefinition)
- `testbed/opcua-sim/server_basic256.py` (port `4850`): security test server (`Basic256Sha256_SignAndEncrypt`)
- `testbed/opcua-sim/server_basic256_userpass.py` (port `4851`): security + required username/password

Helper scripts:
- `tests/ha_opcua_regression/setup_entity_matrix_entry.py` binds the all-entities server in Home Assistant and creates all platform entities
- `tests/ha_opcua_regression/setup_two_server_entries.py` binds both standard servers (`4840`, `4842`) in Home Assistant

## Tests

- Home Assistant-style component tests (pytest layout): `tests/components/opcua/`
  - `__init__.py`, `conftest.py`, `test_init.py`, `test_*.py`
- Local UI/E2E regression tests: `tests/ha_opcua_regression/README.md`

## CI

GitHub Actions workflow runs:
- JSON validation
- Python compile checks
- OPC-UA smoke test (`tests/ci_smoke.py`)
