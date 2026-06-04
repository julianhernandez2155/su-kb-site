from __future__ import annotations

import json
import re
from typing import Any

from .config import BenchmarkQuestion, BenchConfig
from .openrouter_client import OpenRouterClient


JUDGE_SCHEMA_DESCRIPTION = {
    "correctness": "object mapping site names to scores from 0 to 5",
    "citation_quality": "object mapping site names to scores from 0 to 5",
    "provenance_quality": "object mapping site names to scores from 0 to 5",
    "fetch_efficiency": "object mapping site names to scores from 0 to 5",
    "notes": "short explanation of the judgment",
    "winner": "one site name, tie, or insufficient",
}


def judge_question(
    *,
    client: OpenRouterClient,
    config: BenchConfig,
    question: BenchmarkQuestion,
    site_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt = {
        "task": "Judge two knowledge-base agent benchmark answers.",
        "required_json_shape": JUDGE_SCHEMA_DESCRIPTION,
        "question": question.question,
        "expected": question.expected,
        "rubric": question.rubric,
        "site_runs": [
            {
                "site": run["site"]["name"],
                "fetch_count": run["fetch_count"],
                "max_fetches_reached": run["max_fetches_reached"],
                "invalid_no_fetch_answer": run["invalid_no_fetch_answer"],
                "fetched_urls": run["fetched_urls"],
                "final_answer": run["final_answer"],
            }
            for run in site_runs
        ],
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict benchmark judge. Return only JSON. "
                "Score answer quality and provenance from the evidence in fetched URLs and final answers. "
                "Do not reward answers that appear uncited or based on prior knowledge."
            ),
        },
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=True, indent=2)},
    ]
    response = client.chat_completion(
        model=config.models.judge,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0,
    )
    raw_text = response["choices"][0]["message"].get("content") or ""
    parsed = parse_judge_json(raw_text)
    if parsed is None:
        return {
            "question_id": question.id,
            "model": config.models.judge,
            "judge_parse_error": True,
            "raw_judge_text": raw_text,
        }
    parsed.update(
        {
            "question_id": question.id,
            "model": config.models.judge,
            "judge_parse_error": False,
        }
    )
    for key in ("correctness", "citation_quality", "provenance_quality", "fetch_efficiency", "notes", "winner"):
        parsed.setdefault(key, None)
    return parsed


def parse_judge_json(raw_text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(raw_text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
