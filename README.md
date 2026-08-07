# Minecraft Struktur/Biom/Farm/Base-Finder Bot

Ein Discord-Bot, mit dem eure Community gefundene Strukturen, Biome,
gebaute Farmen und Basen (mit Koordinaten und Bildern) einträgt, damit
andere sie leicht wiederfinden. Zusätzlich gibt es ein Bestellsystem,
über das man anfragen kann, dass jemand etwas für einen farmt.

## Funktionen

- **Eintragen-Channel**: Button "📍 Eintragen" → Dropdown "Struktur,
  Biom, Farm oder Base?" → zweites Dropdown mit der passenden Liste
  (bei Struktur z.B. Village, Stronghold, Nether Fortress, ...; bei
  Biom z.B. Desert, Jungle, Savanna, ...; bei Farm z.B. Iron Farm, Gold
  Farm, Raid Farm, ...; bei Base z.B. Hauptbase, Shop,
  Redstone-Werkstatt, ...) → Formular (Name, Koordinaten,
  Beschreibung, bei Farmen zusätzlich ein **Specs-Feld** für
  Rate/AFK-Spot/Notizen).
  Alles läuft ephemeral ab, d.h. nur die Person, die einträgt, sieht
  die Zwischenschritte. Anschließend kann man optional Bild(er) in den
  Channel hochladen – der Bot liest sie aus, speichert sie **gruppiert**
  (statt einzeln) in einem versteckten Archiv-Channel und **löscht die
  Bild-Nachrichten danach automatisch wieder**, damit der Channel
  aufgeräumt bleibt. Über den Button "📝 Bilder beschreiben" können die
  hochgeladenen Bilder direkt im Anschluss mit einer kurzen Beschreibung
  versehen werden.
- **Tags (bei allem) & YouTube-Link (nur bei Farmen) & Farbe (bei
  allem)**: Nach dem Eintragen erscheint bei **jeder Kategorie** eine
  optionale Ansicht zum Vergeben von Tags – per Dropdown aus
  Vorschlägen (**Overworld, Nether, End**) und/oder frei über
  "➕ Eigenen Tag hinzufügen" (z.B. "Redstone", "Survival", "1.21").
  Bei **Farmen** kann danach noch optional ein **YouTube-Tutorial-Link**
  hinterlegt werden; bei **Strukturen, Biomen und Basen** entfällt nur
  dieser eine Schritt (YouTube-Links ergeben dort keinen Sinn) – es geht
  direkt weiter zur Farbauswahl. Am Ende (bei jeder Kategorie) kann
  noch eine **individuelle Embed-Farbe** für genau diesen Eintrag
  festgelegt werden (Vorschläge wie Rot/Grün/Blau/... oder ein eigener
  Hex-Code über "🎨 Eigene Farbe (Hex)") – überschreibt die sonst nach
  Kategorie vergebene Standardfarbe (blau/grün/gold). Alle Schritte
  sind komplett freiwillig – werden sie übersprungen, hat der Eintrag
  einfach keine Tags/kein Video/die Standardfarbe.
- **Duplikat-Warnung im Umkreis**: Beim Eintragen einer **Struktur**
  oder eines **Bioms** (nicht bei Farmen) prüft der Bot, ob im Umkreis
  von 100 Blöcken (X/Z) bereits ein Eintrag desselben Typs existiert.
  Falls ja, wird vor dem Speichern nachgefragt und der nahegelegene
  Eintrag (Name, Koordinaten, Entfernung, Beschreibung **und dessen
  Bilder**) angezeigt – über "✅ Trotzdem eintragen" bzw.
  "❌ Abbrechen" entscheidet man dann selbst, ob wirklich ein zweiter
  Eintrag angelegt werden soll.
- **Suchen-Channel**: Button "🔍 Suchen" → Dropdown "Struktur, Biom
  oder Farm?" → zweites Dropdown mit der passenden Liste (oder "Alle
  Strukturen"/"Alle Biome"/"Alle Farmen") → Formular (Name optional,
  eigene aktuelle Position optional). Man erhält den passenden Treffer
  als übersichtliches Embed mit Feldern für Kategorie, Koordinaten,
  Entfernung, Tags und Beschreibung, plus einem Link-Button
  "▶️ Tutorial ansehen", falls ein YouTube-Link hinterlegt ist.
  **Bilder und Farm-Specs sind standardmäßig eingeklappt** und lassen
  sich per Button ("🖼️ Bilder anzeigen" / "🔧 Specs anzeigen") gezielt
  einblenden. Über "📏 Entfernung berechnen" lässt sich die Distanz auch
  nachträglich (ohne die Suche neu zu starten) berechnen – alle
  Treffer werden dabei automatisch nach Entfernung sortiert. Komplett
  ephemeral, sichtbar nur für die suchende Person.
