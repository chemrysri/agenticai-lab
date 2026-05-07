import uuid
from datetime import datetime

from db import get_connection


def save_message(thread_id, role, content):
    message_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_messages (
            message_id,
            thread_id,
            role,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            message_id,
            thread_id,
            role,
            content,
            now,
        ),
    )

    cursor.execute(
        """
        UPDATE chat_threads
        SET updated_at = ?
        WHERE thread_id = ?
        """,
        (
            now,
            thread_id,
        ),
    )

    cursor.execute(
        """
        UPDATE projects
        SET updated_at = ?
        WHERE project_id = (
            SELECT project_id
            FROM chat_threads
            WHERE thread_id = ?
        )
        """,
        (
            now,
            thread_id,
        ),
    )

    conn.commit()
    conn.close()

    return message_id


def load_messages(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM chat_messages
        WHERE thread_id = ?
        ORDER BY id ASC
        """,
        (thread_id,),
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


def clear_thread_messages(thread_id):
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM chat_messages
        WHERE thread_id = ?
        """,
        (thread_id,),
    )

    cursor.execute(
        """
        DELETE FROM thread_context
        WHERE thread_id = ?
        """,
        (thread_id,),
    )

    cursor.execute(
        """
        UPDATE chat_threads
        SET title = ?,
            updated_at = ?
        WHERE thread_id = ?
        """,
        (
            "New thread",
            now,
            thread_id,
        ),
    )

    conn.commit()
    conn.close()