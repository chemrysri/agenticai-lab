from pathlib import Path

SEARXNG_BASE_URL = "http://localhost:8080"

# Restrict filesystem tools to safe folders only.
REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_FILE_ROOTS = [
    REPO_ROOT / "PrivateAIAssitant",
]

# Your app DB path, if you want MCP SQLite tools to inspect it.
ASSISTANT_DB_PATH = REPO_ROOT / "PrivateAIAssitant" / "assistant.db"