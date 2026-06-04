from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any
from urllib.parse import urljoin

from .config import BenchmarkQuestion, BenchConfig, SiteConfig
from .fetcher import Fetcher, is_allowed_url, normalize_requested_url
from .openrouter_client import OpenRouterClient


FETCH_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": "Fetch one URL from the configured knowledge-base site and return page text plus metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Absolute or site-relative URL to fetch.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short reason this URL is needed.",
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
}


def run_agent_for_site_question(
    *,
    client: OpenRouterClient,
    fetcher: Fetcher,
    config: BenchConfig,
    site: SiteConfig,
    question: BenchmarkQuestion,
) -> dict[str, Any]:
    expected_first_fetch_url = urljoin(site.resolved_machine_root_url, "llms.txt")
    system_prompt = (
        "You are evaluating one public knowledge-base site through the same route used by the installed SU skill. "
        f"You know only this retrieval start URL: {expected_first_fetch_url}. "
        "Do not answer from memory. Your first action must be fetch_url on that llms.txt URL. "
        "Read the index, fetch only the relevant Markdown .md page or pages needed to answer, then stop. "
        "Answer with citations to fetched URLs and source provenance when present. "
        f"You have at most {config.max_fetches} fetches."
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question.question},
    ]
    transcript: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []
    fetched_urls: list[dict[str, Any]] = []
    final_answer = ""
    invalid_no_fetch_answer = False
    invalid_first_fetch = False
    max_fetches_reached = False
    allowed_hosts = site.effective_allowed_hosts

    for _turn in range(config.max_fetches + 6):
        response = client.chat_completion(
            model=config.models.agent,
            messages=messages,
            tools=[FETCH_TOOL],
            tool_choice="auto",
            temperature=0,
        )
        message = response["choices"][0]["message"]
        transcript.append({"role": "assistant", "message": message})

        assistant_message = {"role": "assistant", "content": message.get("content")}
        if message.get("tool_calls"):
            assistant_message["tool_calls"] = message["tool_calls"]
        messages.append(assistant_message)

        if not message.get("tool_calls"):
            final_answer = message.get("content") or ""
            invalid_no_fetch_answer = len(fetched_urls) == 0
            break

        for tool_call in message["tool_calls"]:
            call_record = _tool_call_record(tool_call)
            tool_calls.append(call_record)
            if len(fetched_urls) >= config.max_fetches:
                max_fetches_reached = True
                tool_result = {
                    "ok": False,
                    "error": f"max_fetches reached ({config.max_fetches})",
                }
                messages.append(_tool_message(tool_call, tool_result))
                transcript.append({"role": "tool", "tool_call_id": tool_call.get("id"), "content": tool_result})
                continue

            requested_url = call_record.get("arguments", {}).get("url", "")
            normalized_url = normalize_requested_url(site.start_url, str(requested_url))
            if len(fetched_urls) == 0 and normalized_url.rstrip("/") != expected_first_fetch_url.rstrip("/"):
                invalid_first_fetch = True
            if not is_allowed_url(normalized_url, allowed_hosts, config.allow_external_fetches):
                tool_result = {
                    "ok": False,
                    "url": normalized_url,
                    "error": "URL outside configured allowed hosts",
                    "allowed_hosts": list(allowed_hosts),
                }
                messages.append(_tool_message(tool_call, tool_result))
                transcript.append({"role": "tool", "tool_call_id": tool_call.get("id"), "content": tool_result})
                continue

            fetch_result = fetcher.fetch(normalized_url)
            fetched_urls.append(fetch_result.to_record(include_text=False))
            tool_result = {
                "ok": fetch_result.error is None and fetch_result.status_code is not None and fetch_result.status_code < 400,
                "url": fetch_result.url,
                "final_url": fetch_result.final_url,
                "status_code": fetch_result.status_code,
                "content_type": fetch_result.content_type,
                "bytes": fetch_result.bytes,
                "error": fetch_result.error,
                "body": _trim(fetch_result.text, config.max_page_chars),
            }
            messages.append(_tool_message(tool_call, tool_result))
            transcript.append({"role": "tool", "tool_call_id": tool_call.get("id"), "content": tool_result})

        if max_fetches_reached:
            continue

    return {
        "question": asdict(question),
        "site": asdict(site),
        "model": config.models.agent,
        "max_fetches": config.max_fetches,
        "fetch_count": len(fetched_urls),
        "max_fetches_reached": max_fetches_reached,
        "invalid_no_fetch_answer": invalid_no_fetch_answer,
        "expected_first_fetch_url": expected_first_fetch_url,
        "invalid_first_fetch": invalid_first_fetch,
        "tool_calls": tool_calls,
        "fetched_urls": fetched_urls,
        "final_answer": final_answer,
        "transcript": transcript,
    }


def _tool_call_record(tool_call: dict[str, Any]) -> dict[str, Any]:
    function = tool_call.get("function") or {}
    raw_arguments = function.get("arguments") or "{}"
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        arguments = {"_parse_error": True, "raw": raw_arguments}
    return {
        "id": tool_call.get("id"),
        "name": function.get("name"),
        "arguments": arguments,
    }


def _tool_message(tool_call: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call.get("id"),
        "name": "fetch_url",
        "content": json.dumps(content, ensure_ascii=True),
    }


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[agent_site_bench: tool output truncated]"