- **Bestellungen-Channel** (eigenständiges System, unabhängig von den
  Einträgen oben): Button "📦 Bestellung aufgeben" → Modal (Was soll
  gefarmt werden?, Beschreibung optional) → Dropdown für die
  **Dringlichkeit** (🟢 Niedrig, 🟡 Mittel, 🟠 Hoch, 🔴 Dringend) →
  optional eine **bestimmte Person pingen** (Nutzer-Auswahl) → optional
  ein **YouTube-Video** verlinken (z.B. Tutorial, wo man das Item
  bekommt) → optional **Bilder** hochladen (z.B. ein Bild des
  gewünschten Items). Ist ein Bestellungen-Forum verknüpft
  (`/setup_bestellungen_forum`), wird automatisch ein Forum-Beitrag
  erstellt (Titel = gewünschtes Item, gepingte Person wird direkt beim
  Erstellen im Beitrag benachrichtigt) und bekommt automatisch die
  Tags **"Offen"** sowie die gewählte Dringlichkeit als echte
  Discord-Forum-Tags. Der Beitrag hat zwei Buttons:
  - **"🔧 In Bearbeitung"** – setzt den Status um, der Tag wechselt von
    "Offen" auf "In Bearbeitung".
  - **"✅ Fertig"** – fragt optional nach einem Bild, wo die Kiste mit
    den Items steht, setzt den Tag auf "Erledigt" und **pingt die
    Person, die die Bestellung aufgegeben hat**, direkt im
    Forum-Beitrag.
- **Log-Channel**: Optionaler Channel, in dem neue Einträge, hinzugefügte
  Bilder und Löschungen automatisch protokolliert werden (mit Name,
  Kategorie, ID und wer die Aktion ausgeführt hat).
- **Struktur-/Biom-/Farm-/Base-Forum**: Bis zu vier unabhängige,
  optionale Forum-Channel – je einer für Strukturen
  (`/setup_struktur_forum`), Biome (`/setup_biom_forum`), Farmen
  (`/setup_farm_forum`) und Basen (`/setup_base_forum`). Ist für
  die jeweilige Kategorie ein Channel verknüpft, wird beim Eintragen
  automatisch ein eigener Forum-Beitrag darin erstellt, sobald auch
  eventuell hochgeladene Bilder gespeichert sind. Der Beitrag besteht
  aus mehreren Embeds: ein Haupt-Embed mit Kategorie, Koordinaten und
  ID, ein separates **"📋 Details"-Embed** für Beschreibung, Specs
  (nur bei Farmen), Tags und YouTube-Link (nur bei Farmen, jeweils nur
  falls vorhanden), sowie **ein eigenes Embed pro Bild** inklusive der
  jeweiligen Bildbeschreibung als Footer. Zusätzlich werden vergebene
  Tags als **echte Discord-Forum-Tags** am Beitrag angewendet (nicht
  nur als Text) – fehlen sie noch am jeweiligen Forum-Channel, legt
  der Bot sie automatisch an (bis zu 20 Tags pro Channel, 5 pro
  Beitrag sind Discord-Limits). Dadurch lässt sich in jedem
  Forum-Channel über Discords eingebauten Tag-Filter danach
  suchen/filtern (z.B. alle Strukturen mit Tag "Nether"). Wird eine
  Bildbeschreibung, ein Tag, ein YouTube-Link (Farmen) oder die Farbe
  nachträglich gesetzt, aktualisiert sich der Forum-Beitrag (inkl.
  Tags) automatisch mit. Löschst du den Eintrag (egal ob per ID oder
  über den interaktiven Löschen-Flow), wird der zugehörige
  Forum-Beitrag ebenfalls automatisch gelöscht. In den Suchergebnissen
  erscheint zusätzlich ein Link-Button "💬 Zum Forum-Beitrag". Der
  Forum-Beitrag selbst hat außerdem zwei Buttons **"✏️ Bearbeiten"**
  und **"🗑️ Löschen"** direkt unter dem Beitrag. "✏️ Bearbeiten" öffnet
  ein Menü mit den für die Kategorie passenden Optionen:
  - 📝 **Details** – Name, Koordinaten, Beschreibung (bei Farmen
    zusätzlich Specs)
  - 🎨 **Farbe ändern**
  - 🔗 **YouTube-Link ändern/entfernen** (nur bei Farmen)
  - 🖼️ **Bilder verwalten** – durchblättern, Beschreibungen ändern,
    einzelne Bilder löschen oder neue hinzufügen

  "🗑️ Löschen" entfernt den Eintrag (inkl. Forum-Beitrag) komplett,
  ohne extra in den Eintragen/Löschen-Channel wechseln zu müssen. Beide
  Buttons funktionieren auch nach einem Bot-Neustart weiter und dürfen
  nur von der Person, die den Eintrag ursprünglich angelegt hat, oder
  von Admins (Administrator- bzw. Manage-Messages-Rechte im
  Forum-Channel) benutzt werden. Dasselbe Bearbeiten-Menü ist auch über
  "✏️ Bearbeiten" in den Suchergebnissen (für Ersteller/Admins) und im
  `/eintrag_loeschen`-Durchklick-Flow (Admins) erreichbar.
