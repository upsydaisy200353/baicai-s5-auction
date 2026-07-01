"""SQLite 名单库"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from constants import POOL_LETTERS

DB_PATH = Path(__file__).resolve().parent / "auction.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS roster (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sort_order INTEGER NOT NULL,
    identity TEXT NOT NULL CHECK(identity IN ('player', 'captain')),
    serial TEXT,
    name TEXT NOT NULL,
    pool_letter TEXT NOT NULL CHECK(pool_letter IN ('A','B','C','D','E')),
    start_price INTEGER NOT NULL DEFAULT 0,
    buyout_price INTEGER,
    funds INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_roster_sort ON roster(sort_order);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'captain')),
    captain_name TEXT,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
    migrate_db()


def migrate_db() -> None:
    with connect() as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(roster)").fetchall()}
        if "avatar" not in cols:
            conn.execute("ALTER TABLE roster ADD COLUMN avatar TEXT")


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    pool_letter = row["pool_letter"]
    position = POOL_LETTERS[pool_letter]
    return {
        "id": row["id"],
        "sortOrder": row["sort_order"],
        "identity": row["identity"],
        "serial": row["serial"],
        "name": row["name"],
        "poolLetter": pool_letter,
        "position": position,
        "startPrice": row["start_price"],
        "buyoutPrice": row["buyout_price"],
        "funds": row["funds"],
        "avatar": row["avatar"] if "avatar" in row.keys() else None,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def list_roster() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM roster ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_entry(entry_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM roster WHERE id = ?", (entry_id,)).fetchone()
    return row_to_dict(row) if row else None


def next_sort_order(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM roster").fetchone()
    return int(row["n"])


def create_entry(data: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    with connect() as conn:
        sort_order = data.get("sortOrder") or next_sort_order(conn)
        cur = conn.execute(
            """
            INSERT INTO roster
              (sort_order, identity, serial, name, pool_letter,
               start_price, buyout_price, funds, avatar, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sort_order,
                data["identity"],
                data.get("serial"),
                data["name"],
                data["poolLetter"],
                data.get("startPrice", 0),
                data.get("buyoutPrice"),
                data.get("funds"),
                data.get("avatar"),
                now,
                now,
            ),
        )
        entry_id = cur.lastrowid
    return get_entry(entry_id)  # type: ignore


def update_entry(entry_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_entry(entry_id)
    if not existing:
        return None
    merged = {**existing, **data, "id": entry_id}
    now = _now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE roster SET
              sort_order = ?,
              identity = ?,
              serial = ?,
              name = ?,
              pool_letter = ?,
              start_price = ?,
              buyout_price = ?,
              funds = ?,
              avatar = ?,
              updated_at = ?
            WHERE id = ?
            """,
            (
                merged["sortOrder"],
                merged["identity"],
                merged.get("serial"),
                merged["name"],
                merged["poolLetter"],
                merged["startPrice"],
                merged.get("buyoutPrice"),
                merged.get("funds"),
                merged.get("avatar"),
                now,
                entry_id,
            ),
        )
    return get_entry(entry_id)


def delete_entry(entry_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM roster WHERE id = ?", (entry_id,))
    return cur.rowcount > 0


def clear_roster() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM roster")


def count_roster() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM roster").fetchone()
    return int(row["c"])


def user_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "passwordHash": row["password_hash"],
        "role": row["role"],
        "captainName": row["captain_name"],
        "displayName": row["display_name"],
        "createdAt": row["created_at"],
    }


def list_users() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return [user_row_to_dict(r) for r in rows]


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return user_row_to_dict(row) if row else None


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return user_row_to_dict(row) if row else None


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO users
              (username, password_hash, role, captain_name, display_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["username"],
                data["passwordHash"],
                data["role"],
                data.get("captainName"),
                data.get("displayName") or data["username"],
                now,
            ),
        )
        uid = cur.lastrowid
    return get_user_by_id(uid)  # type: ignore


def count_users() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    return int(row["c"])


def clear_users() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM users")
