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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_orders (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                order_type     TEXT DEFAULT 'bestellung',
                item           TEXT NOT NULL,
                beschreibung   TEXT,
                urgency        TEXT,
                youtube_link   TEXT,
                ping_user_ids  TEXT,
                ping_role_ids  TEXT,
                claimed_by_id  INTEGER,
                claimed_by_name TEXT,
                status         TEXT DEFAULT 'offen',
                forum_thread_id INTEGER,
                ersteller_id   INTEGER,
                ersteller_name TEXT,
                erstellt_am    TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_images (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                url      TEXT NOT NULL,
                caption  TEXT,
                kind     TEXT DEFAULT 'request'
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
            "ALTER TABLE farm_orders ADD COLUMN order_type TEXT DEFAULT 'bestellung'",
            "ALTER TABLE farm_orders ADD COLUMN ping_user_ids TEXT",
            "ALTER TABLE farm_orders ADD COLUMN ping_role_ids TEXT",
            "ALTER TABLE farm_orders ADD COLUMN claimed_by_id INTEGER",
            "ALTER TABLE farm_orders ADD COLUMN claimed_by_name TEXT",
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


# --------------------------------------------------------------------------- #
# Farm-Bestellungen
# --------------------------------------------------------------------------- #

async def add_order(
    item: str,
    beschreibung: Optional[str],
    ersteller_id: int,
    ersteller_name: str,
    order_type: str = "bestellung",
) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "INSERT INTO farm_orders (item, beschreibung, ersteller_id, ersteller_name, order_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (item, beschreibung, ersteller_id, ersteller_name, order_type),
        )
        await conn.commit()
        return cur.lastrowid


async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM farm_orders WHERE id = ?", (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_order_urgency(order_id: int, urgency: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE farm_orders SET urgency = ? WHERE id = ?", (urgency, order_id))
        await conn.commit()


async def set_order_ping_users(order_id: int, user_ids: List[int]) -> None:
    """Speichert die zu pingenden Nutzer als kommagetrennte ID-Liste."""
    value = ",".join(str(uid) for uid in user_ids) if user_ids else None
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE farm_orders SET ping_user_ids = ? WHERE id = ?", (value, order_id)
        )
        await conn.commit()


async def set_order_ping_roles(order_id: int, role_ids: List[int]) -> None:
    """Speichert die zu pingenden Rollen als kommagetrennte ID-Liste."""
    value = ",".join(str(rid) for rid in role_ids) if role_ids else None
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE farm_orders SET ping_role_ids = ? WHERE id = ?", (value, order_id)
        )
        await conn.commit()


async def set_order_claimed(order_id: int, user_id: Optional[int], user_name: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE farm_orders SET claimed_by_id = ?, claimed_by_name = ? WHERE id = ?",
            (user_id, user_name, order_id),
        )
        await conn.commit()


async def set_order_youtube(order_id: int, youtube_link: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE farm_orders SET youtube_link = ? WHERE id = ?", (youtube_link, order_id)
        )
        await conn.commit()


async def set_order_status(order_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE farm_orders SET status = ? WHERE id = ?", (status, order_id))
        await conn.commit()


async def set_order_forum_thread(order_id: int, thread_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE farm_orders SET forum_thread_id = ? WHERE id = ?", (thread_id, order_id)
        )
        await conn.commit()


async def add_order_images(order_id: int, urls: List[str], kind: str = "request") -> None:
    if not urls:
        return
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executemany(
            "INSERT INTO order_images (order_id, url, kind) VALUES (?, ?, ?)",
            [(order_id, url, kind) for url in urls],
        )
        await conn.commit()


async def get_order_images(order_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM order_images WHERE order_id = ?", (order_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_order(order_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM order_images WHERE order_id = ?", (order_id,))
        cur = await conn.execute("DELETE FROM farm_orders WHERE id = ?", (order_id,))
        await conn.commit()
        return cur.rowcount > 0