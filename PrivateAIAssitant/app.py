import uuid

import streamlit as st

from assets import get_thread_assets, save_thread_asset
from config import DEFAULT_MODEL
from context_manager import build_messages_for_model, maybe_compact_context
from db import init_db
from export_utils import export_thread_as_markdown
from media_store import save_uploaded_file
from messages import clear_thread_messages, load_messages, save_message
from ollama_client import ask_ollama
from pdf_processor import extract_pdf_text, summarize_pdf_for_thread
from projects import create_project, get_latest_project, get_user_projects
from threads import (
    create_thread,
    delete_thread,
    get_latest_thread,
    get_project_threads,
    get_thread,
    rename_thread,
    update_thread_settings,
    update_thread_title_if_needed,
)
from users import get_all_users, get_or_create_user


def initialize_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None

    if "project_id" not in st.session_state:
        st.session_state.project_id = None

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    if "known_user_select" not in st.session_state:
        st.session_state.known_user_select = ""

    if "new_username_input" not in st.session_state:
        st.session_state.new_username_input = ""


def show_user_selection():
    known_users = get_all_users()

    st.subheader("Choose user")

    selected_user = ""

    user_options = [""] + known_users

    if st.session_state.known_user_select not in user_options:
        st.session_state.known_user_select = ""

    if known_users:
        selected_user = st.selectbox(
            "Known users",
            options=user_options,
            key="known_user_select",
        )

    new_username = st.text_input(
        "Or enter a new username",
        key="new_username_input",
    )

    if st.button("Continue", key="continue_user_selection"):
        username_to_use = new_username.strip() or selected_user

        if not username_to_use:
            st.warning("Please select or enter a username.")
            return

        user = get_or_create_user(username_to_use)

        latest_project = get_latest_project(user["user_id"])

        if latest_project:
            project_id = latest_project["project_id"]
        else:
            project_id = create_project(
                user_id=user["user_id"],
                title="Default project",
            )

        latest_thread = get_latest_thread(project_id)

        if latest_thread:
            thread_id = latest_thread["thread_id"]
        else:
            thread_id = create_thread(
                project_id=project_id,
                title="New thread",
            )

        st.session_state.user = user
        st.session_state.project_id = project_id
        st.session_state.thread_id = thread_id

        st.rerun()


def ensure_current_project_and_thread_exist(user):
    if not st.session_state.project_id:
        latest_project = get_latest_project(user["user_id"])

        if latest_project:
            st.session_state.project_id = latest_project["project_id"]
        else:
            st.session_state.project_id = create_project(
                user_id=user["user_id"],
                title="Default project",
            )

    if not st.session_state.thread_id:
        latest_thread = get_latest_thread(st.session_state.project_id)

        if latest_thread:
            st.session_state.thread_id = latest_thread["thread_id"]
        else:
            st.session_state.thread_id = create_thread(
                project_id=st.session_state.project_id,
                title="New thread",
            )


def delete_current_thread_and_select_next():
    deleted_project_id = delete_thread(st.session_state.thread_id)

    if not deleted_project_id:
        st.session_state.thread_id = None
        return

    remaining_threads = get_project_threads(deleted_project_id)

    if remaining_threads:
        st.session_state.thread_id = remaining_threads[0]["thread_id"]
    else:
        st.session_state.thread_id = create_thread(
            project_id=deleted_project_id,
            title="New thread",
        )


