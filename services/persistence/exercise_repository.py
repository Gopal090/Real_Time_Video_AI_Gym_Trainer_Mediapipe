import sqlite3
from pathlib import Path

_DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


def _get_conn():
    conn = sqlite3.connect(_DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                sets INTEGER NOT NULL DEFAULT 0,
                reps INTEGER NOT NULL DEFAULT 0,
                time INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_user(username):
    clean_name = username.strip() if username else ""
    if not clean_name:
        return None
    with _get_conn() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE username = ? COLLATE NOCASE", (clean_name,)).fetchone()
        if row:
            return {"id": row["id"], "username": row["username"]}
    return None


def create_user(username):
    clean_name = username.strip()
    with _get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (clean_name,))
    return get_user(clean_name)


def get_or_create_user(username):
    clean_name = username.strip() if username else ""
    user = get_user(clean_name)
    if user is None:
        user = create_user(clean_name)
    return user


def add_exercise(user_id, exercise_name, sets, reps, time):
    if not user_id:
        return
    with _get_conn() as conn:
        existing = conn.execute("""
            SELECT id FROM exercises
            WHERE user_id = ? AND exercise_name = ? AND date(created_at) = date('now')
        """, (user_id, exercise_name)).fetchone()

        if existing:
            conn.execute("""
                UPDATE exercises
                SET reps = reps + ?, sets = sets + ?, time = time + ?
                WHERE id = ?
            """, (reps, sets, time, existing['id']))
        else:
            conn.execute("""
                INSERT INTO exercises (user_id, exercise_name, sets, reps, time)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, exercise_name, sets, reps, time))


def get_user_exercises(user_id):
    if not user_id:
        return []
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT exercise_name, sets, reps, time, created_at FROM exercises  
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]

