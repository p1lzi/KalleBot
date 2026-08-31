# 💾 KalleBot Datenbank-Schema

SQLite-Datenbank (`data.db`) mit aiosqlite für async Zugriff.

---

## 📊 Tabellen-Übersicht

| Tabelle | Zweck | Rows |
|---------|-------|------|
| `config` | Admin-Konfiguration (Channel-IDs) | <50 |
| `entries` | Strukturen, Biome, Farmen, Basen | variabel |
| `images` | Bilder pro Entry | variabel |
| `orders` | Bestellungen & Aufträge | variabel |

---

## 🔑 Detailliertes Schema

### 1. `config`

Speichert Discord-Channel-IDs und andere Konfigurationswerte.

```sql
CREATE TABLE config (
    key   TEXT PRIMARY KEY,
    value TEXT
)
```

**Spalten**:
| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| `key` | TEXT PK | Config-Schlüssel |
| `value` | TEXT | Config-Wert (usually Discord-ID als String) |

**Bekannte Keys**:
```
entry_channel_id              → Channel-ID für Eintragen-Button
search_channel_id             → Channel-ID für Suchen-Button
log_channel_id                → Channel-ID für Logs
image_archive_channel_id      → Channel-ID für Bild-Archiv (privat)
farm_forum_channel_id         → Forum-Channel-ID für Farmen
struktur_forum_channel_id     → Forum-Channel-ID für Strukturen
biom_forum_channel_id         → Forum-Channel-ID für Biome
base_forum_channel_id         → Forum-Channel-ID für Basen
bestellungen_channel_id       → Channel-ID für Bestellungen-Button
bestellungen_forum_channel_id → Forum-Channel-ID für Bestellungen
```

**Beispiel-Eintrag**:
```
key="entry_channel_id", value="1234567890"
```

---

### 2. `entries`

Alle Strukturen, Biome, Farmen und Basen.

