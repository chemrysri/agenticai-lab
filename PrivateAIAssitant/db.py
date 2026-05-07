import sqlite3

from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)

    # Required for SQLite foreign key constraints to actually work.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


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
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_threads (
            thread_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (project_id)
                REFERENCES projects (project_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (thread_id)
                REFERENCES chat_threads (thread_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS thread_context (
            thread_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            last_message_id TEXT,
            message_count_at_summary INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (thread_id)
                REFERENCES chat_threads (thread_id)
                ON DELETE CASCADE,

            FOREIGN KEY (last_message_id)
                REFERENCES chat_messages (message_id)
                ON DELETE SET NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_projects_user
        ON projects (user_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_threads_project
        ON chat_threads (project_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_messages_thread
        ON chat_messages (thread_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_created
        ON chat_messages (thread_id, created_at)
        """
    )

    conn.commit()
    conn.close()


def reset_db():
    """
    Use this only when you intentionally want to destroy
    the local database schema and recreate it from scratch.

    Do not call this automatically from the Streamlit app on every rerun.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS thread_context")
    cursor.execute("DROP TABLE IF EXISTS chat_messages")
    cursor.execute("DROP TABLE IF EXISTS chat_threads")
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS users")

    conn.commit()
    conn.close()

    init_db()