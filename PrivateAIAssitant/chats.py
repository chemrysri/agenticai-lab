import uuid
from datetime import datetime

from db import get_connection


def create_chat_session(user_id, title="New chat"):
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_sessions (
            chat_id,
            user_id,
            title,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            user_id,
            title,
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return chat_id


def get_latest_chat_session(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT chat_id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (user_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "chat_id": row[0],
        "title": row[1],
        "created_at": row[2],
        "updated_at": row[3],
    }


def get_user_chat_sessions(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT chat_id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "chat_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
        for row in rows
    ]


def save_message(user, session_id, chat_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chats (
            message_id,
            user_id,
            username,
            session_id,
            chat_id,
            role,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            user["user_id"],
            user["username"],
            session_id,
            chat_id,
            role,
            content,
            datetime.now().isoformat(),
        ),
    )

    cursor.execute(
        """
        UPDATE chat_sessions
        SET updated_at = ?
        WHERE chat_id = ?
          AND user_id = ?
        """,
        (
            datetime.now().isoformat(),
            chat_id,
            user["user_id"],
        ),
    )

    conn.commit()
    conn.close()


def load_messages(user_id, chat_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM chats
        WHERE user_id = ?
          AND chat_id = ?
        ORDER BY id ASC
        """,
        (
            user_id,
            chat_id,
        ),
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "role": role,
            "content": content,
        }
        for role, content in rows
    ]


def clear_chat_history(user_id, chat_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM chats
        WHERE user_id = ?
          AND chat_id = ?
        """,
        (
            user_id,
            chat_id,
        ),
    )

    cursor.execute(
        """
        UPDATE chat_sessions
        SET title = ?,
            updated_at = ?
        WHERE user_id = ?
          AND chat_id = ?
        """,
        (
            "New chat",
            datetime.now().isoformat(),
            user_id,
            chat_id,
        ),
    )

    conn.commit()
    conn.close()


def update_chat_title_if_needed(user_id, chat_id, first_user_message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title
        FROM chat_sessions
        WHERE user_id = ?
          AND chat_id = ?
        """,
        (
            user_id,
            chat_id,
        ),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    current_title = row[0]

    if current_title != "New chat":
        conn.close()
        return

    title = first_user_message.strip().replace("\n", " ")

    if len(title) > 40:
        title = title[:40] + "..."

    if not title:
        title = "New chat"

    cursor.execute(
        """
        UPDATE chat_sessions
        SET title = ?,
            updated_at = ?
        WHERE user_id = ?
          AND chat_id = ?
        """,
        (
            title,
            datetime.now().isoformat(),
            user_id,
            chat_id,
        ),
    )

    conn.commit()
    conn.close()