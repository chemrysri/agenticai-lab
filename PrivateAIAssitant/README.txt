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
├── config.py
├── db.py
├── users.py
├── chats.py
├── ollama_client.py
└── requirements.txt

Setup Steps:

1. Install Ollama.

2. Pull a model:

   ollama pull llama3.2:3b

3. Ollama runs by default and exposes api as - http://localhost:11434/

4. Create a Python virtual environment:

   python -m venv venv

5. Activate virtual environment:

   .\venv\Scripts\activate

6. Install dependencies:

   pip install -r requirements.txt

7. Run the app:

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

0.2.2
- Multi projects, chat thread support
- Context compaction at every N messages per thread (Default N = 10)

0.2.3
- Rename chats
- Delete individual chats
- Export chat as Markdown

0.2.4
- Support for PDF inputs

1.0.0
- Extend ability to search internet for updated info using mcp tools

1.1.0
- Generate conceptual search queries locally with Ollama
- Search once per query through MCP and SearXNG
- Deduplicate and rank results before adding evidence to the model prompt

1.1.1
- Add follow-up query rewriting using recent conversation context
- Add evidence-quality notes for ranked search results
- Move fresh web evidence into the final user task so small local models are less likely to ignore it
- Add deterministic extracted-fact notes for visible snippets where possible
- Set Ollama generation temperature to 0 for more stable query planning and answer synthesis
- Document known caveats around local model grounding and SearXNG snippet quality

Known Factors Affecting Search Results:

Model-related caveats:
- Small local models such as llama3.2:3b may ignore retrieved evidence and fall back to training-data disclaimers.
- The model may over-infer from snippets, page titles, or URLs when the actual requested fact is not visible.
- The model may struggle with dense or conflicting evidence unless the answer is extracted or structured before synthesis.
- Prompting helps, but it is not a complete substitute for better retrieval, page extraction, and stronger synthesis models.

SearXNG/tool-related caveats:
- SearXNG usually returns snippets, not full page content.
- Snippets can be incomplete, stale, or ambiguous.
- Search results may mix official pages, mirrors, speculative pages, and outdated URLs.
- A result title can mention the requested year or topic while the URL/content points to a different or partial context.
- Current ranking improves relevance but does not fully prove factual completeness.

Latest trial notes:
- Conceptual query generation improved search coverage but can drift without conversation-aware query rewriting.
- Follow-up rewriting fixed cases where short questions like "who is the title winner" lost prior context.
- Grounding the final user message reduced generic knowledge-cutoff disclaimers.
- The model still needs better evidence extraction because snippets alone are often not enough for reliable final answers.

UpNext:

1. Add Ollama model discovery and model dropdown instead of typing model names manually
2. Add separate model settings for normal chat, PDF summarization, context compaction, and search planning
3. Add an app health/status panel for Ollama, MCP server, SearXNG, and SQLite

Possible / Considered Future Enhancements:

Conversation and project UX:
- Add regenerate last answer
- Add edit-and-resubmit for previous user messages
- Add search/filter for projects and chat threads
- Improve thread title generation using the local model

Document and local knowledge:
- Add a document/file management panel for uploaded PDFs
- Allow deleting uploaded thread files safely
- Add per-document summary view
- Allow asking questions against selected documents only
- Add search across previous chats
- Add optional local memory / notes that the user can approve before saving
- Add database backup/export and project export/import

Privacy and permissions:
- Add a tool permission/status panel showing which tools are allowed
- Show exactly which tools were used for each assistant answer
- Add private/no-save thread mode
- Add clearer cleanup behavior for uploaded files when threads are deleted

Developer-assistant capabilities:
- Add local project file review tools with explicit workspace permissions
- Summarize code files and project structure
- Generate TODOs from a project folder
- Maintain a project scratchpad automatically
- Summarize what changed since the previous session

Web-search experiments / known caveat work:
- Build grounded web-answer synthesis using extracted page content
- Add source authority, freshness, and requested-year validation
- Require claim-level citations and conflict handling
- Avoid knowledge-cutoff disclaimers when current evidence is available
- Compare llama3.2:3b with a stronger local model such as an 8B-class model for query rewriting and evidence synthesis
- Add page fetching/extraction for the top ranked sources before final answer generation
- Add structured evidence extraction before final answer generation
- Decide automatically when a user request needs web search
- Treat current web search as experimental until page extraction and stronger grounded synthesis are added

Notes:
This app is private as long as it only talks to the local Ollama server.
External tools such as web search, email, or cloud hosting may involve external services later.
