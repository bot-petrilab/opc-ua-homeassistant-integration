# Changelog

## 0.8.0
- Added built-in OPC-UA notification bridge:
  - Fires Home Assistant event: `opcua_machine_notification`
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
