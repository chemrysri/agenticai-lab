import uuid

import streamlit as st

from chats import (
    clear_chat_history,
    create_chat_session,
    get_latest_chat_session,
    get_user_chat_sessions,
    load_messages,
    save_message,
    update_chat_title_if_needed,
)
from config import DEFAULT_MODEL
from db import init_db
from ollama_client import ask_ollama
from users import get_all_users, get_or_create_user


def initialize_session_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "user" not in st.session_state:
        st.session_state.user = None

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None


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

        latest_chat = get_latest_chat_session(user["user_id"])

        if latest_chat:
            chat_id = latest_chat["chat_id"]
        else:
            chat_id = create_chat_session(user["user_id"])

        st.session_state.user = user
        st.session_state.chat_id = chat_id

        st.rerun()


def ensure_current_chat_exists(user):
    if st.session_state.chat_id:
        return

    latest_chat = get_latest_chat_session(user["user_id"])

    if latest_chat:
        st.session_state.chat_id = latest_chat["chat_id"]
    else:
        st.session_state.chat_id = create_chat_session(user["user_id"])


def show_sidebar(user):
    with st.sidebar:
        st.header("Settings")

        st.subheader("Current user")
        st.write(user["username"])

        st.subheader("Known users")

        for username in get_all_users():
            st.write(f"- {username}")

        st.subheader("Chats")

        chat_sessions = get_user_chat_sessions(user["user_id"])

        if chat_sessions:
            chat_id_to_label = {
                chat["chat_id"]: chat["title"]
                for chat in chat_sessions
            }

            chat_ids = [chat["chat_id"] for chat in chat_sessions]

            if st.session_state.chat_id not in chat_ids:
                st.session_state.chat_id = chat_ids[0]

            selected_chat_id = st.selectbox(
                "Your chats",
                options=chat_ids,
                format_func=lambda chat_id: chat_id_to_label.get(
                    chat_id,
                    "Untitled chat",
                ),
                index=chat_ids.index(st.session_state.chat_id),
            )

            if selected_chat_id != st.session_state.chat_id:
                st.session_state.chat_id = selected_chat_id
                st.rerun()

        if st.button("New chat"):
            st.session_state.chat_id = create_chat_session(user["user_id"])
            st.rerun()

        if st.button("Clear current chat history"):
            clear_chat_history(
                user_id=user["user_id"],
                chat_id=st.session_state.chat_id,
            )
            st.rerun()

        if st.button("Switch user"):
            st.session_state.user = None
            st.session_state.chat_id = None
            st.rerun()

        st.subheader("Current IDs")
        st.caption(f"User ID: {user['user_id']}")
        st.caption(f"Session ID: {st.session_state.session_id}")
        st.caption(f"Chat ID: {st.session_state.chat_id}")

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
        user_id=user["user_id"],
        chat_id=st.session_state.chat_id,
    )

    for message in stored_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask something...")

    if not user_input:
        return

    save_message(
        user=user,
        session_id=st.session_state.session_id,
        chat_id=st.session_state.chat_id,
        role="user",
        content=user_input,
    )

    update_chat_title_if_needed(
        user_id=user["user_id"],
        chat_id=st.session_state.chat_id,
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
            user_id=user["user_id"],
            chat_id=st.session_state.chat_id,
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
        user=user,
        session_id=st.session_state.session_id,
        chat_id=st.session_state.chat_id,
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

    ensure_current_chat_exists(user)

    model, system_prompt = show_sidebar(user)

    show_chat(
        user=user,
        model=model,
        system_prompt=system_prompt,
    )


if __name__ == "__main__":
    main()