def show_pdf_upload_section(user, model):
    st.subheader("PDF input")

    uploaded_pdfs = st.file_uploader(
        "Upload PDF(s) to current chat",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.thread_id}",
    )

    if not uploaded_pdfs:
        assets = get_thread_assets(st.session_state.thread_id)

        if assets:
            with st.expander("PDFs in this chat"):
                for asset in assets:
                    st.markdown(f"**{asset['file_name']}**")
                    st.caption(f"Uploaded at: {asset['created_at']}")

                    if asset["extracted_summary"]:
                        st.markdown(asset["extracted_summary"])

                    st.divider()

        return

    st.caption(f"{len(uploaded_pdfs)} PDF(s) selected.")

    if st.button(
        "Process selected PDF(s)",
        key=f"process_pdfs_{st.session_state.thread_id}",
    ):
        processed_count = 0
        failed_files = []

        for uploaded_pdf in uploaded_pdfs:
            asset_id = str(uuid.uuid4())

            try:
                with st.spinner(f"Saving and reading {uploaded_pdf.name}..."):
                    storage_path = save_uploaded_file(
                        uploaded_file=uploaded_pdf,
                        thread_id=st.session_state.thread_id,
                        asset_id=asset_id,
                    )

                    extracted_text = extract_pdf_text(storage_path)

                with st.spinner(f"Summarizing {uploaded_pdf.name} locally..."):
                    extracted_summary = summarize_pdf_for_thread(
                        file_name=uploaded_pdf.name,
                        extracted_text=extracted_text,
                        model=model,
                    )

                save_thread_asset(
                    asset_id=asset_id,
                    thread_id=st.session_state.thread_id,
                    file_name=uploaded_pdf.name,
                    file_type="pdf",
                    mime_type=uploaded_pdf.type,
                    storage_path=storage_path,
                    extracted_text=extracted_text,
                    extracted_summary=extracted_summary,
                )

                save_message(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=(
                        f"Uploaded PDF: **{uploaded_pdf.name}**\n\n"
                        "The PDF was extracted, summarized, and saved as context "
                        "for this thread."
                    ),
                )

                processed_count += 1

            except Exception as error:
                failed_files.append(
                    {
                        "file_name": uploaded_pdf.name,
                        "error": str(error),
                    }
                )

        if processed_count:
            st.success(f"Processed {processed_count} PDF(s).")

        if failed_files:
            st.error("Some PDFs failed to process.")

            for failed_file in failed_files:
                st.write(f"**{failed_file['file_name']}**")
                st.code(failed_file["error"])

        st.rerun()

    assets = get_thread_assets(st.session_state.thread_id)

    if assets:
        with st.expander("PDFs in this chat"):
            for asset in assets:
                st.markdown(f"**{asset['file_name']}**")
                st.caption(f"Uploaded at: {asset['created_at']}")

                if asset["extracted_summary"]:
                    st.markdown(asset["extracted_summary"])

                st.divider()


