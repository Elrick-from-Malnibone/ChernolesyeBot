import sqlite3

DB_PATH = "game.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            health INTEGER,
            damage INTEGER,
            current_section INTEGER
        )
    """)
    conn.commit()
    conn.close()

def create_player(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO players (user_id, health, damage, current_section) VALUES (?, 20, 5, 1)", (user_id,))
    conn.commit()
    conn.close()