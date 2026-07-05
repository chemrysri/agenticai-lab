# MCP Tools

This folder contains the local MCP tools that can be used used by the other Applications.

The goal of this folder is to keep tool-like capabilities separate from the main Streamlit application.

The Streamlit app handles:

- UI
- users
- projects
- chat threads
- messages
- PDF uploads
- context compaction
- Ollama interaction

The MCP server handles external/local tools such as:

- internet search
- filesystem access
- SQLite inspection
- calendar access (planned)
- future automation tools

Current implemented tool:

- `search_web` using local SearXNG

Planned tools:

- filesystem tools
- SQLite tools
- calendar tools
- document tools
- code execution tools

---

## Quick Start on Windows

Run the following commands from the `agenticai-lab` repository root.

### One-time setup

Create one virtual environment for the Streamlit application and MCP server:

```powershell
python -m venv .venv

.\.venv\Scripts\python.exe -m pip install `
  -r .\PrivateAIAssitant\requirements.txt `
  -r .\mcp_tools\requirements.txt

ollama pull llama3.2:3b
```

### Start the application

Keep each process running in a separate PowerShell terminal.

#### Terminal 1: Ollama

```powershell
ollama serve
```

Skip this command if Ollama is already running as a Windows background service.

#### Terminal 2: SearXNG

```powershell
cd .\mcp_tools\searxng
docker compose up -d
docker compose ps
```

#### Terminal 3: MCP server

```powershell
cd .\mcp_tools
..\.venv\Scripts\python.exe server.py
```

Leave this terminal running. The MCP endpoint is available at:

```text
http://localhost:8000/mcp
```

#### Terminal 4: Streamlit application

```powershell
cd .\PrivateAIAssitant
..\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit. To test conceptual search, enable
**Search the internet for latest updates**, submit a current-information
question, and expand **Web search results used** to inspect the generated
queries and ranked results.

The required startup order is:

```text
Ollama -> SearXNG -> MCP server -> Streamlit application
```

---

## Folder Structure

Recommended structure:

```text
mcp_tools/
    ├── README.md
    ├── server.py
    ├── config.py
    ├── requirements.txt
    │
    ├── tools/
    │   ├── __init__.py
    │   ├── searxng_tool.py
    │   ├── filesystem_tool.py
    │   ├── sqlite_tool.py
    │   └── calendar_tool.py
    │
    └── searxng/
        ├── docker-compose.yml
        └── settings.yml
```

---

## What This MCP Server Does

This folder runs a local MCP server.

Other Applications talks to this MCP server when it needs tool capabilities.

Example search flow:

```text
User asks a question
        ↓
Streamlit app checks whether web search is enabled
        ↓
Streamlit app calls MCP tool: search_web
        ↓
MCP server calls local SearXNG
        ↓
SearXNG returns web results
        ↓
Search results are injected into the Ollama prompt
        ↓
Local model answers using web search context
```

The local LLM does not browse the internet by itself.

Instead:

```text
Python app + MCP tool perform search
        ↓
Search results are passed to the model as context
```

---

## Current MCP Tool

### `search_web`

Searches the internet through a local SearXNG instance.

Tool shape:

```text
search_web(query, max_results, language, time_range)
```

Parameters:

```text
query        Search query text
max_results  Number of results to return, usually 1-10
language     Search language, for example "en"
time_range   Optional: "day", "month", "year", or null
```

Example response:

```json
{
  "query": "latest ollama vision models",
  "source": "searxng",
  "results": [
    {
      "title": "Example result",
      "url": "https://example.com",
      "snippet": "Short search result snippet",
      "engine": "duckduckgo",
      "category": "general",
      "published_date": ""
    }
  ]
}
```

---

## Setup

## SearXNG Setup

SearXNG is the local search backend used by the MCP `search_web` tool.

The MCP server does not search the web by itself.

The full flow is:

```text
Application
        ↓
mcp_client.py
        ↓
mcp_tools/server.py
        ↓
tools/searxng_tool.py
        ↓
SearXNG
        ↓
Search engines
```

---

### 1. SearXNG Folder

SearXNG files should live here:

```text
mcp_tools/
└── searxng/
    ├── docker-compose.yml
    └── settings.yml
