# 🏗️ KalleBot System-Architektur

## Übersicht

KalleBot ist ein modularer Discord Bot für Minecraft-Community-Management mit 3 Hauptsystemen:

```
┌─────────────────────────────────────────────────────────┐
│                   Discord API                            │
│          (Slash Commands, Events, UI)                    │
└────────────────┬──────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼────┐  ┌───▼────┐
│ Core  │   │ Entries│  │ Orders │
│ Bot   │   │ System │  │ System │
└───┬───┘   └───┬────┘  └───┬────┘
    │           │           │
    └───┬───────┴───┬───────┘
        │           │
    ┌───▼───────────▼────┐
    │   SQLite Database   │
    │   (aiosqlite)       │
    └─────────────────────┘
```

## 📦 Modulstruktur

### 1. **Core Bot** (`bot.py`)
- **Verantwortung**: Event-Handling, Admin-Commands, Setup
- **Haupt-Klasse**: `FinderBot(commands.Bot)`
- **Admin-Commands**:
  - `/setup_eintragen`, `/setup_suchen`, `/setup_log`
  - `/setup_farm_forum`, `/setup_struktur_forum`, `/setup_biom_forum`, `/setup_base_forum`
  - `/setup_bestellungen`, `/setup_bestellungen_forum`
  - `/eintrag_loeschen [optional_id]`
  - `!sync [optional_guild_id]` (Slash-Commands synchronisieren)

### 2. **Entries System** (`views.py`)
**Zweck**: Verwalten von Strukturen, Biomen, Farmen, Basen

**Klassen**:
```
EntryView (Button "Eintragen")
├─ CategoryTypeSelect (Struktur/Biom/Farm/Base)
├─ ItemSelect (Paginiertes Dropdown)
├─ EntryModal (Name, Koordinaten, Beschreibung)
├─ TagsModal (Tags eingeben)
├─ YouTubeModal (Link eingeben, nur Farmen)
└─ ColorPickerView (Farbe wählen)

SearchView (Button "Suchen")
├─ CategoryTypeSelect
├─ ItemSelect
├─ SearchModal
├─ PaginatedResultView (mit Entfernung-Button)
└─ ImageModal (Beschreibung hinzufügen)

DeleteTypeView (Kategorie-Auswahl beim Löschen)
```

**Flows**:
- Eintragen: Kategorie → Item → Modal → Tags → Farbe → Bilder → Forum-Post
- Suchen: Kategorie → Item → Modal → Ergebnisse (mit Pagination, Bilder, Specs)
- Löschen: Kategorie → Item → Bestätigung → Gelöscht + Log

### 3. **Orders System** (`orders.py`)
**Zweck**: Bestellungen (Items farmen) & Aufträge (andere Tasks)

**Klassen**:
```
BestellungView (Button "Bestellung/Auftrag")
├─ OrderTypeSelect (Bestellung oder Auftrag?)
├─ OrderModal (Was wird benötigt?)
├─ UrgencySelect (Dringlichkeit)
├─ PingModal (optional: Wer soll gepingt werden?)
├─ YouTubeModal (optional: Video-Link)
└─ FinishUploadView (Bilder hochladen)

Forum-Post mit Buttons:
├─ OrderProgressButton (🔧 In Bearbeitung)
└─ OrderDoneButton (✅ Fertig)
```

**Status-Flow**:
```
Offen → In Bearbeitung → Erledigt
         (+ Zuweisen)     (+ Foto, Ping Requester)
```

### 4. **Database** (`database.py`)
**Zweck**: SQLite Persistierung

**Tabellen**:

| Tabelle | Zweck |
|---------|-------|
| `config` | Admin-Setup (Channel-IDs, Forum-Channel-IDs) |
| `entries` | Strukturen, Biome, Farmen, Basen |
| `images` | Bilder pro Entry |
| `orders` | Bestellungen & Aufträge |

**Wichtige Funktionen**:
- `init_db()` - DB initialisieren
- `insert_entry(...)` - Neuen Eintrag erstellen
- `search_entries(...)` - Einträge durchsuchen
- `delete_entry(id)` - Eintrag löschen
- `add_image(entry_id, url, ...)` - Bild speichern
- `set_config(key, value)` - Konfiguration speichern

### 5. **Logging** (`logs.py`)
**Zweck**: Protokollierung von Bot-Aktionen

**Hauptfunktion**:
- `log_action(guild, embed)` → sendet Embed an Log-Channel

**Gelogged**:
- 🆕 Neue Einträge
- 🖼️ Bilder hinzugefügt
- 🗑️ Einträge gelöscht
- 📋 Bestellungen erstellt/aktualisiert

---

## 🔄 Inter-System Kommunikation

