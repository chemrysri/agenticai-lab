import asyncio
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_SEARCH_SERVER_URL = "http://localhost:8000/mcp"

class MCPToolError(Exception):
    pass


async def _call_search_web_async(
    query: str,
    max_results: int = 5,
    language: str = "en",
    time_range: str | None = None,
) -> dict[str, Any]:
    async with streamable_http_client(MCP_SEARCH_SERVER_URL) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "search_web",
                arguments={
                    "query": query,
                    "max_results": max_results,
                    "language": language,
                    "time_range": time_range,
                },
            )

            if result.isError:
                error_text = "MCP search tool failed."

                if result.content:
                    error_text = getattr(result.content[0], "text", error_text)

                raise MCPToolError(error_text)

            if result.structuredContent:
                return result.structuredContent

            if result.content:
                text = getattr(result.content[0], "text", "")
                return {
                    "query": query,
                    "source": "mcp",
                    "results": [],
                    "raw_text": text,
                }

            return {
                "query": query,
                "source": "mcp",
                "results": [],
            }


def call_search_web(
    query: str,
    max_results: int = 5,
    language: str = "en",
    time_range: str | None = None,
) -> dict[str, Any]:
    try:
        return asyncio.run(
            _call_search_web_async(
                query=query,
                max_results=max_results,
                language=language,
                time_range=time_range,
            )
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()

        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                _call_search_web_async(
                    query=query,
                    max_results=max_results,
                    language=language,
                    time_range=time_range,
                )
            )
        finally:
            loop.close()


def format_search_results_for_model(search_response: dict[str, Any]) -> str:
    query = search_response.get("query", "")
    results = search_response.get("results", [])

    if not results:
        raw_text = search_response.get("raw_text", "")

        if raw_text:
            return raw_text

        return (
            "A web search was attempted, but no useful results were returned.\n"
            f"Search query: {query}"
        )

    content = (
        "Current web search results are below. Use them as supporting context. "
        "Do not invent facts beyond these snippets. Include source links when useful.\n\n"
        f"Search query: {query}\n\n"
    )

    for index, result in enumerate(results, start=1):
        content += (
            f"[{index}] {result.get('title', 'Untitled result')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Snippet: {result.get('snippet', '')}\n"
            f"Engine: {result.get('engine', '')}\n\n"
        )

    return content


def format_search_results_for_display(search_response: dict[str, Any]) -> str:
    results = search_response.get("results", [])

    if not results:
        return "_No web results returned._"

    lines = []

    for index, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled result"
        url = result.get("url") or ""
        snippet = result.get("snippet") or ""

        if url:
            lines.append(f"{index}. [{title}]({url})")
        else:
            lines.append(f"{index}. {title}")

        if snippet:
            lines.append(f"   {snippet}")

    return "\n".join(lines)