# OPC-UA (Custom Integration for Home Assistant)

This integration uses **opcua-asyncio** (`asyncua`) and follows Home Assistant integration patterns with:

- `manifest.json` + `config_flow`
- Config entry runtime + `DataUpdateCoordinator`
- Supported entity platforms:
  - `sensor`
  - `binary_sensor`
  - `switch`
  - `light`
  - `button`
  - `climate`
  - `cover`
  - `date`
  - `datetime`
  - `fan`
  - `notify`
  - `number`
  - `scene`
  - `select`
  - `text`
  - `time`
  - `weather`

## Current status

✅ UI-configurable via **Settings → Devices & Services → Add Integration**  
✅ Multiple nodes per endpoint via **Options**  
✅ Polling + auto-reconnect on disconnect  
✅ HA discovery popup via Zeroconf (`_opcua-tcp._tcp.local.`): discovered servers can be confirmed and added directly  
✅ OPC-UA server discovery in options flow (FindServers/GetEndpoints + endpoint selection)  
✅ OPC-UA browser in options flow (root/depth/max + import as entities)  
✅ Auto-discovery (native OPC-UA + companion heuristics)  
✅ Stack light profile assistant (R/Y/G + optional buzzer)  
✅ Built-in notifications (`opcua_notification` event + optional HA notify service call)  
✅ Light entity with optional features (all optional):
- on/off
- brightness
- color_temp (kelvin)
- hs
- rgb
- rgbw
- rgbww
- xy
- white
- effect
- transition
- flash

## Limitations

- Supported security policies:
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- For Basic256Sha256, certificate/key paths must be set in the config flow
- Polling is used instead of OPC-UA subscriptions

## Usage

1. Restart Home Assistant.
2. Add the **OPC-UA** integration.
3. Enter endpoint (for example `opc.tcp://192.168.0.50:4840`).
4. Add nodes or use auto-discovery in integration options.

## Full example (all entity types + variants)

A full example with **all supported entity types** and a **light configuration with all optional variants** is available here:

- `examples/opcua_all_entities_example.json`

Included:
- sensor
- binary_sensor
- switch
- light (on/off, brightness, color_temp, hs, rgb, rgbw, rgbww, xy, white, effect, transition, flash)
- button
- climate
- cover
- date
- datetime
- fan
- notify
- number
- scene
- select
- text
- time
- weather

Note:
- The JSON is intended as a **reference/template** file (adapt node IDs to your server).
- Easiest path: configure integration via UI and copy node IDs/values from the example.

## Auto-discovery + companion mapping

In the options menu:
- **Auto discovery (native + companion)**
  - scans OPC-UA address space
  - maps variables automatically to core entity types (sensor/binary_sensor/switch/light)
  - additional entity types can be added manually in options flow
  - optionally applies companion/industrial heuristics (for example alarms, stack light, PackML-like states)
  - standard namespace nodes (`i=...`) can be hidden (default: hidden)
- **Browse OPC UA nodes**
  - tree-style branch navigation (open child branch / go up one level)
  - select/import individual variables from current branch
  - per-node metadata (NodeClass, SampleType, RO/RW)
