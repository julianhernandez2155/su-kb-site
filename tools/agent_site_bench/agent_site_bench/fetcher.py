from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str | None
    status_code: int | None
    content_type: str | None
    bytes: int
    text: str
    elapsed_ms: int
    error: str | None = None

    def to_record(self, include_text: bool = True, text_limit: int | None = None) -> dict:
        data = asdict(self)
        if not include_text:
            data.pop("text", None)
        elif text_limit is not None and len(data["text"]) > text_limit:
            data["text"] = data["text"][:text_limit]
            data["text_truncated"] = True
        return data


class Fetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        user_agent: str = "agent_site_bench/0.1",
        max_bytes: int = 2_000_000,
    ) -> None:
        self.max_bytes = max_bytes
        self.client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": user_agent, "Accept": "text/html,text/plain,application/xml,*/*"},
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self, url: str) -> FetchResult:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return FetchResult(
                url=url,
                final_url=None,
                status_code=None,
                content_type=None,
                bytes=0,
                text="",
                elapsed_ms=0,
                error=f"unsupported URL scheme: {parsed.scheme or '(missing)'}",
            )

        start = perf_counter()
        try:
            response = self.client.get(url)
            elapsed_ms = int((perf_counter() - start) * 1000)
            body = response.content[: self.max_bytes]
            text = body.decode(response.encoding or "utf-8", errors="replace")
            if len(response.content) > self.max_bytes:
                text += "\n\n[agent_site_bench: response truncated after max_bytes]"
            return FetchResult(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=response.headers.get("content-type"),
                bytes=len(response.content),
                text=text,
                elapsed_ms=elapsed_ms,
                error=None,
            )
        except httpx.HTTPError as exc:
            elapsed_ms = int((perf_counter() - start) * 1000)
            return FetchResult(
                url=url,
                final_url=None,
                status_code=None,
                content_type=None,
                bytes=0,
                text="",
                elapsed_ms=elapsed_ms,
                error=f"{type(exc).__name__}: {exc}",
            )


def normalize_requested_url(base_url: str, requested_url: str) -> str:
    return urljoin(base_url, requested_url)


def is_allowed_url(url: str, allowed_hosts: Iterable[str], allow_external: bool = False) -> bool:
    if allow_external:
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc in set(allowed_hosts)
