# 🤖 KalleBot Discord Bot - Skill für KI-Assistenten

> **Für KI-Assistenten**: Dieses Dokument erklärt die Bot-Architektur, Datenstruktur und Best Practices für neue Features.

---

## 📌 Schnelle Übersicht

**KalleBot** ist ein Python Discord Bot (discord.py v2.4.0+) zur Verwaltung von Minecraft-Inhalten:

| Feature | Datei | Funktion |
|---------|-------|----------|
| 🏛️ Strukturen/🌳 Biome/🚜 Farmen/🏘️ Basen eintragen | `views.py` | `EntryView()` + `EntryModal` |
| 🔍 Suchen mit Koordinaten & Entfernung | `views.py` | `SearchView()` + Pagination |
| 🗑️ Admin-Löschung | `bot.py` | `/eintrag_loeschen` |
| 📋 Bestellungen & Aufträge | `orders.py` | `BestellungView()` + Status-Tracking |
| 💾 Datenspeicherung | `database.py` | SQLite (aiosqlite) |
| 📝 Logging | `logs.py` | `log_action()` |

---

## 🏗️ Datei-Zwecke

```python
bot.py              # Haupteinstieg, Admin-Commands (/setup_*, /eintrag_loeschen, !sync)
database.py         # SQLite CRUD: entries, images, config, orders
views.py            # UI: Buttons, Modals, Dropdowns, Resultats-Embeds
orders.py           # Bestellungen-System (eigenständig von Entries)
logs.py             # Logging: log_action(guild, embed) → Log-Channel
requirements.txt    # discord.py, aiosqlite, python-dotenv
.env               # DISCORD_TOKEN, BOT_ACTIVITY_*, BOT_STATUS
```

---

## 💾 Datenbank-Schnellreferenz

### entries (Haupttabelle)
```
id              INT PRIMARY KEY AUTOINCREMENT
name            TEXT NOT NULL
typ             TEXT ('struktur'|'biom'|'farm'|'base')
x, z            REAL (Minecraft-Koordinaten)
y               REAL (optional)
beschreibung    TEXT
specs           TEXT (JSON bei Farmen, z.B. "farm_mobs: [creeper, spider]")
forum_thread_id INT (verknüpfte Discord Forum-Thread-ID)
tags            TEXT (komma-getrennt, z.B. "Overworld,Nether,custom-tag")
youtube_link    TEXT (nur Farmen)
color           TEXT (Hex-Farbe für Embed, z.B. "#00ff00")
ersteller_id    INT (Discord User-ID)
ersteller_name  TEXT (Discord Username)
erstellt_am     TEXT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### images
```
id          INT PRIMARY KEY
entry_id    INT (Foreign Key zu entries.id)
url         TEXT (Discord-CDN-URL)
beschreibung TEXT (optional)
```

### config
```
key             TEXT PRIMARY KEY
value           TEXT (Werte sind immer TEXT, z.B. Channel-ID "123456789")
```

Wichtige Config-Keys:
- `entry_channel_id`, `search_channel_id`, `log_channel_id`
- `farm_forum_channel_id`, `struktur_forum_channel_id`, `biom_forum_channel_id`, `base_forum_channel_id`
- `bestellungen_channel_id`, `bestellungen_forum_channel_id`

---

## 🎮 Haupt-Flows

### Flow 1: Eintragen
```
Button "Eintragen" 
  → CategorySelect (Struktur/Biom/Farm/Base)
  → ItemSelect (Liste wählen, max 25 pro Seite, suchbar)
  → EntryModal (Name, X/Z, Y optional, Beschreibung; bei Farms zusätzlich Specs)
  → Bestätigung
  → TagsModal (Overworld/Nether/End + custom)
  → Optional: YouTube-Link-Modal (Farmen)
  → Optional: Farbe-Wahl
  → Bilder hochladen (im Channel, Bot archiviert in Image-Channel)
  → Forum-Beitrag erstellt (mit Tags) wenn verknüpft
  → Entry in DB gespeichert
```

**Wichtige Funktionen**:
- `database.insert_entry(name, typ, x, y, z, beschreibung, specs, tags, ...)`
- `database.add_image(entry_id, url, beschreibung)`
- `_resolve_forum_tags(guild, tags)` → Discord Forum-Tags erstellen
- `_get_image_channel(guild)` → Archiv-Channel finden/erstellen

---

### Flow 2: Suchen
```
Button "Suchen"
  → CategorySelect
  → ItemSelect (oder "Alle Einträge dieser Kategorie")
  → SearchModal (Suchbegriff optional, Position optional: "X Z" oder "X Y Z")
  → Embed-Liste mit Pagination
    ├─ Koordinaten, Beschreibung
    ├─ 🖼️ Bilder (eingeklappt, Button expandiert)
    ├─ 📊 Specs (eingeklappt, Button expandiert)
    ├─ 📏 Entfernung-Button (berechnet Distanz: sqrt((user_x - entry_x)² + (user_z - entry_z)²))
    └─ Weitere Navigation mit ← → Buttons