def show_sidebar(user):
    with st.sidebar:
        st.header("Settings")

        st.subheader("Current user")
        st.write(user["username"])

        st.subheader("Known users")
        for username in get_all_users():
            st.write(f"- {username}")

        st.divider()

        st.subheader("Projects")

        projects = get_user_projects(user["user_id"])

        if projects:
            project_id_to_label = {
                project["project_id"]: project["title"]
                for project in projects
            }

            project_ids = [
                project["project_id"]
                for project in projects
            ]

            if st.session_state.project_id not in project_ids:
                st.session_state.project_id = project_ids[0]

            selected_project_id = st.selectbox(
                "Your projects",
                options=project_ids,
                format_func=lambda project_id: project_id_to_label.get(
                    project_id,
                    "Untitled project",
                ),
                index=project_ids.index(st.session_state.project_id),
            )

            if selected_project_id != st.session_state.project_id:
                st.session_state.project_id = selected_project_id

                latest_thread = get_latest_thread(selected_project_id)

                if latest_thread:
                    st.session_state.thread_id = latest_thread["thread_id"]
                else:
                    st.session_state.thread_id = create_thread(
                        project_id=selected_project_id,
                        title="New thread",
                    )

                st.rerun()

        new_project_title = st.text_input(
            "New project name",
            placeholder="Example: Private AI Assistant",
        )

        if st.button("Create project"):
            title = new_project_title.strip() or "Untitled project"

            project_id = create_project(
                user_id=user["user_id"],
                title=title,
            )

            thread_id = create_thread(
                project_id=project_id,
                title="New thread",
            )

            st.session_state.project_id = project_id
            st.session_state.thread_id = thread_id

            st.rerun()

        st.divider()

        st.subheader("Chats / Threads")

        threads = get_project_threads(st.session_state.project_id)

        if threads:
            thread_id_to_label = {
                thread["thread_id"]: thread["title"]
                for thread in threads
            }

            thread_ids = [
                thread["thread_id"]
                for thread in threads
            ]

            if st.session_state.thread_id not in thread_ids:
                st.session_state.thread_id = thread_ids[0]

            selected_thread_id = st.selectbox(
                "Project chats",
                options=thread_ids,
                format_func=lambda thread_id: thread_id_to_label.get(
                    thread_id,
                    "Untitled chat",
                ),
                index=thread_ids.index(st.session_state.thread_id),
            )

            if selected_thread_id != st.session_state.thread_id:
                st.session_state.thread_id = selected_thread_id
                st.rerun()

        if st.button("New chat"):
            st.session_state.thread_id = create_thread(
                project_id=st.session_state.project_id,
                title="New thread",
            )
            st.rerun()

        current_thread = get_thread(st.session_state.thread_id)

        if current_thread:
            st.divider()
            st.subheader("Chat actions")

            new_thread_title = st.text_input(
                "Rename current chat",
                value=current_thread["title"],
                key=f"rename_thread_{st.session_state.thread_id}",
            )

            if st.button("Save chat name"):
                rename_thread(
                    thread_id=st.session_state.thread_id,
                    new_title=new_thread_title,
                )
                st.success("Chat renamed.")
                st.rerun()

            markdown_data, markdown_filename = export_thread_as_markdown(
                user=user,
                project_id=st.session_state.project_id,
                thread_id=st.session_state.thread_id,
            )

            st.download_button(
                label="Export current chat as Markdown",
                data=markdown_data,
                file_name=markdown_filename,
                mime="text/markdown",
            )

            if st.button("Clear current chat history"):
                clear_thread_messages(
                    thread_id=st.session_state.thread_id,
                )
                st.rerun()

            with st.expander("Delete current chat"):
                st.warning(
                    "This permanently deletes the current chat, including "
                    "its messages, compacted context, and uploaded assets."
                )

                confirm_delete = st.checkbox(
                    "I understand. Delete this chat.",
                    key=f"confirm_delete_{st.session_state.thread_id}",
                )

                if st.button("Delete chat", disabled=not confirm_delete):
                    delete_current_thread_and_select_next()
                    st.rerun()

        st.divider()

        if st.button("Switch user"):
            st.session_state.user = None
            st.session_state.project_id = None
            st.session_state.thread_id = None
            st.rerun()

        st.subheader("Current IDs")
        st.caption(f"User ID: {user['user_id']}")
        st.caption(f"Project ID: {st.session_state.project_id}")
        st.caption(f"Thread ID: {st.session_state.thread_id}")

        st.divider()

        model = st.text_input(
            "Ollama model",
            value=DEFAULT_MODEL,
            help="Example: llama3.2:3b, gemma3:4b, qwen3:4b",
        )

        st.divider()

        show_pdf_upload_section(
            user=user,
            model=model,
        )

        st.divider()

        current_thread = get_thread(st.session_state.thread_id)

        st.subheader("Thread settings")

        system_prompt = st.text_area(
            "Thread system instructions",
            value=current_thread["system_prompt"],
            height=120,
            key=f"system_prompt_{st.session_state.thread_id}",
        )

        context_compaction_n = st.number_input(
            "Compact context every N messages",
            min_value=2,
            max_value=100,
            value=int(current_thread["context_compaction_n"]),
            step=1,
            help=(
                "Counts total messages, meaning user + assistant messages. "
                "For example, 10 means roughly every 5 back-and-forth turns."
            ),
            key=f"context_compaction_n_{st.session_state.thread_id}",
        )

        if st.button("Save thread settings"):
            update_thread_settings(
                thread_id=st.session_state.thread_id,
                system_prompt=system_prompt,
                context_compaction_n=int(context_compaction_n),
            )
            st.success("Thread settings saved.")

    return model, system_prompt, int(context_compaction_n)


def show_chat(user, model, system_prompt, context_compaction_n):
    stored_messages = load_messages(
        thread_id=st.session_state.thread_id,
    )

    for message in stored_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask something...")

    if not user_input:
        return

    save_message(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input,
    )

    update_thread_title_if_needed(
        thread_id=st.session_state.thread_id,
        first_user_message=user_input,
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    messages_for_model = build_messages_for_model(
        thread_id=st.session_state.thread_id,
        system_prompt=system_prompt,
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking locally..."):
            assistant_reply = ask_ollama(
                messages=messages_for_model,
                model=model,
            )

            st.markdown(assistant_reply)

    save_message(
        thread_id=st.session_state.thread_id,
        role="assistant",
        content=assistant_reply,
    )

    with st.spinner("Updating compact thread context if needed..."):
        maybe_compact_context(
            thread_id=st.session_state.thread_id,
            model=model,
            context_compaction_n=context_compaction_n,
        )


def main():
    st.set_page_config(
        page_title="Private AI Assistant",
        page_icon="🤖",
        layout="centered",
    )

    init_db()
    initialize_session_state()

    st.title("🤖 Private AI Assistant")
    st.caption("Local chatbot powered by Ollama + Streamlit + SQLite")

    if st.session_state.user is None:
        show_user_selection()
        st.stop()

    user = st.session_state.user

    ensure_current_project_and_thread_exist(user)

    model, system_prompt, context_compaction_n = show_sidebar(user)

    show_chat(
        user=user,
        model=model,
        system_prompt=system_prompt,
        context_compaction_n=context_compaction_n,
    )


if __name__ == "__main__":
    main()