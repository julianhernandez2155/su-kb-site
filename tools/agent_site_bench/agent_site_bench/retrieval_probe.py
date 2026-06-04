from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from .config import BenchmarkQuestion, SiteConfig
from .fetcher import Fetcher, is_allowed_url


STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "someone",
    "the",
    "to",
    "use",
    "what",
    "where",
    "with",
}


@dataclass(frozen=True)
class LlmsEntry:
    title: str
    url: str
    description: str
    source_line: str
    position: int


def run_retrieval_probe_for_site_question(
    *,
    fetcher: Fetcher,
    site: SiteConfig,
    question: BenchmarkQuestion,
    top_k: int = 3,
    allow_external_fetches: bool = False,
) -> dict[str, Any]:
    llms_url = urljoin(site.resolved_machine_root_url, "llms.txt")
    llms_fetch = fetcher.fetch(llms_url)
    entries = parse_llms_entries(llms_fetch.text, llms_fetch.final_url or llms_url)
    scored = score_entries(question.question, entries)
    candidates = scored[:top_k]

    candidate_records = []
    fetched_bytes = llms_fetch.bytes
    elapsed_ms = llms_fetch.elapsed_ms
    for candidate in candidates:
        entry = candidate["entry"]
        if not is_allowed_url(entry.url, site.effective_allowed_hosts, allow_external_fetches):
            fetch_record = {
                "url": entry.url,
                "status_code": None,
                "bytes": 0,
                "elapsed_ms": 0,
                "error": "URL outside configured allowed hosts",
            }
        else:
            fetch = fetcher.fetch(entry.url)
            fetched_bytes += fetch.bytes
            elapsed_ms += fetch.elapsed_ms
            fetch_record = fetch.to_record(include_text=False)

        candidate_records.append(
            {
                "rank": len(candidate_records) + 1,
                "title": entry.title,
                "url": entry.url,
                "description": entry.description,
                "score": candidate["score"],
                "matched_terms": candidate["matched_terms"],
                "fetch": fetch_record,
                "expected_match": _matches_expected(entry.url, question.expected_urls),
            }
        )

    expected_hit_rank = None
    expected_hit_url = None
    for candidate in candidate_records:
        if candidate["expected_match"]:
            expected_hit_rank = candidate["rank"]
            expected_hit_url = candidate["url"]
            break

    return {
        "question": asdict(question),
        "site": asdict(site),
        "mode": "llms_txt_to_markdown_probe",
        "llms_url": llms_url,
        "llms_fetch": llms_fetch.to_record(include_text=False),
        "llms_entry_count": len(entries),
        "top_k": top_k,
        "fetch_count": 1 + len(candidate_records),
        "total_bytes": fetched_bytes,
        "total_elapsed_ms": elapsed_ms,
        "expected_urls": list(question.expected_urls),
        "expected_hit_rank": expected_hit_rank,
        "expected_hit_url": expected_hit_url,
        "candidates": candidate_records,
    }


def parse_llms_entries(text: str, base_url: str) -> list[LlmsEntry]:
    entries = []
    pattern = re.compile(r"^\s*[-*]\s+\[([^\]]+)\]\(([^)]+)\)\s*:?\s*(.*)$")
    for position, line in enumerate(text.splitlines(), start=1):
        match = pattern.match(line)
        if not match:
            continue
        title, href, description = match.groups()
        entries.append(
            LlmsEntry(
                title=title.strip(),
                url=urljoin(base_url, href.strip()),
                description=description.strip(),
                source_line=line.strip(),
                position=position,
            )
        )
    return entries


def score_entries(question: str, entries: list[LlmsEntry]) -> list[dict[str, Any]]:
    question_terms = _content_terms(question)
    scored = []
    for entry in entries:
        title_terms = _content_terms(entry.title)
        description_terms = _content_terms(entry.description)
        url_terms = _content_terms(urlparse(entry.url).path.replace("-", " "))
        title_hits = question_terms & title_terms
        description_hits = question_terms & description_terms
        url_hits = question_terms & url_terms
        score = (4 * len(title_hits)) + (2 * len(description_hits)) + len(url_hits)
        matched_terms = sorted(title_hits | description_hits | url_hits)
        scored.append(
            {
                "entry": entry,
                "score": score,
                "matched_terms": matched_terms,
                "position": entry.position,
            }
        )
    return sorted(scored, key=lambda item: (-item["score"], item["position"]))


def _content_terms(text: str) -> set[str]:
    terms = set()
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        if len(token) <= 1 or token in STOP_WORDS:
            continue
        terms.add(token)
    return terms


def _matches_expected(url: str, expected_urls: tuple[str, ...]) -> bool:
    if not expected_urls:
        return False
    parsed_path = urlparse(url).path
    for expected in expected_urls:
        if expected in url or expected in parsed_path:
            return True
    return False
