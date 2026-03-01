# Home Assistant Core PR Checklist – OPC-UA

Basis: 
- Core architecture: https://developers.home-assistant.io/docs/architecture/core/
- Config entries: https://developers.home-assistant.io/docs/config_entries_index/
- Config flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- Options flow: https://developers.home-assistant.io/docs/config_entries_options_flow_handler/
- Quality scale: https://developers.home-assistant.io/docs/core/integration-quality-scale/
- Checklist: https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/

## Bronze (PR-MVP)

- [x] `config_flow` – UI setup vorhanden
- [x] `unique_config_entry` – Duplikate werden abgefangen
- [x] `runtime_data` – `ConfigEntry.runtime_data` wird genutzt
- [x] `test_before_setup` – Setup prüft Verbindung (ConfigEntryNotReady)
- [x] `appropriate_polling` – Coordinator-Intervall konfigurierbar
- [x] `entity_unique_id` – eindeutige IDs pro Entity
- [x] `config_entry_unloading` – Unload implementiert
- [x] `discovery` – Zeroconf + Discovery-Flows vorhanden
- [ ] `config-flow-test-coverage` – für Core: pytest-Tests in `tests/components/opcua` ergänzen
- [ ] `brands` – Brand assets im Core/brands prüfen (separater PR/Asset-Pfad)
- [ ] `has_entity_name` – pro Plattform validieren und ggf. nachziehen
- [ ] `docs-*` – Endnutzer-Doku im core-docs Stil finalisieren

## Silver/Gold vorbereiten

- [ ] Reauth-Flow (falls Auth relevant)
- [ ] Diagnostics (`diagnostics.py`)
- [ ] Repair-Issues bei Benutzerintervention
- [ ] Höhere Unit-Test-Abdeckung (>95% im Integrationsteil)

## Technische PR-Vorbereitung

- [ ] Zielpfad auf Core-Struktur umsetzen: `homeassistant/components/opcua`
- [ ] Standalone-Smoke-Hilfen entfernen (z. B. `Platform`-Fallback in `const.py`)
- [ ] Core-lint/typing lokal laufen lassen (im Core-Repo)
- [ ] Core-pytest für `tests/components/opcua/*`
- [ ] PR mit Bronze-Checkliste + Links auf Tests/Code einreichen

## Empfohlene Einreichungsstrategie

1. **PR 1 (MVP/Bronze):** config flow + coordinator + Kernplattformen + Core-Tests
2. **PR 2+:** erweiterte Plattformen (`climate`, `cover`, `weather`, ...)

So sinkt das Review-Risiko deutlich.
