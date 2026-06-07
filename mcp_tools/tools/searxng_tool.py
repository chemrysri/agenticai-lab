from typing import Any

import requests

from config import SEARXNG_BASE_URL


def search_searxng(
    query: str,
    max_results: int = 5,
    language: str = "en",
    time_range: str | None = None,
) -> dict[str, Any]:
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    max_results = max(1, min(int(max_results), 10))

    params = {
        "q": query.strip(),
        "format": "json",
        "language": language,
    }

    if time_range:
        params["time_range"] = time_range

    response = requests.get(
        f"{SEARXNG_BASE_URL.rstrip('/')}/search",
        params=params,
        timeout=30,
    )

    if response.status_code == 403:
        raise RuntimeError(
            "SearXNG returned 403. Ensure JSON output is enabled in settings.yml."
        )

    response.raise_for_status()

    data = response.json()
    raw_results = data.get("results", [])

    results = []

    for item in raw_results[:max_results]:
        results.append(
            {
                "title": item.get("title", "").strip(),
                "url": item.get("url", "").strip(),
                "snippet": (
                    item.get("content")
                    or item.get("snippet")
                    or item.get("description")
                    or ""
                ).strip(),
                "engine": item.get("engine", ""),
                "category": item.get("category", ""),
                "published_date": item.get("publishedDate", ""),
            }
        )

    return {
        "query": query,
        "source": "searxng",
        "results": results,
    }


def register_searxng_tools(mcp):
    @mcp.tool()
    def search_web(
        query: str,
        max_results: int = 5,
        language: str = "en",
        time_range: str | None = None,
    ) -> dict[str, Any]:
        """
        Search the web using the local SearXNG instance.
        """
        return search_searxng(
            query=query,
            max_results=max_results,
            language=language,
            time_range=time_range,
        )