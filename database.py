"""
Einfache SQLite-Datenbank für den Struktur/Biom/Farm-Finder-Bot.
Speichert Konfiguration (Channel-IDs), Einträge, Bilder (inkl. Beschreibung) und
Farm-Specs.
"""

import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

DB_PATH = Path(__file__).parent / "data.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                typ            TEXT NOT NULL,
                x              REAL NOT NULL,
                y              REAL,
                z              REAL NOT NULL,
                beschreibung   TEXT,
                specs          TEXT,
                forum_thread_id INTEGER,
                tags           TEXT,
                youtube_link   TEXT,
                color          TEXT,
                ersteller_id   INTEGER,
                ersteller_name TEXT,
                erstellt_am    TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                url      TEXT NOT NULL,
                caption  TEXT
            )
            """
        )

        # Migration: Falls die Datenbank noch aus einer älteren Version des Bots
        # stammt, existieren manche Spalten evtl. noch nicht - dann per
        # ALTER TABLE nachrüsten. Schlägt fehl (Spalte existiert schon), wird
        # das einfach ignoriert.
        for statement in (
            "ALTER TABLE entries ADD COLUMN specs TEXT",
            "ALTER TABLE entries ADD COLUMN forum_thread_id INTEGER",
            "ALTER TABLE entries ADD COLUMN tags TEXT",
            "ALTER TABLE entries ADD COLUMN youtube_link TEXT",
            "ALTER TABLE entries ADD COLUMN color TEXT",
            "ALTER TABLE images ADD COLUMN caption TEXT",
        ):
            try:
                await conn.execute(statement)
            except aiosqlite.OperationalError:
                pass

        await conn.commit()


async def set_config(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        await conn.commit()


async def get_config(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT value FROM config WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


async def add_entry(
    name: str,
    typ: str,
    x: float,
    y: Optional[float],
    z: float,
    beschreibung: Optional[str],
    ersteller_id: int,
    ersteller_name: str,
    specs: Optional[str] = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            """
            INSERT INTO entries (name, typ, x, y, z, beschreibung, specs, ersteller_id, ersteller_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, typ, x, y, z, beschreibung, specs, ersteller_id, ersteller_name),
        )
        await conn.commit()
        return cur.lastrowid


async def add_images(entry_id: int, urls: List[str]) -> List[int]:
    """Fügt Bilder (zunächst ohne Beschreibung) hinzu und liefert die neu
    vergebenen Bild-IDs zurück, damit sie danach beschriftet werden können."""
    if not urls:
        return []
    async with aiosqlite.connect(DB_PATH) as conn:
        ids: List[int] = []
        for url in urls:
            cur = await conn.execute(
                "INSERT INTO images (entry_id, url) VALUES (?, ?)", (entry_id, url)
            )
            ids.append(cur.lastrowid)
        await conn.commit()
        return ids


async def set_image_caption(image_id: int, caption: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE images SET caption = ? WHERE id = ?", (caption, image_id))
        await conn.commit()


async def set_forum_thread(entry_id: int, thread_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE entries SET forum_thread_id = ? WHERE id = ?", (thread_id, entry_id)
        )
        await conn.commit()


async def set_entry_tags(entry_id: int, tags: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE entries SET tags = ? WHERE id = ?", (tags, entry_id))
        await conn.commit()


async def set_entry_youtube(entry_id: int, youtube_link: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE entries SET youtube_link = ? WHERE id = ?", (youtube_link, entry_id)
        )
        await conn.commit()


async def set_entry_color(entry_id: int, color: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE entries SET color = ? WHERE id = ?", (color, entry_id))
        await conn.commit()


async def search_entries(
    term: str = "", typ: Optional[Union[str, List[str]]] = None
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM entries WHERE 1=1"
    params: List[Any] = []
    if term:
        query += " AND name LIKE ?"
        params.append(f"%{term}%")
    if typ:
        if isinstance(typ, (list, tuple, set)):
            placeholders = ",".join("?" for _ in typ)
            query += f" AND typ IN ({placeholders})"
            params.extend(typ)
        else:
            query += " AND typ = ?"
            params.append(typ)
    query += " ORDER BY name COLLATE NOCASE"

    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_used_types() -> List[str]:
    """Liefert alle 'typ'-Werte, für die es mindestens einen Eintrag gibt."""
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT DISTINCT typ FROM entries") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def get_entry(entry_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_images(entry_id: int) -> List[str]:
    """Nur die URLs (ohne Beschreibung) - für einfache Anwendungsfälle."""
    full = await get_images_full(entry_id)
    return [r["url"] for r in full]


async def get_images_full(entry_id: int) -> List[Dict[str, Any]]:
    """Bilder inkl. ID und Beschreibung, z.B. zum nachträglichen Beschriften."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT id, url, caption FROM images WHERE entry_id = ?", (entry_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def update_entry(
    entry_id: int,
    name: Optional[str] = None,
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
    beschreibung: Optional[str] = None,
    specs: Optional[str] = None,
    _unset_y: bool = False,
) -> None:
    """
    Aktualisiert die Kern-Felder eines Eintrags. Nur übergebene (nicht-None)
    Felder werden geändert - Felder, die weggelassen werden, bleiben
    unverändert. Um Y explizit auf NULL zu setzen (2D-Koordinate ohne Höhe),
    _unset_y=True übergeben.
    """
    updates: Dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if x is not None:
        updates["x"] = x
    if y is not None or _unset_y:
        updates["y"] = y
    if z is not None:
        updates["z"] = z
    if beschreibung is not None:
        updates["beschreibung"] = beschreibung
    if specs is not None:
        updates["specs"] = specs

    if not updates:
        return

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [entry_id]
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(f"UPDATE entries SET {set_clause} WHERE id = ?", params)
        await conn.commit()


async def delete_image(image_id: int) -> None:
    """Entfernt ein einzelnes Bild (nur den Datenbank-Eintrag/Link, nicht die
    Datei im Archiv-Channel)."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
        await conn.commit()


async def delete_entry(entry_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM images WHERE entry_id = ?", (entry_id,))
        cur = await conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        await conn.commit()
        return cur.rowcount > 0