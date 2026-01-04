import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    alias TEXT,
    state TEXT,
    partner_id INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS skips (
    skipper_id INTEGER,
    skipped_id INTEGER,
    expires_at INTEGER
)
""")

conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def create_user(user_id):
    cur.execute(
        "INSERT OR IGNORE INTO users VALUES (?, NULL, 'NEW', NULL)",
        (user_id,)
    )
    conn.commit()

def set_alias(user_id, alias):
    cur.execute(
        "UPDATE users SET alias=?, state='IDLE' WHERE user_id=?",
        (alias, user_id)
    )
    conn.commit()

def set_state(user_id, state, partner_id=None):
    cur.execute(
        "UPDATE users SET state=?, partner_id=? WHERE user_id=?",
        (state, partner_id, user_id)
    )
    conn.commit()

def add_skip(x, y):
    expires = int(time.time()) + 86400
    cur.execute(
        "INSERT INTO skips VALUES (?, ?, ?)",
        (x, y, expires)
    )
    conn.commit()

def is_blocked(a, b):
    now = int(time.time())
    cur.execute("""
    SELECT 1 FROM skips
    WHERE ((skipper_id=? AND skipped_id=?)
        OR (skipper_id=? AND skipped_id=?))
      AND expires_at > ?
    """, (a, b, b, a, now))
    return cur.fetchone() is not None

def find_match(user_id):
    cur.execute("""
    SELECT user_id FROM users
    WHERE state='WAITING' AND user_id!=?
    """, (user_id,))
    candidates = [r[0] for r in cur.fetchall()]
    for c in candidates:
        if not is_blocked(user_id, c):
            return c
    return None

