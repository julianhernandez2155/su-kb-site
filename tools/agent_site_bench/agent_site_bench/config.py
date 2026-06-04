from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import yaml


@dataclass(frozen=True)
class SiteConfig:
    name: str
    start_url: str
    machine_root_url: str | None = None
    protected_design: bool = False
    allowed_hosts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def resolved_machine_root_url(self) -> str:
        if self.machine_root_url:
            return ensure_trailing_slash(self.machine_root_url)
        parsed = urlparse(self.start_url)
        if parsed.path.endswith("/"):
            base_path = parsed.path
        else:
            base_path = parsed.path.rsplit("/", 1)[0] + "/"
        return parsed._replace(path=base_path, params="", query="", fragment="").geturl()

    @property
    def effective_allowed_hosts(self) -> tuple[str, ...]:
        hosts = {urlparse(self.start_url).netloc}
        hosts.update(host for host in self.allowed_hosts if host)
        return tuple(sorted(hosts))


@dataclass(frozen=True)
class ModelsConfig:
    agent: str
    judge: str


@dataclass(frozen=True)
class BenchConfig:
    sites: tuple[SiteConfig, ...]
    models: ModelsConfig
    max_fetches: int = 8
    retrieval_top_k: int = 3
    timeout_seconds: float = 20.0
    max_page_chars: int = 12000
    allow_external_fetches: bool = False
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    user_agent: str = "agent_site_bench/0.1"


@dataclass(frozen=True)
class BenchmarkQuestion:
    id: str
    question: str
    expected: str | None = None
    expected_urls: tuple[str, ...] = field(default_factory=tuple)
    rubric: str | None = None


def ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"


def load_config(path: str | Path) -> BenchConfig:
    data = _load_yaml_mapping(path)
    sites = tuple(_parse_site(item) for item in _require_list(data, "sites"))
    if len(sites) != 2:
        raise ValueError(f"config.sites must contain exactly two sites; found {len(sites)}")

    models_raw = _require_mapping(data, "models")
    models = ModelsConfig(
        agent=_require_string(models_raw, "agent"),
        judge=_require_string(models_raw, "judge"),
    )
    if not models.agent or not models.judge:
        raise ValueError("models.agent and models.judge are required")

    return BenchConfig(
        sites=sites,
        models=models,
        max_fetches=_optional_int(data, "max_fetches", 8, minimum=1),
        retrieval_top_k=_optional_int(data, "retrieval_top_k", 3, minimum=1),
        timeout_seconds=float(data.get("timeout_seconds", 20.0)),
        max_page_chars=_optional_int(data, "max_page_chars", 12000, minimum=1000),
        allow_external_fetches=bool(data.get("allow_external_fetches", False)),
        openrouter_base_url=str(data.get("openrouter_base_url", "https://openrouter.ai/api/v1")),
        user_agent=str(data.get("user_agent", "agent_site_bench/0.1")),
    )


def load_questions(path: str | Path) -> tuple[BenchmarkQuestion, ...]:
    data = _load_yaml_mapping(path)
    questions = []
    seen_ids: set[str] = set()
    for item in _require_list(data, "questions"):
        if not isinstance(item, dict):
            raise ValueError("each question entry must be a mapping")
        question_id = _require_string(item, "id")
        if question_id in seen_ids:
            raise ValueError(f"duplicate question id: {question_id}")
        seen_ids.add(question_id)
        questions.append(
            BenchmarkQuestion(
                id=question_id,
                question=_require_string(item, "question"),
                expected=_optional_string(item, "expected"),
                expected_urls=_optional_string_tuple(item, "expected_urls"),
                rubric=_optional_string(item, "rubric"),
            )
        )
    if not questions:
        raise ValueError("questions must contain at least one question")
    return tuple(questions)


def resolve_against_site(site: SiteConfig, url_or_path: str) -> str:
    return urljoin(site.resolved_machine_root_url, url_or_path)


def _parse_site(item: Any) -> SiteConfig:
    if not isinstance(item, dict):
        raise ValueError("each site entry must be a mapping")
    allowed_hosts = item.get("allowed_hosts") or []
    if not isinstance(allowed_hosts, list):
        raise ValueError("site.allowed_hosts must be a list when provided")
    start_url = _require_string(item, "start_url")
    parsed = urlparse(start_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"site.start_url must be an absolute http(s) URL: {start_url}")
    machine_root = _optional_string(item, "machine_root_url")
    if machine_root:
        machine_parsed = urlparse(machine_root)
        if machine_parsed.scheme not in {"http", "https"} or not machine_parsed.netloc:
            raise ValueError(f"site.machine_root_url must be an absolute http(s) URL: {machine_root}")
    return SiteConfig(
        name=_require_string(item, "name"),
        start_url=start_url,
        machine_root_url=machine_root,
        protected_design=bool(item.get("protected_design", False)),
        allowed_hosts=tuple(str(host) for host in allowed_hosts),
    )


def _load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return loaded


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return value


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string when provided")
    return value.strip() or None


def _optional_string_tuple(data: dict[str, Any], key: str) -> tuple[str, ...]:
    value = data.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a string or list of strings when provided")
    values = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain only strings")
        stripped = item.strip()
        if stripped:
            values.append(stripped)
    return tuple(values)


def _optional_int(data: dict[str, Any], key: str, default: int, minimum: int) -> int:
    value = int(data.get(key, default))
    if value < minimum:
        raise ValueError(f"{key} must be at least {minimum}")
    return value
