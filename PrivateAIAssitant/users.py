import uuid
from datetime import datetime

from db import get_connection


def normalize_username(username):
    return username.strip().lower()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username
        FROM users
        ORDER BY username ASC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]


def get_or_create_user(username):
    username = normalize_username(username)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id, username
        FROM users
        WHERE username = ?
        """,
        (username,),
    )

    row = cursor.fetchone()

    if row:
        conn.close()

        return {
            "user_id": row[0],
            "username": row[1],
        }

    user_id = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT INTO users (
            user_id,
            username,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            username,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "username": username,
    }