```
---

### 2. Start SearXNG

Run:

```powershell
docker compose up -d
```

SearXNG should now be available at:

```text
http://localhost:8080
```

---

### 3. Test SearXNG Directly

```powershell
curl "http://localhost:8080/search?q=ollama+latest+models&format=json"
```

Expected result:

```text
JSON response containing search results
```

If you get:

```text
403 Forbidden
```

then JSON output is not enabled or the container is not using the correct `settings.yml`.

Fix:

```powershell
docker compose down
docker compose up -d --force-recreate
```

Then test again.

---

## MCP Server

The MCP server exposes all local tools through one server.

Recommended design:

```text
mcp_tools/
├── server.py
├── config.py
├── requirements.txt
└── tools/
    ├── searxng_tool.py
    ├── filesystem_tool.py
    ├── sqlite_tool.py
    └── calendar_tool.py
```

---

## Start the MCP Server

Run:

```powershell
python server.py
```

The MCP server should expose tools at:

```text
http://localhost:8000/mcp
```

Do not use a browser to test this URL as if it were a normal web page. The MCP
endpoint requires an MCP client and the `text/event-stream` protocol. Opening it
directly in a browser may return:

```json
{
  "jsonrpc": "2.0",
  "id": "server-error",
  "error": {
    "code": -32600,
    "message": "Not Acceptable: Client must accept text/event-stream"
  }
}
```

This response is expected and confirms that the MCP server is reachable. Test
the complete integration through `PrivateAIAssitant/mcp_client.py` by starting
the Streamlit app, enabling web search, and submitting a question. The MCP
client supplies the required protocol headers automatically.

---

## Application Integration

The Streamlit app calls the MCP server through:

```text
Application/mcp_client.py
```

The MCP URL should be:

```python
MCP_SEARCH_SERVER_URL = "http://localhost:8000/mcp"
```

The app should not call SearXNG directly.

Correct flow:

```text
Application/app.py
        ↓
Application/mcp_client.py
        ↓
http://localhost:8000/mcp
        ↓
mcp_tools/server.py
        ↓
tools/searxng_tool.py
        ↓
http://localhost:8080/search
```

---

## Required Running Processes

For internet search to work, these must be running:

```text
1. Ollama
2. SearXNG Docker container
3. MCP tools server
4. Streamlit Application
```

Typical local setup:

```text
Terminal 1: ollama serve
Terminal 2: docker compose up -d
Terminal 3: python server.py
Terminal 4: streamlit run app.py
```

---

## Run Commands

### Terminal 1: Ollama

```powershell
ollama serve
```

If Ollama is already running as a background service, this may not be needed.

---

### Terminal 2: SearXNG

```powershell
docker compose up -d
```

---

### Terminal 3: MCP Tools Server

```powershell
python server.py
```

---

### Terminal 4: Application

```powershell
streamlit run app.py
```

---

## Search Behavior

Current behavior:

```text
If web search toggle is ON:
    ask Ollama for complementary conceptual search queries
    call MCP search_web once per generated query
    deduplicate results by normalized URL
    rank results by search position, query coverage, and text relevance
    inject the highest-ranked evidence into model context
```

If query generation fails or Ollama returns invalid JSON, the app falls back to
searching the original user message.

Future behavior:

```text
If web search toggle is ON:
    decide whether search is actually needed
    search only when current information or external evidence is needed
```

The long-term meaning of the toggle should be:

```text
Assistant is allowed to search
```

not:

```text
Always search the exact latest user message
```

---

## Adding More Tools

The MCP server can expose many tools from one `server.py`.

Future tools can be added like this:

```text
mcp_tools/tools/
├── searxng_tool.py
├── filesystem_tool.py
├── sqlite_tool.py
└── calendar_tool.py
```

Each tool file should provide a registration function:

```python
def register_some_tools(mcp):
    @mcp.tool()
    def some_tool(...):
        ...
```

Then register it in `server.py`:

```python
from tools.some_tool import register_some_tools

