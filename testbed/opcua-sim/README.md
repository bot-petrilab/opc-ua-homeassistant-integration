# OPC-UA Test Servers

This directory contains two standard test servers plus security-focused test servers.

## 1) All Entities Server (Port 4840)

File: `server_all_entities.py`

Purpose:
- all data types relevant to the integration
- all supported entity types (sensor, binary_sensor, switch, light, button, climate, cover, date, datetime, fan, notify, number, scene, select, text, time, weather)

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_all_entities.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4840`

## 2) Device Split Server (Port 4842)

File: `server_device_split.py`

Purpose:
- models device hierarchy with `DeviceType` (HasTypeDefinition)
- models light objects with `LightType` (HasTypeDefinition)
- tests automatic device grouping in Home Assistant

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_device_split.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4842`

## 3) Basic256Sha256 Security Server (Port 4850)

File: `server_basic256.py`

Purpose:
- security test server for `Basic256Sha256_SignAndEncrypt`
- integration must be configured with security policy `Basic256Sha256_SignAndEncrypt`

Start:

```bash
cd /home/user/.openclaw/workspace/opc-ua-homeassistant-integration
python3 testbed/opcua-sim/server_basic256.py
```

Endpoint:
- `opc.tcp://127.0.0.1:4850`

Server certificate:
- `testbed/opcua-sim/certs/server_basic256_cert.pem`

## 4) Basic256Sha256 + Username/Password Server (Port 4851)

File: `server_basic256_userpass.py`

Purpose:
- security test server with encrypted channel **and** mandatory user authentication
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

Create both standard servers as Home Assistant config entries automatically:

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
