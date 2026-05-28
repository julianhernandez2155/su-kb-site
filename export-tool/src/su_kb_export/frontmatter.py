"""Frontmatter build + serialize for su-kb-site (ADR-0002 8-field schema).

Adapted from su-kb-pipeline's 26-field schema. The public KB drops everything
access-related, PII-bearing, or build-internal. The on-disk frontmatter is the
LLM-readable + SEO surface, so it stays minimal:

    title         — canonical page title
    description   — one-line summary (SEO meta + LLM snippet); synthesized
                    from the first paragraph by the converter
    page_id       — numeric Confluence page id (stable identity, rename-safe)
    department    — site department slug (e.g. data-ai), from sync_config
    source_url    — authoritative Confluence URL
    last_modified — YYYY-MM-DD (date only, not full ISO timestamp)
    tags          — flat list (from Confluence labels)
    audience      — [students, faculty, staff, ...] (defaulted; preserved if
                    a human edits it on disk)

Field ownership:
  Puller-owned (always overwritten on sync): title, description, page_id,
    department, source_url, last_modified, tags.
  Human/classifier-owned (preserved across re-sync if present on disk):
    audience.

Filename convention (ADR-0002): `<slug>.md` (e.g. claude-faq.md). Page id lives
in frontmatter only; `find_existing_page_file` searches by page_id so renames
are safe.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# Frontmatter schema version — bump when the set of puller-owned fields changes
# in a way that requires re-ingesting existing pages. Used by SyncState's
# `should_skip_by_version` to force backfill when prior syncs predate the
# current schema.
#  su-kb-site v1 (ADR-0002): the 8-field public schema.
FRONTMATTER_SCHEMA_VERSION = 10


# Default audience for a page when nothing on disk overrides it. The public KB
# serves the SU community by default; the converter / a human can widen it
# (e.g. add IT) based on page content.
DEFAULT_AUDIENCE: tuple[str, ...] = ("students", "faculty", "staff")


# Human/classifier-owned keys read from existing frontmatter and preserved
# across re-syncs. The puller writes the default only when the target file
# doesn't exist or the key is absent.
PRESERVED_KEYS: tuple[str, ...] = ("audience",)


# Windows-illegal char map (used for the source-side title sanitization that a
# few callers still rely on; the canonical filename is slug-based, below).
_SANITIZE_MAP = {
    ":": "_",
    "/": "-",
    "\\": "-",
    "?": "",
    "*": "",
    '"': "'",
    "<": "(",
    ">": ")",
    "|": "-",
}


def sanitize_filename_title(title: str) -> str:
    out = title or "untitled"
    for ch, repl in _SANITIZE_MAP.items():
        out = out.replace(ch, repl)
    out = re.sub(r"\s+", " ", out).strip().strip(".")
    return out or "untitled"


def slugify(title: str) -> str:
    """Lowercase, kebab-case slug derived from a title (ADR-0002).

    "Claude — Frequently Asked Questions" → "claude-frequently-asked-questions".
    Non-alphanumerics collapse to single hyphens; leading/trailing hyphens
    trimmed. Empty input yields "untitled".
    """
    s = (title or "").lower()
    # Normalize common unicode dashes to ascii so they collapse cleanly.
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "untitled"


def canonical_filename(title: str) -> str:
    """`<slug>.md` (ADR-0002). Page id lives in frontmatter, not the filename."""
    return f"{slugify(title)}.md"


def content_hash(body_markdown: str) -> str:
    h = hashlib.sha256(body_markdown.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def _date_only(iso_timestamp: str) -> str:
    """Reduce an ISO 8601 timestamp to a YYYY-MM-DD date string.

    Tolerant: returns "" for empty input, and falls back to the leading 10
    chars if the value isn't parseable but looks date-shaped.
    """
    if not iso_timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except ValueError:
        return iso_timestamp[:10] if len(iso_timestamp) >= 10 else iso_timestamp


@dataclass
class PageMeta:
    """All data needed to build the 8-field frontmatter for one page."""

    page_id: str
    title: str
    source_url: str
    department: str
    description: str = ""
    ancestor_path: list[str] = field(default_factory=list)
    last_modified: str = ""  # ISO 8601 UTC; reduced to YYYY-MM-DD on write
    labels: list[str] = field(default_factory=list)


def find_existing_page_file(space_root: Path, page_id: str) -> Path | None:
    """Locate an existing markdown file whose frontmatter carries `page_id`.

    Rename-safe: the slug-based filename can change when a Confluence page is
    retitled, so we search by the stable `page_id` in frontmatter rather than
    by filename prefix. Returns the first match; orphan files should be cleaned
    up by the caller after a successful write.
    """
    if not space_root.exists():
        return None
    target = str(page_id)
    for md_path in space_root.rglob("*.md"):
        fm = read_existing_frontmatter(md_path)
        if fm and str(fm.get("page_id", "")) == target:
            return md_path
    return None


def read_existing_frontmatter(target_path: Path) -> dict[str, Any] | None:
    """Parse the YAML frontmatter block from an existing markdown file.

    Returns the parsed dict, or None if the file is absent, has no frontmatter,
    or the frontmatter block is malformed. Used to preserve human-owned keys
    (audience) across re-syncs and to find a page by id.
    """
    if not target_path.exists():
        return None
    try:
        text = target_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    yaml_text = text[4:end + 1]
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def merge_preserved_keys(
    new_fm: dict[str, Any],
    existing_fm: dict[str, Any] | None,
) -> dict[str, Any]:
    """Preserve human/classifier-owned keys (audience) from existing frontmatter.

    A human may have narrowed/widened the audience on disk; that edit survives
    re-sync. New pages (existing_fm is None) keep the puller default.
    """
    if not existing_fm:
        return new_fm
    for key in PRESERVED_KEYS:
        if key in existing_fm:
            new_fm[key] = existing_fm[key]
    return new_fm


def build_frontmatter(
    meta: PageMeta,
    existing_frontmatter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the 8-field frontmatter dict. Field order is the emit order."""
    new_fm: dict[str, Any] = {
        "title": meta.title,
        "description": meta.description or "",
        "page_id": str(meta.page_id),
        "department": meta.department,
        "source_url": meta.source_url,
        "last_modified": _date_only(meta.last_modified),
        "tags": list(meta.labels),
        "audience": list(DEFAULT_AUDIENCE),
    }
    return merge_preserved_keys(new_fm, existing_frontmatter)


def serialize(fm: dict[str, Any]) -> str:
    """Emit the YAML frontmatter block (with --- delimiters + trailing newline)."""
    body = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{body}---\n"


# Required fields — must be present and non-empty for a valid page.
# `tags` and `audience` may legitimately be empty lists, so they're not
# required-non-empty. `description` is synthesized and should be present, but a
# genuinely empty page can have an empty description, so it's not gated here.
REQUIRED_FIELDS = (
    "title",
    "page_id",
    "department",
    "source_url",
    "last_modified",
)


def validate(fm: dict[str, Any]) -> list[str]:
    """Return a list of missing-required-field errors. Empty = valid.

    A field is "missing" if it's None, an empty string, or absent.
    """
    return [
        f for f in REQUIRED_FIELDS
        if f not in fm or fm[f] is None or fm[f] == ""
    ]
