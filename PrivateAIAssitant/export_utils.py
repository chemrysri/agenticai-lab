from datetime import datetime

from db import get_connection


def make_safe_filename(value):
    safe = value.strip().lower()

    for char in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
        safe = safe.replace(char, "-")

    while "--" in safe:
        safe = safe.replace("--", "-")

    return safe.strip("-") or "chat-export"


def export_thread_as_markdown(user, project_id, thread_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title
        FROM projects
        WHERE project_id = ?
        """,
        (project_id,),
    )
    project_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT title, system_prompt, context_compaction_n, created_at, updated_at
        FROM chat_threads
        WHERE thread_id = ?
        """,
        (thread_id,),
    )
    thread_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT summary, updated_at
        FROM thread_context
        WHERE thread_id = ?
        """,
        (thread_id,),
    )
    context_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT role, content, created_at
        FROM chat_messages
        WHERE thread_id = ?
        ORDER BY id ASC
        """,
        (thread_id,),
    )
    message_rows = cursor.fetchall()

    conn.close()

    project_title = project_row[0] if project_row else "Unknown project"

    if thread_row:
        thread_title = thread_row[0]
        system_prompt = thread_row[1]
        context_compaction_n = thread_row[2]
        thread_created_at = thread_row[3]
        thread_updated_at = thread_row[4]
    else:
        thread_title = "Unknown thread"
        system_prompt = ""
        context_compaction_n = ""
        thread_created_at = ""
        thread_updated_at = ""

    lines = []

    lines.append(f"# {thread_title}")
    lines.append("")
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- User: `{user['username']}`")
    lines.append(f"- User ID: `{user['user_id']}`")
    lines.append(f"- Project: `{project_title}`")
    lines.append(f"- Project ID: `{project_id}`")
    lines.append(f"- Thread ID: `{thread_id}`")
    lines.append(f"- Thread created at: `{thread_created_at}`")
    lines.append(f"- Thread updated at: `{thread_updated_at}`")
    lines.append(f"- Exported at: `{datetime.now().isoformat()}`")
    lines.append(f"- Context compaction N: `{context_compaction_n}`")
    lines.append("")

    if system_prompt:
        lines.append("## Thread System Instructions")
        lines.append("")
        lines.append(system_prompt)
        lines.append("")

    if context_row:
        lines.append("## Compacted Context Summary")
        lines.append("")
        lines.append(f"_Last updated: `{context_row[1]}`_")
        lines.append("")
        lines.append(context_row[0])
        lines.append("")

    lines.append("## Messages")
    lines.append("")

    if not message_rows:
        lines.append("_No messages in this thread._")
        lines.append("")
    else:
        for role, content, created_at in message_rows:
            display_role = "User" if role == "user" else "Assistant"

            lines.append(f"### {display_role}")
            lines.append("")
            lines.append(f"_Created at: `{created_at}`_")
            lines.append("")
            lines.append(content)
            lines.append("")

    markdown = "\n".join(lines)

    filename = make_safe_filename(thread_title) + ".md"

    return markdown, filename