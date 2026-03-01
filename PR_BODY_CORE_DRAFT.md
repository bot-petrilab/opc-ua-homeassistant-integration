# Draft PR Body – Home Assistant Core (`opcua`)

## Summary

Adds a new config-entry-based `opcua` integration for Home Assistant Core.

### Included

- Config flow + options flow
- DataUpdateCoordinator runtime
- Discovery + browse-assisted onboarding
- Security policy support
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- Notification bridge event: `opcua_notification`
- Platform support:
  - `sensor`, `binary_sensor`, `switch`, `light`
  - `button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`

## Why

OPC-UA is a common industrial protocol (PLC, SCADA, machine telemetry/control). A native integration enables direct, standardized industrial connectivity in Home Assistant.

## Architecture / Core fit

- Uses config entries and UI setup
- Uses async runtime with coordinator pattern
- Uses entity platform forwarding in `async_setup_entry`
- Supports unload/reload lifecycle

## Validation

- Local regression suite passing
- Platform coverage test passing
- Security configflow check passing
- CI smoke passing

## Notes for reviewer

- This integration currently exists as a custom integration reference implementation.
- For upstreaming, paths should be moved to `homeassistant/components/opcua` and tests mirrored under `tests/components/opcua`.
- See prep docs in repository root:
  - `PR_PREP_HOME_ASSISTANT_CORE.md`
  - `CORE_PR_CHECKLIST.md`
