import streamlit as st

from config import DEFAULT_MODEL
from db import init_db
from messages import clear_thread_messages, load_messages, save_message
from ollama_client import ask_ollama
from projects import create_project, get_latest_project, get_user_projects
from threads import (
    create_thread,
    get_latest_thread,
    get_project_threads,
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


def show_user_selection():
    known_users = get_all_users()

    st.subheader("Choose user")

    selected_user = ""

    if known_users:
        selected_user = st.selectbox(
            "Known users",
            options=[""] + known_users,
        )

    new_username = st.text_input("Or enter a new username")

    if st.button("Continue"):
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

        st.subheader("Threads")

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
                "Project threads",
                options=thread_ids,
                format_func=lambda thread_id: thread_id_to_label.get(
                    thread_id,
                    "Untitled thread",
                ),
                index=thread_ids.index(st.session_state.thread_id),
            )

            if selected_thread_id != st.session_state.thread_id:
                st.session_state.thread_id = selected_thread_id
                st.rerun()

        if st.button("New thread"):
            st.session_state.thread_id = create_thread(
                project_id=st.session_state.project_id,
                title="New thread",
            )
            st.rerun()

        if st.button("Clear current thread history"):
            clear_thread_messages(
                thread_id=st.session_state.thread_id,
            )
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

        system_prompt = st.text_area(
            "Assistant behavior",
            value=(
                "You are a helpful private AI assistant. "
                "Give clear, practical, beginner-friendly answers."
            ),
            height=120,
        )

    return model, system_prompt


def show_chat(user, model, system_prompt):
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

    messages_for_model = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    messages_for_model.extend(
        load_messages(
            thread_id=st.session_state.thread_id,
        )
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

    model, system_prompt = show_sidebar(user)

    show_chat(
        user=user,
        model=model,
        system_prompt=system_prompt,
    )


if __name__ == "__main__":
    main()