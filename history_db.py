"""SQLite database for decode history."""
import os
import sqlite3
from datetime import datetime


class HistoryDB:
    """Manages the decode history SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Create a new connection with row_factory set."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create the history table if it doesn't exist."""
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    original_text TEXT NOT NULL,
                    neutrality_score INTEGER NOT NULL,
                    emotional_tone TEXT NOT NULL,
                    likely_intent TEXT NOT NULL,
                    full_response TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def save_decode(
        self,
        original_text: str,
        neutrality_score: int,
        emotional_tone: str,
        likely_intent: str,
        full_response: str,
    ):
        """Save a decode result to history."""
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO history
                   (original_text, neutrality_score, emotional_tone, likely_intent, full_response)
                   VALUES (?, ?, ?, ?, ?)""",
                (original_text, neutrality_score, emotional_tone, likely_intent, full_response),
            )
            conn.commit()
        finally:
            conn.close()

    def get_all(self) -> list[dict]:
        """Return all history entries, newest first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY timestamp DESC, id DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_by_id(self, row_id: int) -> dict | None:
        """Return a single history entry by ID."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM history WHERE id = ?", (row_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def search(self, query: str) -> list[dict]:
        """Search history by text content."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM history WHERE original_text LIKE ? ORDER BY timestamp DESC, id DESC",
                (f"%{query}%",),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def clear_all(self):
        """Delete all history entries."""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM history")
            conn.commit()
        finally:
            conn.close()
