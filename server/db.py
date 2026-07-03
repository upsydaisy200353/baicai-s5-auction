"""名单库 — 本地 SQLite；线上可接 BidKing 同款 Neon PostgreSQL"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from constants import POOL_LETTERS

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = Path(__file__).resolve().parent / "auction.db"

_pg_pool = None

SQLITE_SCHEMA = """
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

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS baicai_roster (
    id SERIAL PRIMARY KEY,
    sort_order INTEGER NOT NULL,
    identity TEXT NOT NULL CHECK(identity IN ('player', 'captain')),
    serial TEXT,
    name TEXT NOT NULL,
    pool_letter TEXT NOT NULL CHECK(pool_letter IN ('A','B','C','D','E')),
    start_price INTEGER NOT NULL DEFAULT 0,
    buyout_price INTEGER,
    funds INTEGER,
    avatar TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_baicai_roster_sort ON baicai_roster(sort_order);

CREATE TABLE IF NOT EXISTS baicai_users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'captain')),
    captain_name TEXT,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_baicai_users_username ON baicai_users(username);
"""


def get_storage_backend() -> str:
    return "postgres" if DATABASE_URL else "sqlite"


def _roster_table() -> str:
    return "baicai_roster" if DATABASE_URL else "roster"


def _users_table() -> str:
    return "baicai_users" if DATABASE_URL else "users"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _adapt_sql(sql: str) -> str:
    return sql.replace("?", "%s") if DATABASE_URL else sql


def _init_pg_pool() -> None:
    global _pg_pool
    if _pg_pool is not None:
        return
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor

    sslmode = "require" if "localhost" not in DATABASE_URL else "prefer"
    _pg_pool = pool.SimpleConnectionPool(
        1,
        5,
        DATABASE_URL,
        cursor_factory=RealDictCursor,
        sslmode=sslmode,
    )


class _PgConnection:
    def __init__(self, raw) -> None:
        self._raw = raw
        self._last_cursor = None

    def execute(self, sql: str, params: tuple | list = ()):
        from psycopg2.extras import RealDictCursor

        cur = self._raw.cursor(cursor_factory=RealDictCursor)
        cur.execute(_adapt_sql(sql), params)
        self._last_cursor = cur
        return cur

    def executescript(self, sql: str) -> None:
        for stmt in (s.strip() for s in sql.split(";") if s.strip()):
            cur = self._raw.cursor()
            cur.execute(stmt)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()


def init_db() -> None:
    if DATABASE_URL:
        _init_pg_pool()
        with connect() as conn:
            conn.executescript(PG_SCHEMA)
    else:
        with connect() as conn:
            conn.executescript(SQLITE_SCHEMA)
    migrate_db()


def migrate_db() -> None:
    roster = _roster_table()
    with connect() as conn:
        if DATABASE_URL:
            row = conn.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = ? AND column_name = 'avatar'
                """,
                (roster,),
            ).fetchone()
            if not row:
                conn.execute(f"ALTER TABLE {roster} ADD COLUMN avatar TEXT")
        else:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(roster)").fetchall()}
            if "avatar" not in cols:
                conn.execute("ALTER TABLE roster ADD COLUMN avatar TEXT")


@contextmanager
def connect():
    if DATABASE_URL:
        assert _pg_pool is not None
        raw = _pg_pool.getconn()
        wrapper = _PgConnection(raw)
        try:
            yield wrapper
            wrapper.commit()
        except Exception:
            wrapper.rollback()
            raise
        finally:
            _pg_pool.putconn(raw)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def row_to_dict(row) -> dict[str, Any]:
    pool_letter = row["pool_letter"]
    position = POOL_LETTERS[pool_letter]
    keys = row.keys() if hasattr(row, "keys") else []
    created = row["created_at"]
    updated = row["updated_at"]
    if hasattr(created, "isoformat"):
        created = created.isoformat()
    if hasattr(updated, "isoformat"):
        updated = updated.isoformat()
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
        "avatar": row["avatar"] if "avatar" in keys else None,
        "createdAt": created,
        "updatedAt": updated,
    }


