# OPC-UA Custom Integration for Home Assistant

Custom Home Assistant integration (domain: `opcua`) with display name **OPC-UA**.

This integration connects Home Assistant to OPC-UA servers and lets you bring industrial or machine data into Home Assistant through a standard UI-based setup flow. Typical use cases include reading process values, exposing machine states as entities, controlling writable nodes, and mapping structured OPC-UA models to Home Assistant devices and entities.

## What this integration is for

Use this integration when you want to:

- connect Home Assistant to an OPC-UA endpoint with a normal UI config flow
- discover OPC-UA servers announced via zeroconf
- browse an OPC-UA address space and import selected nodes as entities
- auto-map common OPC-UA variables to Home Assistant entity types
- monitor machine/process values in dashboards and automations
- control writable OPC-UA nodes through standard Home Assistant entity services

## Features

- UI config flow
- Supported entity platforms:
  - sensor
  - binary_sensor
  - switch
  - light
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
- OPC-UA server discovery:
  - Home Assistant discovery prompt via zeroconf (`_opcua-tcp._tcp.local.`)
  - manual endpoint discovery via FindServers/GetEndpoints
- OPC-UA node browser with tree navigation
- Auto-discovery mapping (native + companion-style heuristics)
- Stack-light profile helper
- Built-in OPC-UA notification bridge
- Secure endpoint support:
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`

## Installation

1. Copy `custom_components/opcua` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & Services → Add Integration**.
4. Select **OPC-UA**.
5. Enter the endpoint and complete the setup flow.

## Configuration parameters

Setup flow fields:

- `endpoint`
- `security_policy` (`None`, `Basic256Sha256_Sign`, `Basic256Sha256_SignAndEncrypt`)
- `username` / `password` (optional, depending on server identity policy)
- `client_cert_path` / `client_key_path` and optional `client_key_password` (required for secure policy usage)
- `server_cert_path` (optional)
- `validate_on_save`

Options flow includes:

- node/entity management
- browse and auto-discovery tools
- notification settings

## YAML configuration (import support)

In addition to UI setup, the integration now supports YAML import via `configuration.yaml`.
Each YAML block is imported as a normal config entry, so **all entity kinds** and **device metadata**
work the same way as in UI configuration.

```yaml
opcua:
  - endpoint: opc.tcp://192.168.1.50:4840
    security_policy: None
    notify_enabled: true
    notify_keywords: "alarm,fault,warn"
    nodes:
      - name: Process Temperature
        node_id: ns=2;s=Process.Temperature
        kind: sensor
        unit: "°C"
        device_class: temperature
        state_class: measurement
        device_id: plc_line_1
        device_name: PLC Line 1
        device_manufacturer: Example Automation
        device_model: PLC-X1000
      - name: Machine Running
        node_id: ns=2;s=Machine.Running
        kind: binary_sensor
        device_class: running
        device_id: plc_line_1
      - name: Main Light
        node_id: ns=2;s=Light.Main.On
        kind: light
        brightness_node_id: ns=2;s=Light.Main.Brightness
        device_id: panel_1
        device_name: Operator Panel 1
```

Notes:
- `kind` supports all implemented platforms (`sensor`, `binary_sensor`, `switch`, `light`, `button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`, `valve`).
- Device entries are created when node configs include `device_id` (optionally with `device_name`, `device_manufacturer`, `device_model`, `device_serial`).

## Discovery, node browser, and auto-discovery

These three features serve different purposes:

### 1. Discovery
Use **discovery** when you first want to find an OPC-UA server endpoint.

This integration supports:
- automatic zeroconf discovery in Home Assistant
- manual discovery via FindServers/GetEndpoints

Use this when you do not yet know the final endpoint URL or when a server exposes multiple endpoints/security variants.

### 2. Node browser
Use the **node browser** when you already have a working connection and want precise control over what gets imported.

Best for:
- exploring a server tree manually
- checking where values live in the address space
- importing specific nodes as entities
- avoiding broad heuristic imports

### 3. Auto-discovery
Use **auto-discovery** when you want the integration to scan a subtree and propose or create entity mappings automatically.

Best for:
- quick first imports
- structured servers with consistent naming/typing
- machine models where standard patterns can be inferred automatically

In short:
- **Discovery** finds servers/endpoints
- **Node browser** lets you choose nodes manually
- **Auto-discovery** imports likely entities from a subtree automatically

## Secure setup and certificates

For secure OPC-UA endpoints, Home Assistant must be able to access the configured certificate and key files from its runtime environment.

### When certificates are required
For these security policies, you should expect to provide certificate/key material:
- `Basic256Sha256_Sign`
- `Basic256Sha256_SignAndEncrypt`

### What to verify
If secure setup is used, verify that:
- the configured certificate path exists inside the Home Assistant runtime
- the configured private key path exists inside the Home Assistant runtime
- the private key password is correct, if the key is encrypted
- the selected security policy matches one of the server's exposed endpoints
- username/password requirements match the endpoint identity policy
- the optional server certificate path, if used, points to the expected certificate

### Practical advice
- Start with the exact endpoint/security combination exposed by the server.
- Use `validate_on_save` to catch broken secure settings early.
- If validation fails and you need to isolate whether the problem is path-related or handshake-related, temporarily disable `validate_on_save`, save carefully, and then inspect behavior/runtime logs.

## Data update behavior

- Integration is `local_push`.
- Data updates are driven by OPC-UA subscriptions / monitored items.
- The coordinator keeps an in-memory snapshot and applies subscription updates as they arrive.
- On disconnect, reconnect attempts are handled by the client/coordinator flow.
- One-shot reads are still used for initial snapshots and explicit refreshes after writes.

## Supported devices and functions

Supported functionality includes:
- endpoint discovery
- address-space browsing
- auto-discovery from OPC-UA subtrees
- multi-platform entity mapping from OPC-UA nodes
- writable entity control through standard Home Assistant services
- device grouping from OPC-UA metadata where available

Supported entity platforms:
- sensor
- binary_sensor
- switch
- light
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

Supported device scope:
- OPC-UA servers exposing readable/writable `Variable` nodes (industrial PLCs, gateways, simulation servers, machine controllers).
- Structured models with stable browse names/paths (best results for auto-discovery and device grouping).

Known unsupported / partially supported scenarios:
- Historical/event-stream-only servers without usable current-value `Variable` nodes.
- Server-specific proprietary data models that require custom method calls instead of variable read/write mappings.

## Use cases

### 1. Machine status dashboard
Map machine status, alarms, temperatures, counters, and mode states into Home Assistant entities and visualize them in a Lovelace dashboard.

### 2. Stack light and signal monitoring
Import stack-light or alarm-related nodes and use Home Assistant automations to notify users when warning/fault states become active.

### 3. Bridging industrial values into automations
Use OPC-UA values such as temperatures, tank levels, switch states, or production flags to trigger Home Assistant automations and scenes.

## Service actions

The integration currently does not register custom domain service actions.

Use standard Home Assistant entity services instead, for example:
- `light.turn_on`
- `switch.turn_on`
- `number.set_value`
- `climate.set_temperature`
- `cover.open_cover`

## Automation examples

### Example 1: turn on an OPC-UA light at sunset

```yaml
alias: OPCUA Light On at Sunset
trigger:
  - platform: sun
    event: sunset