- Die Dropdowns beim **Suchen** und **Löschen** zeigen nur Kategorien
  an, für die es tatsächlich schon Einträge gibt – kein Scrollen durch
  leere Strukturen/Biome/Farmen mehr. Beim **Eintragen** bleibt die
  volle Liste sichtbar, damit auch der erste Eintrag einer Kategorie
  angelegt werden kann.
- Alle Einträge werden in farblich unterschiedlichen, mit Emoji und
  Feldern übersichtlich aufbereiteten Embeds angezeigt (blau für
  Strukturen, grün für Biome, gold für Farmen).
- Alle Daten werden dauerhaft in einer lokalen SQLite-Datenbank
  (`data.db`) gespeichert.
- Buttons funktionieren auch nach einem Neustart des Bots weiter.

## 1. Bot im Discord Developer Portal anlegen

1. Gehe zu https://discord.com/developers/applications und klicke auf
   **New Application**.
2. Unter **Bot** → **Reset Token**, den Token kopieren (wird gleich
   gebraucht).
3. Unter **Bot** → **Privileged Gateway Intents** die Option
   **Message Content Intent** aktivieren (wird für das Erkennen von
   hochgeladenen Bildern benötigt).
4. Unter **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: mindestens `Send Messages`, `Embed Links`,
     `Attach Files`, `Read Message History`, `Add Reactions`,
     `Manage Messages` (zum Aufräumen der Bild-Nachrichten),
     `Manage Channels` (zum automatischen Anlegen des versteckten
     Bild-Archiv-Channels), `Create Public Threads`,
     `Send Messages in Threads` und `Manage Threads` (für die
     automatischen Farm-Forum-Beiträge inkl. Aktualisieren/Löschen,
     nur nötig wenn `/setup_struktur_forum`, `/setup_biom_forum` oder
     `/setup_farm_forum` genutzt wird)
   - Die generierte URL öffnen und den Bot auf euren Server einladen.

## 2. Projekt einrichten (venv)

```bash
# Ins Projektverzeichnis wechseln
cd minecraft-finder-bot

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Aktivieren
# Linux/Mac:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Alternative: Docker

Statt venv kann der Bot auch als Docker-Container laufen (`Dockerfile`
und `docker-compose.yml` liegen bereits im Projekt):

```bash
# .env vorher wie in Schritt 3 beschrieben anlegen, dann:
docker compose up -d --build
```

Das startet den Bot im Hintergrund und mountet `data.db` als Datei ins
Projektverzeichnis, damit die Datenbank auch Neustarts/Neubauten des
Containers übersteht. Logs ansehen: `docker compose logs -f`.
Ohne docker-compose geht es auch direkt:

```bash
docker build -t minecraft-finder-bot .
docker run -d --name minecraft-finder-bot \
  --env-file .env \
  -v "$(pwd)/data.db:/app/data.db" \
  minecraft-finder-bot
