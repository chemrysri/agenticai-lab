import uuid
from datetime import datetime

from db import get_connection


def create_thread(project_id, title="New thread"):
    thread_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_threads (
            thread_id,
            project_id,
            title,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            thread_id,
            project_id,
            title,
            now,
            now,
        ),
    )

    cursor.execute(
        """
        UPDATE projects
        SET updated_at = ?
        WHERE project_id = ?
        """,
        (
            now,
            project_id,
        ),
    )

    conn.commit()
    conn.close()

    return thread_id


def get_latest_thread(project_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT thread_id, title, created_at, updated_at
        FROM chat_threads
        WHERE project_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (project_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "thread_id": row[0],
        "title": row[1],
        "created_at": row[2],
        "updated_at": row[3],
    }


def get_project_threads(project_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT thread_id, title, created_at, updated_at
        FROM chat_threads
        WHERE project_id = ?
        ORDER BY updated_at DESC
        """,
        (project_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "thread_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }
        for row in rows
    ]


def update_thread_title_if_needed(thread_id, first_user_message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title
        FROM chat_threads
        WHERE thread_id = ?
        """,
        (thread_id,),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    current_title = row[0]

    if current_title != "New thread":
        conn.close()
        return

    title = first_user_message.strip().replace("\n", " ")

    if len(title) > 40:
        title = title[:40] + "..."

    if not title:
        title = "New thread"

    now = datetime.now().isoformat()

    cursor.execute(
        """
        UPDATE chat_threads
        SET title = ?,
            updated_at = ?
        WHERE thread_id = ?
        """,
        (
            title,
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