# Home Assistant Core PR Checklist – OPC-UA

References:
- Core architecture: https://developers.home-assistant.io/docs/architecture/core/
- Config entries: https://developers.home-assistant.io/docs/config_entries_index/
- Config flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- Options flow: https://developers.home-assistant.io/docs/config_entries_options_flow_handler/
- Quality scale: https://developers.home-assistant.io/docs/core/integration-quality-scale/
- Checklist: https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/

## Bronze (PR MVP)

- [x] `config_flow` – UI setup is implemented
- [x] `unique_config_entry` – duplicate entries are prevented
- [x] `runtime_data` – uses `ConfigEntry.runtime_data`
- [x] `test_before_setup` – setup validates connection (`ConfigEntryNotReady`)
- [x] `appropriate_polling` – coordinator interval is configurable
- [x] `entity_unique_id` – unique IDs per entity
- [x] `config_entry_unloading` – unload is implemented
- [x] `discovery` – zeroconf + discovery flows are implemented
- [x] `config-flow-test-coverage` – pytest coverage exists in `tests/components/opcua` (`test_config_flow.py` + split platform tests)
- [ ] `brands` – verify brand assets in `core/brands` (separate PR/asset path)
- [ ] `has_entity_name` – validate per platform and align where needed
- [ ] `docs-*` – finalize end-user docs in core-docs style

## Silver/Gold preparation

- [ ] Reauth flow (if auth is relevant)
- [ ] Diagnostics (`diagnostics.py`)
- [ ] Repairs issues for user intervention
- [ ] Higher unit test coverage (>95% in integration module)

## Technical PR preparation

- [ ] Move code to Core structure: `homeassistant/components/opcua`
- [ ] Remove standalone smoke helpers (e.g. `Platform` fallback in `const.py`)
- [ ] Run core lint/typing locally (inside core repo)
- [ ] Run core pytest for `tests/components/opcua/*`
- [ ] Submit PR with Bronze checklist + links to tests/code

## Recommended submission strategy

1. **PR 1 (MVP/Bronze):** config flow + coordinator + core platforms + core tests
2. **PR 2+:** extended platforms (`climate`, `cover`, `weather`, ...)

This significantly reduces review risk.
