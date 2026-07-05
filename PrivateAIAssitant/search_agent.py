import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from mcp_client import MCPToolError, call_search_web
from ollama_client import ask_ollama


DEFAULT_QUERY_COUNT = 3
MAX_QUERY_LENGTH = 180

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def _parse_query_list(model_response: str) -> list[str]:
    start = model_response.find("[")
    end = model_response.rfind("]")

    if start == -1 or end <= start:
        return []

    try:
        parsed = json.loads(model_response[start : end + 1])
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    queries = []
    seen = set()

    for item in parsed:
        if not isinstance(item, str):
            continue

        query = " ".join(item.split()).strip()
        key = query.casefold()

        if not query or len(query) > MAX_QUERY_LENGTH or key in seen:
            continue

        seen.add(key)
        queries.append(query)

    return queries


def generate_conceptual_queries(
    user_query: str,
    model: str,
    max_queries: int = DEFAULT_QUERY_COUNT,
) -> tuple[list[str], bool]:
    """Keep the exact intent and add complementary conceptual search queries."""
    max_queries = max(1, min(int(max_queries), 5))
    direct_query = " ".join(user_query.split()).strip()[:MAX_QUERY_LENGTH].rstrip()

    if max_queries == 1:
        return [direct_query], False

    expansion_count = max_queries - 1

    messages = [
        {
            "role": "system",
            "content": (
                "You are a web-search query planner. Create complementary search "
                "queries without changing the user's question. Preserve named "
                "entities, dates, locations, and the requested answer type. For "
                "example, a request asking who won must produce queries about the "
                "winner, result, final, or champion, never merely schedules or team "
                "lists. Use useful synonyms and authoritative-source terminology. "
                "Do not answer the request. Return only a valid JSON array of "
                "strings, with no Markdown or commentary."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Create exactly {expansion_count} complementary search queries "
                "for this request. The original request will be searched separately:\n"
                f"<request>{user_query}</request>"
            ),
        },
    ]

    model_response = ask_ollama(messages=messages, model=model)
    generated_queries = _parse_query_list(model_response)
    queries = [direct_query]
    seen = {direct_query.casefold()}

    for generated_query in generated_queries:
        key = generated_query.casefold()

        if key in seen:
            continue

        seen.add(key)
        queries.append(generated_query)

        if len(queries) >= max_queries:
            break

    if len(queries) > 1:
        return queries, False

    return queries, True


def _normalize_url(url: str) -> str:
    url = url.strip()

    if not url:
        return ""

    try:
        parts = urlsplit(url)
    except ValueError:
        return url.casefold()

    normalized_path = parts.path.rstrip("/") or "/"

    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            normalized_path,
            parts.query,
            "",
        )
    )


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9_-]+", value.casefold())
        if token not in STOP_WORDS and len(token) > 1
    }


def _deduplication_key(result: dict[str, Any]) -> str:
    normalized_url = _normalize_url(result.get("url", ""))

    if normalized_url:
        return f"url:{normalized_url}"

    title = " ".join((result.get("title") or "").casefold().split())
    snippet = " ".join((result.get("snippet") or "").casefold().split())
    return f"text:{title}|{snippet[:160]}"


def _get_exception_messages(error: BaseException) -> list[str]:
    nested_errors = getattr(error, "exceptions", None)

    if nested_errors:
        messages = []

        for nested_error in nested_errors:
            messages.extend(_get_exception_messages(nested_error))

        return messages

    message = str(error).strip()
    return [message or error.__class__.__name__]


def rank_and_deduplicate_results(
    query_results: list[tuple[str, list[dict[str, Any]]]],
    original_query: str,
    max_results: int,
) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    original_terms = _tokenize(original_query)
    query_count = max(1, len(query_results))

    for search_query, results in query_results:
        for rank, raw_result in enumerate(results, start=1):
            key = _deduplication_key(raw_result)

            if key == "text:|":
                continue

            if key not in combined:
                combined[key] = {
                    **raw_result,
                    "matched_queries": [],
                    "_rank_score": 0.0,
                    "_best_rank": rank,
                }

            item = combined[key]

            if search_query not in item["matched_queries"]:
                item["matched_queries"].append(search_query)
                item["_rank_score"] += 1.0 / rank

            item["_best_rank"] = min(item["_best_rank"], rank)

            if len(raw_result.get("snippet", "")) > len(item.get("snippet", "")):
                item["snippet"] = raw_result["snippet"]

    ranked_results = []

    for item in combined.values():
        title_terms = _tokenize(item.get("title", ""))
        snippet_terms = _tokenize(item.get("snippet", ""))
        title_overlap = len(original_terms & title_terms)
        snippet_overlap = len(original_terms & snippet_terms)
        denominator = max(1, len(original_terms))
        lexical_score = (2 * title_overlap + snippet_overlap) / (3 * denominator)
        query_coverage = len(item["matched_queries"]) / query_count
        score = item["_rank_score"] + (0.5 * query_coverage) + lexical_score

        item["score"] = round(score, 4)
        ranked_results.append(item)

    ranked_results.sort(
        key=lambda item: (
            -item["score"],
            item["_best_rank"],
            (item.get("title") or "").casefold(),
        )
    )

    for item in ranked_results:
        item.pop("_rank_score", None)
        item.pop("_best_rank", None)

    return ranked_results[: max(1, int(max_results))]


def run_conceptual_search(
    user_query: str,
    model: str,
    max_results: int = 5,
    language: str = "en",
    time_range: str | None = None,
    max_queries: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    queries, used_fallback = generate_conceptual_queries(
        user_query=user_query,
        model=model,
        max_queries=max_queries,
    )

    query_results = []
    errors = []

    for query in queries:
        try:
            response = call_search_web(
                query=query,
                max_results=max_results,
                language=language,
                time_range=time_range,
            )
            query_results.append((query, response.get("results", [])))
        except Exception as error:
            error_message = "; ".join(dict.fromkeys(_get_exception_messages(error)))
            errors.append({"query": query, "error": error_message})

    if errors and len(errors) == len(queries):
        error_details = "; ".join(
            f"{item['query']}: {item['error']}" for item in errors
        )
        raise MCPToolError(f"All conceptual searches failed. {error_details}")

    ranked_results = rank_and_deduplicate_results(
        query_results=query_results,
        original_query=user_query,
        max_results=max_results,
    )

    return {
        "query": user_query,
        "source": "conceptual_search",
        "generated_queries": queries,
        "query_generation_fallback": used_fallback,
        "results": ranked_results,
        "errors": errors,
    }