```

**Wichtige Funktionen**:
- `database.search_entries(typ, name_filter, user_x, user_z)`
- `_calculate_distance(x1, z1, x2, z2)` → Float (in Blöcken)

---

### Flow 3: Löschen (Admin)
```
/eintrag_loeschen           # Interaktiv (wie Suchen, aber mit 🗑️-Button)
/eintrag_loeschen 42        # Direkt (ID → Löschen)
  → Entry gelöscht
  → Forum-Thread gelöscht (wenn vorhanden)
  → Log-Action erstellt
```

---

### Flow 4: Bestellungen (in orders.py)
```
Button "📋 Bestellung/Auftrag"
  → Typ: 📦 Bestellung (Items farmen) oder 🛠️ Auftrag (z.B. Weg bauen)
  → Modal: Titel/Beschreibung
  → Dringlichkeit: 🟢 Niedrig / 🟡 Mittel / 🟠 Hoch / 🔴 Dringend
  → Optional: Mehrere Personen pingen (Mentions)
  → Optional: YouTube-Link
  → Optional: Bilder
  → Forum-Beitrag mit Status-Tags (Offen/In Bearbeitung/Erledigt)
  
Nach Erstellung:
  → Button "🔧 In Bearbeitung" (wer macht's?) + Tag-Update
  → Button "✅ Fertig" (optional Bild-Modal) + Tag-Update + Ping Requester
```

---

## 🔧 Neue Features hinzufügen - Checkliste

### ✅ Neue Struktur/Biom/Farm-Typ
```python
# views.py, Zeile ~52-77
STRUCTURES: List[Tuple[str, str]] = [
    ("Village", "🏘️"),
    ("Stronghold", "🏰"),
    ("Meine neue Struktur", "🆕"),  # ← Hier einfügen!
]
```

### ✅ Neue Spalte in entries-Tabelle
1. `database.py` → `init_db()` → `ALTER TABLE entries ADD COLUMN ...`
2. `database.py` → `insert_entry()` anpassen
3. `database.py` → `get_entry()` anpassen
4. Ggf. in `views.py` UI updaten (Modal-Felder, Embed-Anzeige)

### ✅ Neuer Admin-Command
```python
# bot.py
@bot.tree.command(name="mein_command", description="...")
@app_commands.checks.has_permissions(administrator=True)
async def mein_command(interaction: discord.Interaction) -> None:
    # Dein Code
    await interaction.response.send_message("✅ Fertig!", ephemeral=True)

# Error-Handler hinzufügen:
@mein_command.error
async def mein_command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Admin-Rechte nötig!", ephemeral=True)
```

### ✅ Neuer Button/Modal
```python
# views.py oder orders.py
class MeinButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Klick mich", style=discord.ButtonStyle.green)
    async def mein_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MeinModal())

class MeinModal(discord.ui.Modal, title="Mein Modal"):
    eintrag = discord.ui.TextInput(label="Name", placeholder="...")
    
    async def on_submit(self, interaction: discord.Interaction):
        # Dein Code
        await interaction.response.send_message(f"✅ Du hast '{self.eintrag}' eingegeben!", ephemeral=True)
```

### ✅ Neue DB-Funktion
```python
# database.py
async def meine_funktion(param):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT * FROM entries WHERE ...", (param,))
        rows = await cursor.fetchall()
        await cursor.close()
    return rows
