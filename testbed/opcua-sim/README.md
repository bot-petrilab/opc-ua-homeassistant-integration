# OPC-UA Test Server

Dieses Verzeichnis enthält zwei Standard-Testserver plus Security-Testserver.

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

## 3) Basic256Sha256 Security Server (Port 4850)

Datei: `server_basic256.py`

Zweck:
- Security-Testserver für `Basic256Sha256_SignAndEncrypt`
- Integration muss mit Security Policy `Basic256Sha256_SignAndEncrypt` angebunden werden

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_basic256.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4850`

Server-Zertifikat:
- `testbed/opcua-sim/certs/server_basic256_cert.pem`

## 4) Basic256Sha256 + Username/Password Server (Port 4851)

Datei: `server_basic256_userpass.py`

Zweck:
- Security-Testserver mit verschlüsseltem Kanal **und** verpflichtender Benutzer-Authentifizierung
- Security Policy: `Basic256Sha256_SignAndEncrypt`
- Identity Token: `Username`

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_basic256_userpass.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4851`

Credentials (Test):
- Username: `admin`
- Password: `Admin123`

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