```

## 3. Token hinterlegen

Kopiere `.env.example` zu `.env` und trage deinen Bot-Token ein:

```bash
cp .env.example .env
```

```
DISCORD_TOKEN=dein_echter_token
```

Optional kannst du dort auch den **Bot-Status** anpassen (wird unter
dem Bot-Namen als "Spielt ..." angezeigt):

```
BOT_ACTIVITY_TYPE=playing
BOT_ACTIVITY_NAME=Minecraft
```

- `BOT_ACTIVITY_TYPE`: `playing` ("Spielt ..."), `watching`
  ("Schaut ..."), `listening` ("Hört ...") oder `competing`
  ("Tritt an in ...")
- `BOT_ACTIVITY_NAME`: der Text danach, z.B. `Minecraft`,
  `auf eurem Server`, `nach Strukturen`, ...

Beide Zeilen weglassen/löschen ergibt "Spielt Minecraft" als Standard.
Änderungen werden erst nach einem Neustart des Bots übernommen.

## 4. Bot starten

```bash
python bot.py
```

(Bei Docker: entfällt, der Container startet den Bot bereits automatisch.)

## 5. Channel einrichten

Auf eurem Server, jeweils im gewünschten Channel ausführen:

- Im Eintragen-Channel: `/setup_eintragen`
- Im Suchen-Channel: `/setup_suchen`
- Im Log-Channel (optional): `/setup_log`
- Im Bestellungen-Channel (optional): `/setup_bestellungen`
- Für Strukturen (optional): `/setup_struktur_forum channel:#dein-forum-channel`
- Für Biome (optional): `/setup_biom_forum channel:#dein-forum-channel`
- Für Farmen (optional): `/setup_farm_forum channel:#dein-forum-channel`
- Für Basen (optional): `/setup_base_forum channel:#dein-forum-channel`
- Für Bestellungen (optional): `/setup_bestellungen_forum channel:#dein-forum-channel`

`/setup_eintragen`, `/setup_suchen`, `/setup_log` und
`/setup_bestellungen` werden im jeweiligen Ziel-Channel ausgeführt und
merken sich diesen. Bei den fünf Forum-Commands wählst du den
Forum-Channel stattdessen direkt als Parameter aus (Discord zeigt beim
Tippen von `#` automatisch nur Forum-Channel zur Auswahl an) – die
Commands können daher von überall aus ausgeführt werden, und du kannst
für jede Kategorie denselben oder unterschiedliche Forum-Channel
verwenden. Alle neun Commands erfordern Administrator-Rechte.
`/setup_eintragen`, `/setup_suchen` und `/setup_bestellungen` posten
zusätzlich den jeweiligen Button dauerhaft in den Channel.

## Weitere Commands

- `/eintrag_loeschen` (Admin) – drei Wege, einen Eintrag zu löschen,
  und zusätzlich die Möglichkeit, ihn zu bearbeiten:
  - `/eintrag_loeschen eintrag_id:<ID>` – löscht sofort per bekannter ID
    (steht in der Bestätigung nach dem Eintragen und in den
    Suchergebnissen).
  - `/eintrag_loeschen` ohne ID – öffnet den gleichen zweistufigen
    Struktur/Biom-Dropdown wie beim Suchen (inkl. Such-Filter),
    anschließend ein Suchfeld für den Namen (leer = alle in der
    Kategorie).
  - In der danach angezeigten Ergebnisliste kannst du dich mit
    "◀ Zurück" / "Weiter ▶" durch die Treffer klicken und mit
    "🗑️ Diesen Eintrag löschen" den gerade angezeigten Eintrag
    entfernen, oder mit **"✏️ Bearbeiten"** stattdessen:
    - 🎨 die **Embed-Farbe** ändern (dieselbe Auswahl wie beim
      Eintragen)
    - 🔗 den **YouTube-Link** ändern oder entfernen
    - 🖼️ die **Bilder verwalten**: durchblättern, Beschreibungen
      ändern ("✏️ Beschreibung ändern"), einzelne Bilder löschen
      ("🗑️ Bild löschen") oder neue hinzufügen
      ("➕ Bild hinzufügen", derselbe Upload-Ablauf wie beim Eintragen
      inkl. "✅ Fertig"-Button)
    - Ein bestehender Farm-Forum-Beitrag wird bei all diesen Änderungen
      automatisch mit aktualisiert.
- `!sync` – synchronisiert die Slash-Commands manuell neu (nur der
  **Bot-Owner** darf das, also der Account, der den Bot im Developer
  Portal erstellt hat). Wird normalerweise nicht gebraucht, da beim
  Start automatisch synchronisiert wird – hilfreich aber, wenn du
  Commands im Code änderst und den Bot nicht neu starten willst:
  - `!sync` – globale Synchronisierung (kann bis zu 1 Stunde dauern,
    bis Discord die Änderung überall anzeigt)
  - `!sync <server_id>` – sofortige Synchronisierung nur auf diesem
    Server (praktisch zum Testen neuer Commands)

