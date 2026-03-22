# Home Assistant Integration Quality Scale Checklist – OPC-UA

References:
- Quality scale: https://developers.home-assistant.io/docs/core/integration-quality-scale/
- Checklist: https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/
- Rules: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/

## Bronze (completed)

- [x] `config_flow` – UI setup implemented
- [x] `unique_config_entry` – duplicate entries are prevented
- [x] `runtime_data` – uses `ConfigEntry.runtime_data`
- [x] `test_before_setup` – setup validates connection (`ConfigEntryNotReady` / auth-aware handling)
- [x] `appropriate_polling` – coordinator interval configurable (including sub-second)
- [x] `entity_unique_id` – unique IDs per entity
- [x] `config_entry_unloading` – unload implemented
- [x] `discovery` – zeroconf + discovery flows implemented
- [x] `config-flow-test-coverage` – test coverage exists (`test_config_flow.py` + split tests)
- [x] `brands` – integration includes brand assets (custom integration context)
- [x] `has_entity_name` – base entity sets `has_entity_name`
- [x] `docs-*` – README/testbed/regression guides completed in English

## Silver/Gold prep items completed in this repository

- [x] Reauth flow implemented (`async_step_reauth` + `async_step_reauth_confirm`)
- [x] Diagnostics implemented (`diagnostics.py`) with sensitive-data redaction
- [x] Repairs implemented for actionable secure-configuration issues (`repairs.py` + issue strings)
- [x] Repairs-style auth handling path in setup (`ConfigEntryAuthFailed` on auth/security failures)
- [x] Extended unit tests and smoke validation

## Test status

- [x] `pytest tests/components/opcua -q` → PASS (`123 passed` at latest verified local run)
- [x] `coverage run -m pytest tests/components/opcua -q` → PASS
- [x] `ruff check custom_components/opcua tests/components/opcua tests/ci_smoke.py` → PASS
- [x] `tests/ci_smoke.py` → PASS

## Notes

This checklist tracks Quality Scale implementation status for the standalone/custom integration repository.
Core-repo migration/submission tasks are tracked separately in PR prep documents.
