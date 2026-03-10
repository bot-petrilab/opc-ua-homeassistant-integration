# OPC-UA Test Server (2-Server Setup)

Dieses Verzeichnis enthält **genau zwei** unterstützte Test-Server.

## 1) All Entities Server (Port 4840)

Datei: `server_all_entities.py`

Zweck:
- alle Datentypen, die in der Integration relevant sind
- alle unterstützten Entity-Typen (sensor, binary_sensor, switch, light, button, climate, cover, date, datetime, fan, notify, number, scene, select, text, time, weather)

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_all_entities.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4840`

## 2) Device Split Server (Port 4842)

Datei: `server_device_split.py`

Zweck:
- modelliert Gerätehierarchie mit `DeviceType` (HasTypeDefinition)
- Lichtobjekte als `LightType` (HasTypeDefinition)
- Tests für automatische Geräteaufteilung in Home Assistant

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_device_split.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4842`

## Home Assistant Bindings

Beide Server automatisch als Config Entries anlegen:

```bash
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/setup_two_server_entries.py
```

All-Entities Setup:

```bash
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/setup_entity_matrix_entry.py
```

LightType Discovery (Device-Split):

```bash
OPC_ENDPOINT=opc.tcp://127.0.0.1:4842 \
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/setup_lighttype_autodiscovery_entry.py
```
