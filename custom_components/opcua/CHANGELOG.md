# Changelog

## 1.0.23
- Added Home Assistant-style integration test structure under `tests/components/opcua/`:
  - `__init__.py`
  - `conftest.py`
  - `test_init.py`
  - `test_entity_writes.py`
  - `test_fan.py`
- Added focused unit tests for OPC-UA write type handling (`number`, `date`, `time`, `datetime`) and fan service behavior.
- Updated README test section to document pytest layout + existing E2E regression suite.

## 1.0.22
- Fixed `fan.turn_on` compatibility with current HA service signature by accepting `(percentage, preset_mode, **kwargs)`.
- Added targeted regression check `entity_matrix_service_actions_check.py` for `number.set_value`, `date.set_value`, `time.set_value`, and `fan.turn_on` on matrix entities.

## 1.0.21
- `server_entity_matrix.py` switched to deterministic static mode (no random autonomous value changes); values now only change on explicit client writes/commands.
- Fixed number write typing to match underlying OPC UA node types (`int`/`float`) and avoid `BadTypeMismatch` on `number.set_value`.
- Fixed `date`, `time`, and `datetime` writes to preserve OPC UA datetime node compatibility and avoid `BadTypeMismatch`/invalid time format issues.
- Enabled explicit fan `turn_on` / `turn_off` support flags in `fan` entities.

## 1.0.20
- Added a dedicated OPC UA entity-matrix simulator: `testbed/opcua-sim/server_entity_matrix.py` (endpoint `opc.tcp://127.0.0.1:4846`).
- Added `setup_entity_matrix_entry.py` to auto-bind the new test server in Home Assistant and create all supported OPC-UA entity platforms with varied options.

## 1.0.19
- Added `security_policy_matrix_check.py` to regression suite to validate config-flow behavior across all offered security policies.
- Integrated security-policy matrix check into reusable full matrix runner.
- Documented security-policy matrix usage in regression README.

## 1.0.18
- Implemented poll-speed groups (`fast`, `normal`, `slow`) with individually configurable intervals in options flow.
- Added per-node poll-profile assignment in options flow.
- Coordinator now polls nodes based on assigned group intervals (due-node scheduling) instead of one global fixed cadence.
- Added regression checks to verify poll-group persistence and per-node profile storage.

## 1.0.17
- Added cleanup of orphaned entity-registry entries when options nodes are persisted.
- Removing nodes in options flow now also removes stale entities from HA registry, avoiding "not provided by integration" leftovers.

## 1.0.16
- Fixed `remove_node` options-flow handling for multi-select values by normalizing selected IDs to strings before filtering.
- This fixes cases where selected entries appeared to be accepted but were not removed.

## 1.0.15
- Removed `companion_profiles` from auto-discovery options, schema, and translations.
- Renamed menu label from `Auto discovery (native + companion)` to `Auto discovery`.
- Removed companion-specific discovery heuristics from mapping logic.

## 1.0.14
- Removed `prefer_lights` option from auto-discovery flow and translations.
- Auto-discovery no longer maps stacklight-like booleans to `light` entities via this toggle; writable booleans are treated as switches.

## 1.0.13
- Removed `Quick setup` from options-flow main menu.
- Removed `add_stack_light_profile` step from options flow and related menu translations.
- Updated regression expectations accordingly.

## 1.0.12
- Fixed JSON syntax regression in translation files (`strings.json`, `translations/en.json`, `translations/de.json`) that caused config-flow 500 errors during integration add.
- Keeps full-subtree discovery/browse descriptions valid and loadable in Home Assistant.

## 1.0.11
- Fixed user config-flow duplicate detection to avoid `already_in_progress` collisions from concurrent discovery flows.
- Uses endpoint-based duplicate checks against existing config entries instead of unique-id in-progress aborts during manual add.

## 1.0.10
- Improved regression runner robustness on HA dashboards where `ha-fab` is unavailable (UI brand-search check is now optional/skip-safe).
- Added reusable full matrix script `tests/ha_opcua_regression/run_full_e2e_matrix.sh` for complete 3-endpoint regression runs.
- Documented reusable matrix command in regression `README.md`.

## 1.0.9
- Removed internal scan limits for options-flow discovery/browse from selected root nodes:
  - auto-discovery now runs without `depth`, `max_nodes`, and `import_limit` limits
  - browse now runs without `depth` and `max_nodes` limits
- Updated EN/DE descriptions to clearly state full-subtree scanning behavior.

## 1.0.8
- Increased internal auto-discovery defaults to work from `i=85` on deeper hierarchies across simulators: `depth=4`, `max_nodes=2000`, `import_limit=500`.
- Increased internal browse defaults to `depth=4`, `max_nodes=2000`.
- Updated EN/DE descriptions to show the new automatic defaults.