```

---

## 🔐 Best Practices

### 1. Admin-Checks immer nutzen
```python
@app_commands.checks.has_permissions(administrator=True)
```

### 2. Ephemere Messages für Bestätigungen
```python
await interaction.response.send_message("✅ Erfolg!", ephemeral=True)
```

### 3. Error-Handler für Commands
```python
@command_name.error
async def command_error(interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Admin-Rechte nötig!", ephemeral=True)
    else:
        print(f"Fehler: {error}")
        await interaction.response.send_message("❌ Fehler aufgetreten!", ephemeral=True)
```

### 4. Typen konsequent nutzen
```python
from typing import Optional, List, Dict, Any, Tuple
async def meine_funktion(user_id: int, name: str) -> Optional[Dict[str, Any]]:
    ...
```

### 5. Logging für wichtige Aktionen
```python
from logs import log_action
await log_action(
    interaction.guild,
    discord.Embed(
        title="🆕 Neuer Eintrag",
        description=f"**{name}** von {interaction.user.mention}",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
)
```

### 6. Timeout-Fehler bei Modal-Interaktionen
```python
class MeinModal(discord.ui.Modal, title="...", timeout=300):  # 5 Min
    ...
```

---

## 🎨 Code-Stil & Konventionen

**Emojis für Feedback**:
- ✅ Erfolgreiche Aktionen
- ❌ Fehler
- 🗑️ Löschungen
- 📝 Logging
- 🏛️ 🌳 🚜 🏘️ für Kategorien
- 📍 für Koordinaten
- 🖼️ für Bilder
- 📊 für Specs

**Embed-Farben**:
```python
discord.Color.green()     # ✅ Erfolg
discord.Color.red()       # ❌ Fehler/Löschen
discord.Color.blurple()   # 🔍 Suchen/Neutrale Infos
discord.Color.greyple()   # 📝 Logs
discord.Color.gold()      # ⭐ Wichtige Infos
```

**Dateistruktur**:
- `bot.py`: Commands + Event-Handler
- `views.py`: UI-Komponenten (Views, Modals, Button Handlers)
- `database.py`: DB-Operationen (async)
- `orders.py`: Bestellungs-Logik (Views + DB)
- `logs.py`: Logging-Helfer

---

## 🐛 Häufige Probleme & Lösungen

| Problem | Lösung |
|---------|--------|
| Slash-Commands werden nicht angezeigt | `!sync <server_id>` ausführen (im Bot-Owner DM) |
| "Interaction failed" bei Modal | Modal.timeout zu kurz? oder Fehler im on_submit? Logs checken |
| Forum-Thread wird nicht erstellt | Forum-Channel-ID in Config überprüfen, `_resolve_forum_tags()` Debug |
| Images werden nicht gespeichert | Image-Archiv-Channel existiert? `_get_image_channel()` Debug |
| Bot antwortet nicht auf Button-Clicks | Persistente Views in `setup_hook()` registriert? `self.add_view(MeinView())` |
| Timeouts bei langen Operationen | Discord-Timeout ist 3 Sekunden, dann `defer()` nutzen |

---

## 🚀 Erste Schritte für neue Features

1. **Überblick verschaffen**:
   - Welche Dateien sind betroffen? (bot.py, views.py, database.py, orders.py, logs.py)
   - Brauche ich neue Datenbank-Spalten?
   - Brauche ich neue Buttons/Modals?

2. **Datenbank-Schema updaten** (falls nötig):
   - `database.py` → `init_db()`
   - `database.py` → CRUD-Funktionen
   - Test: `await init_db()` in Python REPL

3. **UI implementieren**:
   - Neue View/Modal in `views.py` oder `orders.py`
   - In `bot.py` registrieren (setup_hook oder inline)

4. **Command schreiben** (falls nötig):
   - Slash-Command in `bot.py`
   - Error-Handler
   - Test: `/command` aufrufen

5. **Logging hinzufügen**:
   - `log_action()` aufrufen nach wichtigen Aktionen
   - Schöne Embeds mit Emojis & Timestamps

6. **Testen & Synchronisieren**:
   - `!sync <server_id>` für Testing
   - `!sync` für global (kann 1h dauern)

---

## 📚 Wichtige Imports

```python
# bot.py
import os, discord, commands, app_commands, dotenv
import database as db, orders, logs, views

# views.py
import discord, ui, asyncio, math, re
import database as db, logs, views

# database.py
import aiosqlite
from pathlib import Path

# orders.py
import discord, ui, asyncio
import database as db, logs, views

# logs.py
import discord
```

---

## 💡 Pro-Tipps für Entwickler

1. **Modal-Felder validieren**:
   ```python
   try:
       x = float(self.x.value)
   except ValueError:
       await interaction.response.send_message("❌ X muss eine Zahl sein!", ephemeral=True)
       return
   ```

2. **Große Listen paginieren**:
   - Dropdowns maximal 25 Optionen
   - Dann: Pfeil-Buttons für Seiten + Suchfeld

3. **Forum-Posts verknüpfen**:
   - Thread-ID in `forum_thread_id` speichern
   - Bei Löschung: Thread löschen mit `await thread.delete()`

4. **Bilder dauerhaft speichern**:
   - Discord löscht temporäre URLs nach ~24h
   - Solution: Bilder in privaten "Image-Archive"-Channel hochladen
   - URL des Archiv-Bildes speichern

5. **User-Input sanitizen**:
   ```python
   name = self.name.value.strip()[:100]  # Max 100 Zeichen, kein Whitespace
   ```

---

**Version**: 1.0 (Sept 2024)
**Zuletzt aktualisiert**: Skill-Dokumentation
**Ort**: `.github/ai-skills/`
