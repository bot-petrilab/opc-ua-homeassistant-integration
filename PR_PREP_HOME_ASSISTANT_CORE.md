# OPC-UA → Home Assistant Core PR Prep

Stand: 2026-03-01

## Ziel
Diese Checkliste bereitet die bestehende `opcua`-Integration für einen PR gegen `home-assistant/core` vor.

---

## Aktueller Implementierungsstatus (fertig)

- Domain: `opcua`
- Config Entry + Config Flow + Options Flow vorhanden
- Runtime über `DataUpdateCoordinator`
- Plattformen vorhanden:
  - `sensor`, `binary_sensor`, `switch`, `light`
  - `button`, `climate`, `cover`, `date`, `datetime`, `fan`, `notify`, `number`, `scene`, `select`, `text`, `time`, `weather`
- OPC-UA Discovery/Browse/Auto-Mapping vorhanden
- Security-Policy Support:
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- Notification-Bridge Event: `opcua_notification`

## Verifizierte Tests (lokal)

- `tests/ha_opcua_regression/run.sh` → PASS (22/0)
- `tests/ha_opcua_regression/platform_coverage_check.py` → PASS
- `tests/ha_opcua_regression/notification_e2e_check.py` → PASS
- `tests/ha_opcua_regression/security_configflow_check.py` → PASS
- `tests/ci_smoke.py` → PASS

## Verifizierte CI (Repo)

- GitHub Actions Run `22545786693` → PASS

---

## Pflichtarbeiten für echten Core-PR (noch zu erledigen)

> Diese Punkte sind für einen Merge in `home-assistant/core` entscheidend.

1. **Code in Core-Struktur übernehmen**
   - Von: `custom_components/opcua/*`
   - Nach: `homeassistant/components/opcua/*`

2. **Core-konforme Test-Suite ergänzen**
   - `tests/components/opcua/test_config_flow.py`
   - `tests/components/opcua/test_init.py`
   - `tests/components/opcua/test_coordinator.py`
   - `tests/components/opcua/test_<platform>.py` (mind. repräsentative Plattformen)

3. **Core-typische Artefakte/Standards prüfen**
   - Diagnostics (`diagnostics.py`) erwägen
   - Repairs/Issue-Handling bei Setup-Fehlern prüfen
   - Translation-Keys/strings auf Core-Review-Niveau aufräumen

4. **Smoke-Hilfscode entfernen**
   - Fallback in `const.py` für `Platform` (nur für Standalone-Smoke) vor Core-PR entfernen.

5. **Minimalen, reviewbaren Scope festlegen**
   - Empfehlung: initialer Core-PR mit kleinerem Plattform-Umfang (z. B. `sensor`, `binary_sensor`, `switch`, `light`) und Folge-PRs für weitere Typen.

---

## Empfohlene PR-Strategie

### Option A (empfohlen): gestuft
1. PR 1: Grundintegration + Kernplattformen + solide Core-Tests
2. PR 2+: zusätzliche Plattformen (`climate`, `cover`, `fan`, ...)

### Option B: Full Scope
- alles in einem PR, aber deutlich höheres Review-Risiko.

---

## PR-Text (Draft)

**Title**
`Add OPC-UA integration (config entry based) with coordinator runtime`

**Summary**
- Adds new `opcua` integration with config entries.
- Uses `asyncua` client manager + `DataUpdateCoordinator`.
- Supports secure connection policies (`Basic256Sha256_Sign`, `Basic256Sha256_SignAndEncrypt`).
- Includes discovery/browse based entity onboarding.
- Adds initial platform support + tests.

**Why**
- Enables native OPC-UA based industrial/PLC telemetry and control in Home Assistant.

---

## Quick verification commands

```bash
cd /home/user/.openclaw/workspace
tests/ha_opcua_regression/run.sh
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/platform_coverage_check.py
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/notification_e2e_check.py
/home/user/.openclaw/workspace/.pw-venv/bin/python tests/ha_opcua_regression/security_configflow_check.py
```
