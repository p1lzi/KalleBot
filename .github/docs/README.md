# 📖 KalleBot Dokumentation

Detaillierte Dokumentation für Entwickler und KI-Assistenten.

## 📂 Inhalt

### 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md)
System-Architektur des Bots:
- Modulare Struktur (Core Bot, Entries System, Orders System)
- Inter-System Kommunikation
- Datenbank-Relationen
- Erweiterungspunkte
- Performance-Überlegungen

### 💾 [DATABASE.md](DATABASE.md)
Komplettes Datenbank-Schema:
- Alle 4 Tabellen (`config`, `entries`, `images`, `orders`)
- Spalten-Details mit Beispielen
- Relations & Constraints
- Query-Beispiele
- Performance-Tipps
- Backup & Restore

### 📋 [FEATURES.md](FEATURES.md) *(noch zu erstellen)*
Feature-Status und Roadmap:
- Implementierte Features
- Geplante Features
- Bug-Fixes
- Breaking Changes

---

## 🚀 Schnelle Links

**Für KI-Assistenten starten**: [`../ai-skills/kallebot-skill.md`](../ai-skills/kallebot-skill.md)

**Technische Details lesen**: [`ARCHITECTURE.md`](ARCHITECTURE.md)

**Datenbank verstehen**: [`DATABASE.md`](DATABASE.md)

---

## 🎯 Dokumentation nach Use-Case

### "Ich will einen neuen Admin-Command hinzufügen"
1. Lese: [`ai-skills/kallebot-skill.md`](../ai-skills/kallebot-skill.md) → "Neuer Admin-Command hinzufügen"
2. Referenz: [`ARCHITECTURE.md`](ARCHITECTURE.md) → "Core Bot"

### "Ich will eine neue Struktur/Biom-Typ hinzufügen"
1. Schnell: [`ai-skills/kallebot-skill.md`](../ai-skills/kallebot-skill.md) → "Neue Struktur/Biom/Farm-Typ"
2. Fertig in 2 Minuten!

### "Ich will eine neue Datenbank-Spalte hinzufügen"
1. Lese: [`DATABASE.md`](DATABASE.md) → Aktuelles Schema
2. Lese: [`ai-skills/kallebot-skill.md`](../ai-skills/kallebot-skill.md) → "Neue Spalte in entries-Tabelle"
3. Frage: Brauche ich auch UI-Änderungen in `views.py`?

### "Ich verstehe den Bot-Code nicht"
1. Starte: [`ARCHITECTURE.md`](ARCHITECTURE.md) → "Übersicht"
2. Details: [`ARCHITECTURE.md`](ARCHITECTURE.md) → relevantes Modul (Core, Entries, Orders)
3. Spezifisch: [`DATABASE.md`](DATABASE.md) → Datenbank verstehen

### "Ich will Orders mit Entries verknüpfen"
1. Lese: [`DATABASE.md`](DATABASE.md) → `orders` Tabelle
2. Plan: Neue Spalte `entry_id` in `orders`? oder umgekehrt?
3. Referenz: [`ARCHITECTURE.md`](ARCHITECTURE.md) → "Erweiterungspunkte"

---

## 📚 Dokumentations-Konventionen

- **Code-Blöcke**: ```python ... ```
- **SQL-Queries**: ```sql ... ```
- **Tabellen**: Markdown-Format
- **Emojis**: Für schnelle Orientierung
- **Links**: Zu relevanten Dateien im Projekt

---

## ✨ Wie die Dokumentation aktuell bleibt

1. **Bei DB-Änderungen**: `DATABASE.md` updaten
2. **Bei Architektur-Änderungen**: `ARCHITECTURE.md` updaten
3. **Bei neuen Features**: `FEATURES.md` updaten
4. **Bei Feature-Checklisten-Änderungen**: `../ai-skills/kallebot-skill.md` updaten

---

**Version**: 1.0
**Letzte Aktualisierung**: Sept 2024
