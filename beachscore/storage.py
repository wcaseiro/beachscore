import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime


class SQLiteStore:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS courts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    court_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (court_id) REFERENCES courts(id)
                );

                CREATE TABLE IF NOT EXISTS timeline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    court_id TEXT NOT NULL,
                    match_id INTEGER,
                    action TEXT NOT NULL,
                    text TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (court_id) REFERENCES courts(id),
                    FOREIGN KEY (match_id) REFERENCES matches(id)
                );
                """
            )

    def ensure_court(self, court_id, name):
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO courts (id, name, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name
                """,
                (court_id, name, now),
            )

    def list_courts(self):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at FROM courts ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_match(self, court_id, name, state):
        now = utc_now()
        payload = json.dumps(state)
        with self.connect() as conn:
            conn.execute(
                "UPDATE matches SET active = 0 WHERE court_id = ?",
                (court_id,),
            )
            cur = conn.execute(
                """
                INSERT INTO matches
                    (court_id, name, active, state_json, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (court_id, name, payload, now, now),
            )
            return cur.lastrowid

    def save_match_state(self, match_id, state):
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE matches
                SET name = ?, state_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    state["match_name"],
                    json.dumps(state),
                    now,
                    match_id,
                ),
            )

    def active_match(self, court_id):
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, state_json
                FROM matches
                WHERE court_id = ? AND active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (court_id,),
            ).fetchone()

        if not row:
            return None

        state = json.loads(row["state_json"])
        state["match_id"] = row["id"]
        return state

    def list_matches(self, court_id=None):
        sql = """
            SELECT id, court_id, name, active, created_at, updated_at
            FROM matches
        """
        params = ()
        if court_id:
            sql += " WHERE court_id = ?"
            params = (court_id,)
        sql += " ORDER BY updated_at DESC"

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def append_event(self, court_id, match_id, action, text, state):
        now = utc_now()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO timeline_events
                    (court_id, match_id, action, text, state_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (court_id, match_id, action, text, json.dumps(state), now),
            )
            return cur.lastrowid

    def timeline(self, court_id, limit=100):
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, court_id, match_id, action, text, created_at
                FROM timeline_events
                WHERE court_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (court_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def event_snapshot(self, event_id):
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, court_id, match_id, action, text, state_json, created_at
                FROM timeline_events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()

        if not row:
            return None

        data = dict(row)
        data["state"] = json.loads(data.pop("state_json"))
        return data


def utc_now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