## Hinweise

- Koordinaten können als `X Y Z` oder `X Z` eingegeben werden.
- Die Dropdown-Listen (`STRUCTURES` für Strukturen, `BIOMES` für Biome,
  `FARMS` für Farmen) können in `views.py` beliebig angepasst/erweitert
  werden – jeder Eintrag ist ein `(Name, Emoji)`-Tupel. Discord erlaubt
  maximal 25 Optionen pro Dropdown – hat eine Liste mehr Einträge,
  blättert man mit "◀ Zurück" / "Weiter ▶"-Buttons automatisch durch
  die weiteren Seiten. Über den Button "🔍 Suche" kann die Liste
  zusätzlich per Suchbegriff gefiltert werden, damit man nicht lange
  scrollen muss; "✖ Filter zurücksetzen" zeigt wieder die volle Liste.
- Die Entfernungsberechnung bei der Suche nutzt nur X/Z (horizontale
  Entfernung), da das für die Minecraft-Navigation meist relevanter
  ist als die Höhe.
- Die vorgeschlagenen Tags (`PRESET_TAGS` in `views.py`, standardmäßig
  `Overworld`, `Nether`, `End`) lassen sich dort anpassen/erweitern.
  Eigene, freie Tags kann man unabhängig davon jederzeit über
  "➕ Eigenen Tag hinzufügen" ergänzen.
- Die vorgeschlagenen Embed-Farben (`PRESET_COLORS` in `views.py`)
  lassen sich dort ebenfalls anpassen/erweitern; ein beliebiger
  Hex-Code funktioniert unabhängig davon jederzeit über
  "🎨 Eigene Farbe (Hex)".
- Bilder werden nicht selbst in der Datenbank gespeichert, sondern in
  einen automatisch angelegten, versteckten Channel namens
  `bild-archiv` kopiert (nur für den Bot sichtbar) – nur dessen
  dauerhafter Discord-CDN-Link wird in der Datenbank hinterlegt.
  Mehrere gleichzeitig hochgeladene Bilder werden dabei **gruppiert**
  in möglichst wenigen Nachrichten gespeichert (Discord erlaubt bis zu
  10 Anhänge pro Nachricht), statt einzeln verschickt zu werden.
  Dadurch bleiben die Bilder auch dann sichtbar, wenn deine
  ursprüngliche Upload-Nachricht (wie unten beschrieben) gelöscht wird.
  Lösche den `bild-archiv`-Channel nicht manuell, sonst gehen die
  gespeicherten Bilder verloren.
- Bei der Suche/beim Löschen gibt es kein künstliches Limit für die
  Anzahl angezeigter Bilder mehr – gezeigt werden alle vorhandenen
  Bilder eines Eintrags, begrenzt nur durch Discords technisches
  Maximum von 10 Embeds pro Nachricht (1 davon ist für die Infobox
  reserviert, macht maximal 9 Bilder gleichzeitig).
- Bilder und Farm-Specs werden aus Übersichtsgründen standardmäßig
  eingeklappt angezeigt; ein Klick auf "🖼️ Bilder anzeigen" bzw.
  "🔧 Specs anzeigen" blendet sie ein.
- Deine Nachrichten mit den hochgeladenen Bildern im Eintragen-Channel
  werden erst gelöscht, **nachdem** du auf den Button **"✅ Fertig"**
  geklickt hast (oder nach Ablauf der 3 Minuten) – nicht sofort nach
  jedem einzelnen Bild. Der Eintrag selbst wurde zu diesem Zeitpunkt
  bereits gespeichert (das passiert direkt beim Absenden des
  Eintragen-Formulars) – der "Fertig"-Button schließt nur den
  Bild-Upload ab und legt keinen zweiten/neuen Eintrag an.
- Das Specs-Feld beim Eintragen erscheint nur bei der Kategorie
  "Farm" und ist optional (z.B. für Durchsatz, AFK-Position,
  Redstone-Hinweise). Es lässt sich später nicht nachträglich über den
  Bot bearbeiten – dafür den Eintrag löschen und neu anlegen.
- `data.db` liegt im Projektordner und sollte regelmäßig gesichert werden.