def list_roster() -> list[dict[str, Any]]:
    roster = _roster_table()
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM {roster} ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_entry(entry_id: int) -> dict[str, Any] | None:
    roster = _roster_table()
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM {roster} WHERE id = ?", (entry_id,)
        ).fetchone()
    return row_to_dict(row) if row else None


def next_sort_order(conn) -> int:
    roster = _roster_table()
    row = conn.execute(
        f"SELECT COALESCE(MAX(sort_order), 0) + 1 AS n FROM {roster}"
    ).fetchone()
    return int(row["n"])


def create_entry(data: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    roster = _roster_table()
    with connect() as conn:
        sort_order = data.get("sortOrder") or next_sort_order(conn)
        if DATABASE_URL:
            row = conn.execute(
                f"""
                INSERT INTO {roster}
                  (sort_order, identity, serial, name, pool_letter,
                   start_price, buyout_price, funds, avatar, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
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
            ).fetchone()
            entry_id = int(row["id"])
        else:
            cur = conn.execute(
                f"""
                INSERT INTO {roster}
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
            entry_id = int(cur.lastrowid)
    return get_entry(entry_id)  # type: ignore


def update_entry(entry_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_entry(entry_id)
    if not existing:
        return None
    merged = {**existing, **data, "id": entry_id}
    now = _now()
    roster = _roster_table()
    with connect() as conn:
        conn.execute(
            f"""
            UPDATE {roster} SET
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
    roster = _roster_table()
    with connect() as conn:
        cur = conn.execute(f"DELETE FROM {roster} WHERE id = ?", (entry_id,))
    return cur.rowcount > 0


def clear_roster() -> None:
    roster = _roster_table()
    with connect() as conn:
        conn.execute(f"DELETE FROM {roster}")


def count_roster() -> int:
    roster = _roster_table()
    with connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {roster}").fetchone()
    return int(row["c"])


def user_row_to_dict(row) -> dict[str, Any]:
    created = row["created_at"]
    if hasattr(created, "isoformat"):
        created = created.isoformat()
    return {
        "id": row["id"],
        "username": row["username"],
        "passwordHash": row["password_hash"],
        "role": row["role"],
        "captainName": row["captain_name"],
        "displayName": row["display_name"],
        "createdAt": created,
    }


def list_users() -> list[dict[str, Any]]:
    users = _users_table()
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM {users} ORDER BY id").fetchall()
    return [user_row_to_dict(r) for r in rows]


def get_user_by_username(username: str) -> dict[str, Any] | None:
    users = _users_table()
    with connect() as conn:
        row = conn.execute(
            f"SELECT * FROM {users} WHERE username = ?", (username,)
        ).fetchone()
    return user_row_to_dict(row) if row else None


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    users = _users_table()
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM {users} WHERE id = ?", (user_id,)).fetchone()
    return user_row_to_dict(row) if row else None


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    users = _users_table()
    with connect() as conn:
        if DATABASE_URL:
            row = conn.execute(
                f"""
                INSERT INTO {users}
                  (username, password_hash, role, captain_name, display_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    data["username"],
                    data["passwordHash"],
                    data["role"],
                    data.get("captainName"),
                    data.get("displayName") or data["username"],
                    now,
                ),
            ).fetchone()
            uid = int(row["id"])
        else:
            cur = conn.execute(
                f"""
                INSERT INTO {users}
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
            uid = int(cur.lastrowid)
    return get_user_by_id(uid)  # type: ignore


def count_users() -> int:
    users = _users_table()
    with connect() as conn:
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {users}").fetchone()
    return int(row["c"])


def clear_users() -> None:
    users = _users_table()
    with connect() as conn:
        conn.execute(f"DELETE FROM {users}")
