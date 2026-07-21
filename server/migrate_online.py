"""Add is_online and last_seen columns to users table"""
from __future__ import annotations

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "auction.db")

def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_online INTEGER NOT NULL DEFAULT 0")
        print("Added is_online column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("is_online column already exists")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_seen TEXT")
        print("Added last_seen column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("last_seen column already exists")
        else:
            raise

    conn.commit()
    
    cursor.execute("SELECT * FROM users LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"Columns: {[d[0] for d in cursor.description]}")
        print(f"Sample row: {row}")

    conn.close()
    print("\nMigration completed successfully")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