register_some_tools(mcp)
```

Restart the MCP server after adding new tools.

---

## Future Tool: Filesystem

Possible tools:

```text
list_files(path)
read_text_file(path)
search_files(query)
```

Safety rules:

```text
- Only allow access to approved folders
- Never expose the entire filesystem
- Avoid arbitrary file writes at first
- Start read-only
```

---

## Future Tool: SQLite

Possible tools:

```text
list_tables()
describe_table(table_name)
run_readonly_query(sql)
```

Safety rules:

```text
- Start with SELECT-only queries
- Block INSERT, UPDATE, DELETE, DROP, ALTER
- Limit number of returned rows
```

---

## Future Tool: Calendar

Possible tools:

```text
list_events(date_range)
find_free_time(...)
create_event(...)
```

Safety rules:

```text
- Start read-only
- Add write tools only after confirmation flows exist
- Never silently modify calendar events
```

---

## Security Notes

This MCP server is intended for local development.

Do not expose it publicly without authentication and access control.

Important practices:

```text
- Keep the MCP server local
- Keep SearXNG local
- Restrict filesystem access
- Keep SQLite tools read-only initially
- Avoid arbitrary shell execution tools
- Do not expose secrets, tokens, or private credentials
- Be cautious with future calendar/email write tools
```

---

## Troubleshooting

### SearXNG returns `403 Forbidden`

Cause:

```text
JSON output is not enabled
```

Check:

```text
mcp_tools/searxng/settings.yml
```

Make sure it contains:

```yaml
search:
  formats:
    - html
    - json
```

Recreate container:

```powershell
docker compose down
docker compose up -d --force-recreate
```

Test:

```powershell
curl "http://localhost:8080/search?q=test&format=json"
```

---

### MCP server cannot connect to SearXNG

Check SearXNG is running:

```powershell
docker ps
```

Test SearXNG directly:

```powershell
curl "http://localhost:8080/search?q=test&format=json"
```

If this fails, fix SearXNG first.

---

### Streamlit cannot connect to MCP

Make sure MCP server is running:

```powershell
python server.py
```

Check app-side MCP URL:

```python
MCP_SEARCH_SERVER_URL = "http://localhost:8000/mcp"
```

---

### Search results are weak or irrelevant

Inspect the generated queries shown in the app's search-results expander. If
they miss the user's intent, improve the query-planning prompt in
`PrivateAIAssitant/search_agent.py`. Future ranking improvements can add:

```text
- search intent detection
- source quality signals
- freshness scoring
- source filtering
```

---

## Next Steps: Grounded Web Answers

Conceptual query generation improves search coverage, but retrieval alone does
not guarantee a clean or reliable answer. The next phase should improve evidence
validation and answer synthesis.

### Current limitation notes

- SearXNG snippets can be incomplete. A high-ranked result may identify the
  finalists without containing the winner, score, or other requested fact.
- Ranking currently rewards search position, query coverage, and text overlap.
  It does not yet measure source authority, factual completeness, or freshness.
- Search results can contain stale or mismatched URLs, such as a page title that
  mentions the requested year while the URL points to an older season.
- The assistant currently receives snippets rather than the full content of the
  highest-ranked pages, so important supporting details can be missing.
- Small local models such as `llama3.2:3b` can add generic recommendations or
  canned knowledge-cutoff disclaimers even when current evidence is available.
- The answer prompt does not yet strictly require direct answers, claim-level
  citations, or explicit handling of conflicting sources.

### Planned improvements

1. Reject or penalize results whose URL, title, or date conflicts with the
   requested time period.
2. Add source-quality signals and prefer official or established sources where
   appropriate.
3. Fetch and extract content from the highest-ranked pages instead of relying
   only on search snippets.
4. Add a grounded synthesis step that answers only from the collected evidence.
5. Suppress knowledge-cutoff disclaimers when sufficient current evidence is
   present.
6. Require citations beside supported claims and explicitly identify conflicts
   or missing evidence.
7. Evaluate a stronger local model, such as a suitable 8B model, for query
   planning and evidence synthesis.
8. Decide automatically whether a user request actually requires web search.

---

## Current Status

Implemented:

```text
- Single local MCP server
- SearXNG-backed search_web tool
- Streamable HTTP MCP endpoint
- Streamlit app can call MCP search
- Ollama-generated conceptual search queries
- Multi-query result deduplication and ranking
- Ranked search evidence injected into Ollama context
- Restricted filesystem read tools
- Read-only SQLite inspection tools
```

Planned:

```text
- Grounded page-content extraction and answer synthesis
- Source authority, freshness, and date-consistency ranking
- Claim-level citations and conflict handling
- Search history in SQLite
- Automatic search-need detection
- Calendar tools
- Additional local tools
```
