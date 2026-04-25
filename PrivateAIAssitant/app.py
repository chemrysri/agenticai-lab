import sqlite3
from datetime import datetime
import requests
import streamlit as st

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2:3b"
DB_PATH = "assistant.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_message(role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chats (role, content, created_at)
        VALUES (?, ?, ?)
        """,
        (role, content, datetime.now().isoformat()),
    )

    conn.commit()
    conn.close()


def load_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT role, content FROM chats ORDER BY id ASC")
    rows = cursor.fetchall()

    conn.close()

    return [{"role": role, "content": content} for role, content in rows]


def clear_chat_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chats")

    conn.commit()
    conn.close()


def ask_ollama(messages, model):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    except requests.exceptions.ConnectionError:
        return (
            "I could not connect to Ollama. "
            "Please make sure Ollama is installed and running."
        )

    except requests.exceptions.Timeout:
        return "The model took too long to respond. Try a smaller model."

    except Exception as error:
        return f"Something went wrong: {error}"


def main():
    st.set_page_config(
        page_title="Private AI Assistant",
        page_icon="🤖",
        layout="centered",
    )

    init_db()

    st.title("🤖 Private AI Assistant")
    st.caption("Local chatbot powered by Ollama + Streamlit + SQLite")

    with st.sidebar:
        st.header("Settings")

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

        if st.button("Clear chat history"):
            clear_chat_history()
            st.rerun()

    stored_messages = load_messages()

    for message in stored_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        save_message("user", user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        messages_for_model = [{"role": "system", "content": system_prompt}]
        messages_for_model.extend(load_messages())

        with st.chat_message("assistant"):
            with st.spinner("Thinking locally..."):
                assistant_reply = ask_ollama(messages_for_model, model)
                st.markdown(assistant_reply)

        save_message("assistant", assistant_reply)


if __name__ == "__main__":
    main()