## 1.0.7
- Removed `depth`, `max_nodes`, and `import_limit` inputs from the options UI for `auto_discovery` and `browse_nodes`.
- Discovery/browse now always use built-in defaults (auto_discovery: depth=2, max_nodes=400, import_limit=200; browse: depth=2, max_nodes=200).
- Updated EN/DE descriptions so the defaults are clearly visible in the form text.

## 1.0.6
- Made `depth` and `max_nodes` optional in `auto_discovery` and `browse_nodes` forms (defaults are applied automatically).
- Improved field labels and descriptions (EN/DE) to clearly explain optional inputs and default values.

## 1.0.5
- Removed `Discover OPC UA servers` from the `Discovery & browse` menu in options flow.
- Kept discovery/browse menu focused on endpoint-internal actions (`auto_discovery`, `browse_nodes`) after setup.

## 1.0.4
- Removed leftover `done` / `Save and finish` translation entries from `en` and `de` locale files so the option no longer appears in UI labels.

## 1.0.3
- Removed `Save and finish` from options flow (KNX-like behavior with immediate persistence per action).
- Simplified options menu hierarchy so completion is implicit and navigation-focused.

## 1.0.2
- Refactored options/config flow navigation into logical grouped menus (quick setup, add entities, discovery, settings).
- Added explicit back-navigation entries across grouped menus and browse import menus.
- Updated regression flow automation to follow the new grouped menu structure.
- Added deterministic config-entry lifecycle regression test (`config_entry_add_remove_check.py`) covering add + delete of integration entries.
- Updated regression runner path handling to always execute tests from the repository-local tree.

## 1.0.1
- Fixed `date`, `datetime`, and `time` platform entity initialization (`entity_kind` argument).
- Added dedicated regression test `platform_coverage_check.py` for KNX-style platform coverage.

## 1.0.0
- Added broad platform coverage aligned with KNX platform scope:
  - `button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`
  - existing `sensor`, `binary_sensor`, `switch`, `light` retained
- Extended options flow with manual add steps for all new entity types.
- Extended browse-import flow with all new entity kinds.

## 0.9.0
- BREAKING: Integration domain is now `opcua`.
- BREAKING: Component path is now `custom_components/opcua`.
- Removed protocol-specific legacy naming from runtime identifiers for a general-purpose OPC-UA integration.

## 0.8.2
- Standardized runtime HA notification event to generic `opcua_notification`.
- Updated regression tests and docs to use `opcua_notification`.

## 0.8.1
- Fixed config-flow runtime import for notification defaults (prevents flow 500 errors when opening user step).
- Extended regression test to cover notification configuration fields and runtime `opcua_notification` event trigger.

## 0.8.0
- Added built-in OPC-UA notification bridge:
  - Fires Home Assistant event: `opcua_notification`
  - Can create notifications via configurable HA service (default `persistent_notification.create`)
  - Triggered on alarm/warning/fault-like node transitions based on keywords
- Added notification config fields in config flow

## 0.7.0
- Added security policy support for OPC-UA client:
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- Added config-flow fields for certificate/key paths and key password
- Discovery endpoint selection now maps Basic256Sha256 + mode to supported security policy values
- Discovery support marker now includes Basic256Sha256 (Sign/SignAndEncrypt)

## 0.6.0
- Integration display name renamed to **OPC-UA** (UI/flow title)
- Prepared repository/CI packaging for reusable tests

## 0.5.2
- Fixed options flow `add_light` step opening (XY scale selector compatibility)

## 0.5.1
- Fixed HA compatibility for discovery flow import (removed strict `ZeroconfServiceInfo` import)
- Restored config flow loading in current Home Assistant version

## 0.5.0
- Added discovery via Home Assistant discovery flow:
  - `async_step_zeroconf` + confirmation step
  - HA can now show discovered OPC-UA servers and ask to add
- Added manifest zeroconf registration for `_opcua-tcp._tcp.local.`
- Added "Discover OPC UA servers" option step with endpoint picker (from 0.4 flow) and polished translations

## 0.4.0
- Added server discovery flow in options:
  - Discover OPC-UA servers/endpoints via discovery URL (FindServers/GetEndpoints)
  - Optional FindServersOnNetwork probe (LDS-ME)
  - Endpoint selection updates the integration endpoint automatically
- Discovery list now shows app name + endpoint + security mode/policy
- Explicit errors for "no servers found" and unsupported security policy

## 0.3.0
- Tree-style OPC-UA browser navigation:
  - open sub-branch
  - go up one level
  - import variables from current branch
- Browser metadata improvements (node class / sample type / RO-RW)
- Auto-discovery + companion-style mapping available in options flow

## 0.2.0
- UI config flow introduced
- Initial sensor/binary_sensor/switch/light support
