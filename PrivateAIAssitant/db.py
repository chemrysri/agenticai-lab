import sqlite3
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            user_id TEXT,
            username TEXT,
            session_id TEXT,
            chat_id TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Migration support for older assistant.db files
    cursor.execute("PRAGMA table_info(chats)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    required_columns = {
        "message_id": "TEXT",
        "user_id": "TEXT",
        "username": "TEXT",
        "session_id": "TEXT",
        "chat_id": "TEXT",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE chats ADD COLUMN {column_name} {column_type}"
            )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chats_user_chat
        ON chats (user_id, chat_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
        ON chat_sessions (user_id)
        """
    )

    conn.commit()
    conn.close()