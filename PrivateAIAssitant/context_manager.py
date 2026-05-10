from datetime import datetime

from db import get_connection
from ollama_client import ask_ollama


def get_thread_context(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            summary,
            last_message_id,
            message_count_at_summary
        FROM thread_context
        WHERE thread_id = ?
        """,
        (thread_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "summary": "",
            "last_message_id": None,
            "message_count_at_summary": 0,
        }

    return {
        "summary": row[0],
        "last_message_id": row[1],
        "message_count_at_summary": row[2],
    }


def count_thread_messages(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM chat_messages
        WHERE thread_id = ?
        """,
        (thread_id,),
    )

    count = cursor.fetchone()[0]
    conn.close()

    return count


def get_latest_message_id(thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT message_id
        FROM chat_messages
        WHERE thread_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (thread_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return row[0]


def load_messages_after_message(thread_id, last_message_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if last_message_id is None:
        cursor.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE thread_id = ?
            ORDER BY id ASC
            """,
            (thread_id,),
        )
    else:
        cursor.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE thread_id = ?
              AND id > (
                  SELECT id
                  FROM chat_messages
                  WHERE message_id = ?
              )
            ORDER BY id ASC
            """,
            (
                thread_id,
                last_message_id,
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


def save_thread_context(
    thread_id,
    summary,
    last_message_id,
    message_count_at_summary,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO thread_context (
            thread_id,
            summary,
            last_message_id,
            message_count_at_summary,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(thread_id)
        DO UPDATE SET
            summary = excluded.summary,
            last_message_id = excluded.last_message_id,
            message_count_at_summary = excluded.message_count_at_summary,
            updated_at = excluded.updated_at
        """,
        (
            thread_id,
            summary,
            last_message_id,
            message_count_at_summary,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def should_compact_context(thread_id, context_compaction_n):
    context = get_thread_context(thread_id)
    current_message_count = count_thread_messages(thread_id)

    messages_since_last_compaction = (
        current_message_count - context["message_count_at_summary"]
    )

    return messages_since_last_compaction >= context_compaction_n


def compact_thread_context(thread_id, model):
    context = get_thread_context(thread_id)

    new_messages = load_messages_after_message(
        thread_id=thread_id,
        last_message_id=context["last_message_id"],
    )

    if not new_messages:
        return None

    conversation_text = ""

    for message in new_messages:
        conversation_text += (
            f"{message['role'].upper()}:\n"
            f"{message['content']}\n\n"
        )

    summary_messages = [
        {
            "role": "system",
            "content": (
                "You are the context manager for a private AI assistant. "
                "Your job is to compact conversation history into a concise, "
                "useful summary that can be used in future prompts. "
                "Preserve important decisions, user preferences, project details, "
                "technical choices, open questions, constraints, and next steps. "
                "Remove small talk and repeated details."
            ),
        },
        {
            "role": "user",
            "content": (
                "Existing context summary:\n"
                f"{context['summary'] or 'No existing summary yet.'}\n\n"
                "New messages to merge into the summary:\n"
                f"{conversation_text}\n\n"
                "Return the updated compact context summary."
            ),
        },
    ]

    updated_summary = ask_ollama(
        messages=summary_messages,
        model=model,
    )

    latest_message_id = get_latest_message_id(thread_id)
    current_message_count = count_thread_messages(thread_id)

    save_thread_context(
        thread_id=thread_id,
        summary=updated_summary,
        last_message_id=latest_message_id,
        message_count_at_summary=current_message_count,
    )

    return updated_summary


def maybe_compact_context(thread_id, model, context_compaction_n):
    if should_compact_context(
        thread_id=thread_id,
        context_compaction_n=context_compaction_n,
    ):
        return compact_thread_context(
            thread_id=thread_id,
            model=model,
        )

    return None


def build_messages_for_model(thread_id, system_prompt):
    context = get_thread_context(thread_id)

    messages_for_model = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    if context["summary"]:
        messages_for_model.append(
            {
                "role": "system",
                "content": (
                    "Useful compacted context from earlier in this thread:\n"
                    f"{context['summary']}"
                ),
            }
        )

    uncompacted_messages = load_messages_after_message(
        thread_id=thread_id,
        last_message_id=context["last_message_id"],
    )

    messages_for_model.extend(uncompacted_messages)

    return messages_for_model