```
bot.py (Setup-Commands)
  ↓
views.py (EntryView/SearchView) oder orders.py (BestellungView)
  ↓
database.py (Einträge/Bestellungen speichern)
  ↓
logs.py (Aktion protokollieren)
  ↓
Discord API (Embeds, Forum-Posts)
```

**Beispiel-Flow**: Neue Farm eintragen
```
User klickt "Eintragen"
  → EntryView.button() wird ausgelöst
  → CategoryTypeSelect dropdown
  → ItemSelect dropdown
  → EntryModal
  → TagsModal
  → YouTubeModal (nur Farmen)
  → ColorPickerView
  → Bilder hochladen
  → database.insert_entry() + database.add_image()
  → _resolve_forum_tags() → Forum-Post erstellen
  → log_action() → Log-Channel update
  → database.set_config() falls Forum-ID gespeichert
```

---

## 💾 Datenbank-Relationen

```
entries (id, name, typ, x, y, z, ...)
    ↓
    ├─ images (entry_id → entries.id)
    │  (Bilder pro Eintrag)
    │
    └─ orders (optional: verknüpfte Order?)
       (Z.B. "Farm für Bestellung XY eintragen")

config (key, value)
    ↓
    ├─ entry_channel_id → Discord Channel
    ├─ search_channel_id → Discord Channel
    ├─ log_channel_id → Discord Channel
    ├─ farm_forum_channel_id → Discord Forum
    ├─ struktur_forum_channel_id → Discord Forum
    ├─ biom_forum_channel_id → Discord Forum
    ├─ base_forum_channel_id → Discord Forum
    ├─ bestellungen_channel_id → Discord Channel
    └─ bestellungen_forum_channel_id → Discord Forum

orders (id, title, status, urgency, ...)
    ├─ created_by → Discord User
    ├─ assigned_to → Discord User (optional)
    └─ forum_thread_id → Discord Forum Thread
```

---

## 🔐 Persistierung & State Management

### Persistente Views
Manche Buttons müssen auch nach Bot-Restart funktionieren:

```python
# bot.py → setup_hook()
self.add_view(EntryView())
self.add_view(SearchView())
self.add_view(orders.BestellungView())
self.add_dynamic_items(
    ForumEditButton,
    ForumDeleteButton,
    orders.OrderProgressButton,
    orders.OrderDoneButton
)
```

**Wichtig**: View-Komponenten-IDs müssen stabil sein (z.B. basierend auf Entry-ID)

### Forum-Post Integration
- Neue Einträge → Forum-Post mit Tags (Overworld/Nether/End + custom)
- Forum-Post speichert `forum_thread_id` in DB
- Bei Löschung: Thread löschen

### Image-Archivierung
- Nutzer laden Bilder im Eintragen-Channel hoch
- Bot archiviert in privaten "Image-Archive" Channel
- Discord-URLs temporär (~24h), daher Archivierung nötig
- Archiv-URL wird in `images` Tabelle gespeichert

---

## 🔧 Erweiterungspunkte

### Einfach
- Neue Struktur/Biom-Typen: Nur `STRUCTURES`/`BIOMES` in `views.py`
- Config-Werte: Neue Keys in `config` Tabelle (z.B. Discord-Channel-IDs)

### Mittel
- Neue Spalte in `entries`: `database.py` anpassen + UI updaten
- Neuer Admin-Command: `bot.py` + Error-Handler
- Neue Views/Modals: `views.py` + in Setup-Hooks registrieren

### Komplex
- Neues System (ähnlich Orders): Eigene Datei, Views, DB-Tabelle, Integration in `bot.py`
- Forum-Integration ausbauen: Mehr Tag-Typen, Auto-Tagging erweitern

---

## ⚡ Performance Considerations

- **Datenbank**: SQLite mit aiosqlite (async) → keine Blocking-Ops
- **Dropdown-Limit**: Max 25 Items pro Seite → Pagination mit Pfeilen
- **Forum-API**: Erstellen von Forum-Tags/Threads kann slow sein → defer() nutzen
- **Bildarchiv**: Bilder uploadcn zu Discord CDN → keine lokale Speicherung

---

## 🐛 Häufige Architektur-Fragen

**F: Warum aiosqlite?**
A: Discord.py ist async, daher auch DB async (nicht blockierend)

**F: Warum Forum-Integration statt einfach Nachrichten?**
A: Forum-Threads sind organisierter, Tags ermöglichen Filterung (Status, Dringlichkeit)

**F: Warum Bilder archivieren?**
A: Discord-Links gehen nach ~24h tot, Archiv ist persistent

**F: Können Einträge und Orders verknüpft werden?**
A: Zurzeit nicht direkt. Könnte mit `orders.entry_id` erweitert werden

**F: Warum separate orders.py?**
A: Orders sind ein eigenständiges System (kein Direct-Link zu Entries). Könnte später zusammengeführt werden.

---

**Version**: 1.0
**Letzte Aktualisierung**: Sept 2024
