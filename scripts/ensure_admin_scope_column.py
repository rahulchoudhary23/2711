"""Ensure the user table has the admin_scope column before running the app."""
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "instance" / "events.db"

if not DB_PATH.exists():
    raise SystemExit(f"Database file not found at {DB_PATH}. Run the app once to create it.")

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]
    if "admin_scope" not in columns:
        cursor.execute("ALTER TABLE user ADD COLUMN admin_scope TEXT DEFAULT 'super'")
        conn.commit()
        print("Added admin_scope column to user table.")
    else:
        print("admin_scope column already present. No changes made.")
