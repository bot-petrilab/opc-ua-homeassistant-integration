# OPC-UA → Home Assistant Core PR Prep

Status: 2026-03-10

## Goal
Prepare the existing `opcua` integration for a PR against `home-assistant/core`.

---

## Current implementation status (done)

- Domain: `opcua`
- Config entry + config flow + options flow implemented
- Runtime based on `DataUpdateCoordinator`
- Platforms implemented:
  - `sensor`, `binary_sensor`, `switch`, `light`
  - `button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`
- OPC-UA discovery/browse/auto-mapping implemented
- Security policy support:
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- Notification bridge event: `opcua_notification`

## Verified tests (local)

- `tests/ha_opcua_regression/run_full_e2e_matrix.sh` (endpoints 4840/4842) → PASS
- `tests/ha_opcua_regression/setup_entity_matrix_entry.py` → PASS
- `tests/ha_opcua_regression/entity_matrix_service_actions_check.py` → PASS
  - `number.set_value`, `date.set_value`, `time.set_value`, `fan.turn_on`
- `pytest tests/components/opcua -q` → PASS
- `tests/ci_smoke.py` → PASS

## Verified CI (repo)

- GitHub Actions run passes (latest main)

---

## Required work for actual Core PR (still open)

> These items are critical for merge readiness in `home-assistant/core`.

1. **Move code into Core structure**
   - From: `custom_components/opcua/*`
   - To: `homeassistant/components/opcua/*`

2. **Complete Core-style test suite**
   - [x] `tests/components/opcua/test_config_flow.py`
   - [x] `tests/components/opcua/test_init.py`
   - [ ] `tests/components/opcua/test_coordinator.py`
   - [x] `tests/components/opcua/test_<platform>.py` (all currently supported platforms present)

3. **Core artifacts/standards review**
   - [x] Diagnostics (`diagnostics.py`) implemented
   - [x] Repairs/issue handling for actionable secure-config problems
   - [ ] Polish translation keys/strings to Core review quality

4. **Remove smoke-only helper code**
   - [ ] Remove `Platform` fallback in `const.py` before Core PR.

5. **Define a minimal reviewable scope**
   - Recommendation: initial Core PR with smaller platform scope (`sensor`, `binary_sensor`, `switch`, `light`) and follow-up PRs for additional platform types.

---

## Recommended PR strategy

### Option A (recommended): staged
1. PR 1: base integration + core platforms + strong Core tests
2. PR 2+: additional platforms (`climate`, `cover`, `fan`, ...)

### Option B: full scope
- everything in one PR, with significantly higher review risk.

---

## PR text (draft)

**Title**
`Add OPC-UA integration (config entry based) with coordinator runtime`

**Summary**
- Adds new `opcua` integration with config entries.
- Uses `asyncua` client manager + `DataUpdateCoordinator`.
- Supports secure connection policies (`Basic256Sha256_Sign`, `Basic256Sha256_SignAndEncrypt`).
- Includes discovery/browse-based entity onboarding.
- Adds initial platform support + tests.

**Why**
- Enables native OPC-UA-based industrial/PLC telemetry and control in Home Assistant.

---

## Quick verification commands

```bash
cd /home/user/.openclaw/workspace
tests/ha_opcua_regression/run.sh
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/platform_coverage_check.py
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/notification_e2e_check.py
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/security_configflow_check.py
```
nclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/security_configflow_check.py
```
penclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/security_configflow_check.py
```