action:
  - service: light.turn_on
    target:
      entity_id: light.rainbow_pro
```

### Example 2: notify when a machine alarm becomes active

```yaml
alias: OPCUA Machine Alarm
trigger:
  - platform: state
    entity_id: binary_sensor.machine_alarm
    to: "on"
action:
  - service: notify.notify
    data:
      message: "The OPC-UA machine alarm is active."
```

### Example 3: reduce target setpoint when a process value is too high

```yaml
alias: OPCUA Cooling Assist
trigger:
  - platform: numeric_state
    entity_id: sensor.process_temperature
    above: 80
action:
  - service: number.set_value
    target:
      entity_id: number.cooling_setpoint
    data:
      value: 65
```

## Known limitations

- Connection quality and update latency depend on OPC-UA server subscription behavior and monitored-item configuration.
- For secure policies, valid certificate/key material must be available to Home Assistant runtime paths.
- Feature availability depends on node model quality and naming/typing.
- Automatically inferred mappings depend on the structure and quality of the OPC-UA server model.

## Troubleshooting

### Setup fails with a secure endpoint
- verify certificate/key paths are readable from the Home Assistant runtime
- verify endpoint security policy and identity token expectations
- verify client certificate, key, and optional key password match each other
- verify username/password if the selected endpoint requires them

### Discovery does not find the server
- verify the server actually exposes zeroconf or a reachable discovery endpoint
- try manual endpoint discovery
- verify the server/network allows discovery traffic

### Entities do not appear as expected
- use the node browser to confirm the target nodes exist where expected
- verify node readability/writability and data types on the server side
- try manual import if heuristic auto-discovery misses a node

### Imported entities behave unexpectedly
- verify the node type really matches the selected Home Assistant entity model
- verify scaling, writable state, and server-side data typing

## Removal

1. Go to **Settings → Devices & Services**.
2. Open the OPC-UA integration card.
3. Use **Delete** to remove the config entry.
4. Optionally remove `custom_components/opcua` from disk and restart Home Assistant.

## Development testbed

There are two standard test servers plus security-focused test servers:

- `testbed/opcua-sim/server_all_entities.py` (port `4840`): all data types + all entity types supported by the integration
- `testbed/opcua-sim/server_device_split.py` (port `4842`): data types + light objects split across multiple devices (`DeviceType` / `LightType` via HasTypeDefinition)
- `testbed/opcua-sim/server_basic256.py` (port `4850`): security test server (`Basic256Sha256_SignAndEncrypt`)
- `testbed/opcua-sim/server_basic256_userpass.py` (port `4851`): security + required username/password

Helper scripts:
- `tests/ha_opcua_regression/setup_entity_matrix_entry.py` binds the all-entities server in Home Assistant and creates all platform entities
- `tests/ha_opcua_regression/setup_two_server_entries.py` binds both standard servers (`4840`, `4842`) in Home Assistant

## Tests

- Home Assistant-style component tests (pytest layout): `tests/components/opcua/`
  - `__init__.py`, `conftest.py`, `test_init.py`, `test_*.py`
- Local UI/E2E regression tests: `tests/ha_opcua_regression/README.md`

## CI

GitHub Actions workflow runs:
- JSON validation
- Python compile checks
- OPC-UA smoke test (`tests/ci_smoke.py`)
