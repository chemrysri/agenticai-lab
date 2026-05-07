import uuid
from datetime import datetime

from db import get_connection


def create_project(user_id, title="Default project", description=None):
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO projects (
            project_id,
            user_id,
            title,
            description,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            user_id,
            title,
            description,
            now,
            now,
        ),
    )

    conn.commit()
    conn.close()

    return project_id


def get_latest_project(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT project_id, title, description, created_at, updated_at
        FROM projects
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
        "project_id": row[0],
        "title": row[1],
        "description": row[2],
        "created_at": row[3],
        "updated_at": row[4],
    }


def get_user_projects(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT project_id, title, description, created_at, updated_at
        FROM projects
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (user_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "project_id": row[0],
            "title": row[1],
            "description": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]