```sql
CREATE TABLE entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    typ             TEXT NOT NULL,
    x               REAL NOT NULL,
    y               REAL,
    z               REAL NOT NULL,
    beschreibung    TEXT,
    specs           TEXT,
    forum_thread_id INTEGER,
    tags            TEXT,
    youtube_link    TEXT,
    color           TEXT,
    ersteller_id    INTEGER,
    ersteller_name  TEXT,
    erstellt_am     TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Spalten**:

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|-------------|----------|
| `id` | INT PK | Auto-incrementing Entry-ID | 42 |
| `name` | TEXT | Name der Struktur/Biom/Farm | "Dschungel-Tempel" |
| `typ` | TEXT | Typ: "struktur", "biom", "farm", "base" | "farm" |
| `x` | REAL | X-Koordinate (Minecraft) | 1234.5 |
| `y` | REAL | Y-Koordinate (optional) | 64.0 |
| `z` | REAL | Z-Koordinate (Minecraft) | -5678.5 |
| `beschreibung` | TEXT | Beschreibung/Notizen | "Schöne Farm mit guter Lage" |
| `specs` | TEXT | Specs (JSON-ähnlich, nur Farmen) | "mobs: [creeper, spider]" |
| `forum_thread_id` | INT | Verknüpfter Discord Forum-Thread | 98765432 |
| `tags` | TEXT | Tags (komma-getrennt) | "Overworld,Nether,custom-tag" |
| `youtube_link` | TEXT | YouTube-Tutorial-Link (nur Farmen) | "https://youtube.com/watch?v=..." |
| `color` | TEXT | Embed-Farbe (Hex) | "#00ff00" |
| `ersteller_id` | INT | Discord User-ID des Erstellers | 112233445 |
| `ersteller_name` | TEXT | Discord Username | "JohnDoe#1234" |
| `erstellt_am` | TEXT | Timestamp | "2024-09-01 12:30:45" |

**Constraints**:
- `id` ist Primary Key (eindeutig, auto-increment)
- `name`, `typ`, `x`, `z` sind NOT NULL
- `y` ist optional (manche Farmen brauchen nur X/Z)

**Typen**:
```
struktur  → Village, Stronghold, Bastion, Nether Fortress, etc. (siehe STRUCTURES in views.py)
biom      → Ebene, Wald, Taiga, Dschungel, Wüste, etc. (siehe BIOMES in views.py)
farm      → Mob-Farm, Item-Farm, Enderman-Farm, etc. (siehe FARM_TYPES in views.py)
base      → Spieler-Base (siehe BASE_TYPES in views.py)
```

**Beispiel-Eintrag**:
```
id=42, name="Eisen-Farm", typ="farm", x=1234.0, z=-5678.0, 
beschreibung="Funktionierende Eisen-Farm mit Hopper-System",
specs="item: iron_ore, rate: 20 per minute", 
tags="Overworld,automatisch,effizient",
youtube_link="https://youtube.com/watch?v=...",
color="#FFD700",
ersteller_id=1234567890,
ersteller_name="Builder123",
erstellt_am="2024-09-01 15:45:20"
```

---

### 3. `images`

Bilder pro Entry.

```sql
CREATE TABLE images (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id     INTEGER NOT NULL,
    url          TEXT NOT NULL,
    beschreibung TEXT,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
)
```

**Spalten**:

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| `id` | INT PK | Auto-incrementing Image-ID |
| `entry_id` | INT FK | Verweis auf `entries.id` |
| `url` | TEXT | Discord-CDN-URL (Archiv-URL, nicht temporär!) |
| `beschreibung` | TEXT | Optional: Beschreibung des Bildes |

**Wichtig**:
- `entry_id` referenziert `entries.id`
- `ON DELETE CASCADE`: Wenn Entry gelöscht → alle Images automatisch gelöscht
- URLs sollten auf Archive zeigen (Image-Archive-Channel), nicht auf temporäre Links

**Beispiel-Eintrag**:
```
id=1, entry_id=42, url="https://cdn.discordapp.com/attachments/123/456/image.png", 
beschreibung="Hopper-System"
```

---

### 4. `orders`

Bestellungen (Items farmen) und Aufträge (andere Tasks).

```sql
CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_type      TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    status          TEXT DEFAULT 'offen',
    urgency         TEXT,
    created_by      INTEGER NOT NULL,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    assigned_to     INTEGER,
    assigned_at     TEXT,
    completed_at    TEXT,
    forum_thread_id INTEGER,
    tags            TEXT
)
```

**Spalten**:

| Spalte | Typ | Beschreibung |
|--------|-----|-------------|
| `id` | INT PK | Auto-incrementing Order-ID |
| `order_type` | TEXT | "bestellung" oder "auftrag" |
| `title` | TEXT | Titel (z.B. "5 Stacks Eisen") |
| `description` | TEXT | Detaillierte Beschreibung |
| `status` | TEXT | "offen" / "in_bearbeitung" / "erledigt" |
| `urgency` | TEXT | "niedrig" / "mittel" / "hoch" / "dringend" |
| `created_by` | INT | Discord User-ID des Requesters |
| `created_at` | TEXT | Timestamp der Erstellung |
| `assigned_to` | INT | Discord User-ID des Zugewiesenen (optional) |
| `assigned_at` | TEXT | Timestamp der Zuweisung (optional) |
| `completed_at` | TEXT | Timestamp der Fertigstellung (optional) |
| `forum_thread_id` | INT | Verknüpfter Discord Forum-Thread |
| `tags` | TEXT | Forum-Tags (Status + Dringlichkeit) |

**Status-Werte**:
```
offen         → Neu erstellt, wartet auf Bearbeiter
in_bearbeitung → Jemand arbeitet daran (assigned_to ist gesetzt)
erledigt      → Fertig, completed_at gesetzt, Requester gepingt
```

**Urgency-Werte**:
```
niedrig   🟢
mittel    🟡
hoch      🟠
dringend  🔴
```

**Beispiel-Eintrag**:
```
id=1, order_type="bestellung", title="5 Stacks Eisen + 2 Shulker Gold",
description="Brauche so schnell wie möglich...",
status="in_bearbeitung", urgency="hoch",
created_by=1111111111, created_at="2024-09-01 14:00:00",
assigned_to=2222222222, assigned_at="2024-09-01 14:05:00",
forum_thread_id=9876543,
tags="hoch,in_bearbeitung"
```

---

## 🔄 Relationen & Constraints

```
entries (Primary)
  ├─ images (Foreign Key: entry_id → entries.id)
  │  └─ Cascade Delete: Gelöschte Entries → Images auch löschen
  │
  └─ orders (optional: könnte mit entry_id erweitert werden)
     └─ "Bestellung für Farm X"

