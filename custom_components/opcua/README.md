# OPC-UA (Custom Integration for Home Assistant)

Diese Integration nutzt **opcua-asyncio** (`asyncua`) und folgt dem Home-Assistant-Pattern mit:

- `manifest.json` + `config_flow`
- Config Entry Runtime + `DataUpdateCoordinator`
- Standard-Entitäten:
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

## Aktueller Stand

✅ UI-konfigurierbar über **Einstellungen → Geräte & Dienste → Integration hinzufügen**  
✅ Mehrere Nodes je Endpoint über **Optionen**  
✅ Polling + Auto-Reconnect bei Verbindungsabbruch  
✅ HA Discovery-Popup via Zeroconf (`_opcua-tcp._tcp.local.`): gefundene Server können direkt bestätigt und hinzugefügt werden  
✅ OPC-UA Server Discovery im Options-Flow (FindServers/GetEndpoints + Endpoint-Auswahl)  
✅ OPC-UA Browser im Options-Flow (Root/Depth/Max + Import als Entität)  
✅ Auto-Discovery (native OPC-UA + Companion-Heuristiken)  
✅ Stack-Light-Profil-Assistent (R/Y/G + optional Buzzer)  
✅ Built-in notifications (`opcua_notification` event + optional HA notify service call)  
✅ Light-Entity mit optionalen Features (alle optional):
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

## Einschränkung

- Unterstützt jetzt:
  - `None`
  - `Basic256Sha256_Sign`
  - `Basic256Sha256_SignAndEncrypt`
- Für Basic256Sha256 müssen Zertifikat/Key-Pfade im Config-Flow gesetzt sein
- Polling statt OPC-UA-Subscription

## Bedienung

1. Home Assistant neu starten.
2. Integration „**OPC-UA**“ hinzufügen.
3. Endpoint eintragen (z. B. `opc.tcp://192.168.0.50:4840`).
4. In den Integrations-Optionen Nodes hinzufügen oder Auto-Discovery nutzen.

## Vollständiges Beispiel (alle Entity-Typen + Varianten)

Ein vollständiges Beispiel mit **allen unterstützten Entity-Typen** und einer **Light-Konfiguration mit allen optionalen Varianten** liegt hier:

- `examples/opcua_all_entities_example.json`

Enthalten sind:
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

Hinweis:
- Das JSON ist als **Referenz-/Vorlagen-Datei** gedacht (Node-IDs auf deine Maschine anpassen).
- Einfachster Weg: Integration per UI anlegen und die Werte/Node-IDs aus dem Beispiel übernehmen.

## Auto-Discovery + Companion-Mapping

Im Options-Menü:
- **Auto discovery (native + companion)**
  - scannt den OPC-UA-Adressraum
  - ordnet Variablen automatisch Kern-Entitätstypen zu (sensor/binary_sensor/switch/light)
  - weitere Entitätstypen können manuell im Options-Flow ergänzt werden
  - nutzt optional Companion-/Industrie-Heuristiken (z. B. Alarme, Stacklight, PackML-ähnliche States)
  - Standard-Namespace (`i=...`) kann optional ausgeblendet werden (default: ausblenden)
- **Browse OPC UA nodes**
  - baumartige Navigation über Zweige (Unterzweig öffnen / eine Ebene hoch)
  - einzelne Variablen im aktuellen Zweig markieren und importieren
  - Metadaten je Node (NodeClass, SampleType, RO/RW)
