Private AI Assistant

This is a local AI chatbot project built using:
- Python
- Streamlit
- Ollama
- SQLite

Goal:
The goal of this project is to create a private AI assistant that runs locally on the user's computer.
The first version supports local chat with an open-source model and stores chat history in a local SQLite database.

Current Features:
- Local chatbot UI
- Ollama model integration
- SQLite chat history
- Clear chat history button
- Configurable model name
- Configurable assistant behavior/system prompt

Project Structure:

private-ai-assistant/
│
├── app.py
├── requirements.txt
├── assistant.db
└── README.txt

Setup Steps:

1. Install Ollama.

2. Pull a model:

   ollama pull llama3.2:3b

3. Create a Python virtual environment:

   python -m venv venv

4. Activate virtual environment:

   .\venv\Scripts\activate

5. Install dependencies:

   pip install -r requirements.txt

6. Run the app:

   streamlit run app.py

How It Works:

User message
    -> Streamlit UI
    -> Python app
    -> Ollama local API
    -> Local LLM
    -> Response shown in UI
    -> Chat saved in SQLite

Database:

The project uses SQLite.
A file named assistant.db is created automatically.

Table:
chats

Columns:
- id
- role
- content
- created_at

Future Roadmap:

v0.1:
- Basic local chatbot
- SQLite history

v0.2:
- Multiple chat sessions

Notes:
This app is private as long as it only talks to the local Ollama server.
External tools such as web search, email, or cloud hosting may involve external services later.