config (keine direkten Relations, nur Werte)

orders (Primary)
  └─ Keine direkten Foreign Keys (nur User-IDs als Text)
```

---

## 📝 Query-Beispiele

### Alle Farmen abrufen
```sql
SELECT * FROM entries WHERE typ = 'farm' ORDER BY erstellt_am DESC;
```

### Bilder für einen Eintrag
```sql
SELECT * FROM images WHERE entry_id = 42;
```

### Einträge in Nähe von Koordinaten (Overworld)
```sql
SELECT id, name, x, z, 
       SQRT((x - 1000) * (x - 1000) + (z - 2000) * (z - 2000)) as distanz
FROM entries 
WHERE typ = 'farm'
ORDER BY distanz ASC
LIMIT 10;
```

### Offene Bestellungen
```sql
SELECT * FROM orders WHERE status = 'offen' ORDER BY urgency DESC;
```

### Bestellungen von User X
```sql
SELECT * FROM orders WHERE created_by = 1234567890 ORDER BY created_at DESC;
```

### Log-Statistik: Entries pro Typ
```sql
SELECT typ, COUNT(*) as count FROM entries GROUP BY typ;
```

---

## 🔧 Datenbank-Operationen

Alle Ops sind in `database.py` implementiert, async (aiosqlite):

```python
# Initialisierung
await db.init_db()

# Config
await db.get_config("entry_channel_id")
await db.set_config("entry_channel_id", "123456789")

# Entries
await db.insert_entry(name, typ, x, y, z, beschreibung, specs, tags, ...)
await db.get_entry(id)
await db.search_entries(typ, name_filter, user_x, user_z)
await db.delete_entry(id)
await db.update_entry(id, **kwargs)

# Images
await db.add_image(entry_id, url, beschreibung)
await db.get_images(entry_id)

# Orders (in orders.py)
await db.insert_order(order_type, title, description, urgency, created_by)
await db.update_order_status(order_id, status, assigned_to)
```

---

## 📈 Performance-Tipps

1. **Indizes**: Für häufig gesuchte Spalten hinzufügen (z.B. `typ`, `ersteller_id`)
   ```sql
   CREATE INDEX idx_entries_typ ON entries(typ);
   CREATE INDEX idx_entries_ersteller ON entries(ersteller_id);
   CREATE INDEX idx_images_entry ON images(entry_id);
   ```

2. **Pagination**: Bei vielen Einträgen → LIMIT & OFFSET nutzen
   ```sql
   SELECT * FROM entries WHERE typ = 'farm' LIMIT 25 OFFSET 0;
   ```

3. **Vacuum**: Regelmäßig die DB aufräumen
   ```sql
   VACUUM;
   ```

---

## 🔐 Datenschutz & Sicherheit

- **User-IDs**: Werden als INT gespeichert (Discord User-ID)
- **Sensitive Data**: Keine Passwörter oder Tokens in der DB
- **XSS-Protection**: User-Input wird nicht direkt in Embeds verwendet (wird escaped)
- **SQL-Injection**: aiosqlite nutzt prepared statements (sichere Parameterisierung)

---

## 📊 Backup & Restore

```bash
# Backup erstellen
cp data.db data.db.backup

# Aus Backup restaurieren
cp data.db.backup data.db
```

---

**Version**: 1.0
**Letzte Aktualisierung**: Sept 2024
