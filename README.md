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

Es gibt **genau zwei** Test-Server:

- `testbed/opcua-sim/server_all_entities.py` (Port `4840`): alle Datentypen + alle von der Integration unterstützten Entity-Typen
- `testbed/opcua-sim/server_device_split.py` (Port `4842`): Datentypen + Lichtobjekte über mehrere Geräte (`DeviceType` / `LightType` via HasTypeDefinition)

Hilfsskripte:
- `tests/ha_opcua_regression/setup_entity_matrix_entry.py` bindet den All-Entities-Server in Home Assistant ein und erstellt alle Plattform-Entities
- `tests/ha_opcua_regression/setup_two_server_entries.py` bindet beide Standard-Server (`4840`, `4842`) in Home Assistant an

## Tests

- Home Assistant-style component tests (pytest layout): `tests/components/opcua/`
  - `__init__.py`, `conftest.py`, `test_init.py`, `test_*.py`
- Local UI/E2E regression tests: `tests/ha_opcua_regression/README.md`

## CI

GitHub Actions workflow runs:
- JSON validation
- Python compile checks
- OPC-UA smoke test (`tests/ci_smoke.py`)
