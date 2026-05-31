from datetime import datetime

from db import get_connection


def save_thread_asset(
    asset_id,
    thread_id,
    file_name,
    file_type,
    mime_type,
    storage_path,
    extracted_text,
    extracted_summary,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO thread_assets (
            asset_id,
            thread_id,
            file_name,
            file_type,
            mime_type,
            storage_path,
            extracted_text,
            extracted_summary,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            asset_id,
            thread_id,
            file_name,
            file_type,
            mime_type,
            storage_path,
            extracted_text,
            extracted_summary,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def get_thread_assets(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            asset_id,
            file_name,
            file_type,
            mime_type,
            storage_path,
            extracted_summary,
            created_at
        FROM thread_assets
        WHERE thread_id = ?
        ORDER BY created_at DESC
        """,
        (thread_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "asset_id": row[0],
            "file_name": row[1],
            "file_type": row[2],
            "mime_type": row[3],
            "storage_path": row[4],
            "extracted_summary": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


def get_thread_asset_summaries(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT file_name, file_type, extracted_summary
        FROM thread_assets
        WHERE thread_id = ?
          AND extracted_summary IS NOT NULL
          AND TRIM(extracted_summary) != ''
        ORDER BY created_at ASC
        """,
        (thread_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "file_name": row[0],
            "file_type": row[1],
            "extracted_summary": row[2],
        }
        for row in rows
    ]