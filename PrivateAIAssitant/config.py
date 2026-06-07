OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2:3b"
DB_PATH = "assistant.db"

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful private AI assistant. "
    "Give clear, practical, beginner-friendly answers."
)

# Counts total messages: user + assistant.
# Example: 10 means roughly every 5 back-and-forth turns.
DEFAULT_CONTEXT_COMPACTION_N = 10

MCP_SEARCH_SERVER_URL = "http://localhost:8000/mcp"