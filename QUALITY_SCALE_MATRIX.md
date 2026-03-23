# OPC-UA Integration Quality Scale Matrix

References:
- https://developers.home-assistant.io/docs/core/integration-quality-scale/
- https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist
- https://developers.home-assistant.io/docs/core/integration-quality-scale/rules

This matrix tracks implementation state in this repository.

## Bronze
- [x] action-setup *(N/A: no custom domain service actions; uses entity platform services)*
- [x] appropriate-polling *(N/A: runtime is subscription-driven rather than polling-based)*
- [x] brands
- [x] common-modules
- [x] config-flow-test-coverage
- [x] config-flow
  - [x] Uses data_description to give context to fields
  - [x] Uses ConfigEntry.data and ConfigEntry.options correctly
- [x] dependency-transparency
- [x] docs-actions
- [x] docs-high-level-description
- [x] docs-installation-instructions
- [x] docs-removal-instructions
- [x] entity-event-setup *(N/A: no event-subscribing entities in runtime model)*
- [x] entity-unique-id
- [x] has-entity-name
- [x] runtime-data
- [x] test-before-configure
- [x] test-before-setup
- [x] unique-config-entry

## Silver
- [x] action-exceptions *(N/A: no custom domain service actions)*
- [x] config-entry-unloading
- [x] docs-configuration-parameters
- [x] docs-installation-parameters
- [x] entity-unavailable
- [x] integration-owner
- [x] log-when-unavailable
- [x] parallel-updates
- [x] reauthentication-flow
- [ ] test-coverage *(in progress: local measured coverage currently below 95%)*

## Gold
- [x] devices
- [x] diagnostics
- [x] discovery-update-info
- [x] discovery
- [x] docs-data-update
- [x] docs-examples
- [x] docs-known-limitations
- [x] docs-supported-devices
- [x] docs-supported-functions
- [x] docs-troubleshooting
- [x] docs-use-cases
- [x] dynamic-devices
- [x] entity-category *(N/A: no diagnostic/config helper entities currently exposed)*
- [x] entity-device-class
- [x] entity-disabled-by-default *(N/A: no noisy helper entities currently created by default)*
- [x] entity-translations
- [x] exception-translations
- [x] icon-translations
- [x] reconfiguration-flow
- [x] repair-issues *(actionable Home Assistant repair issue for missing secure certificate files + auth/security handling paths)*
- [x] stale-devices *(device mapping by explicit config context; stale cleanup via config entry lifecycle)*

## Platinum
- [x] async-dependency
- [x] inject-websession *(N/A: OPC-UA dependency does not use HTTP client sessions)*
- [x] strict-typing
