# Changelog

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
