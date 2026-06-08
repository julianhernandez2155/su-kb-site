#!/usr/bin/env python3
"""Native-aware frontmatter validator for su-kb-site (the publish gate).

One validator for the whole corpus. The site has two kinds of page:

  * `origin: confluence` — seeded by the export tool; carries `page_id` +
    `source_url` (a Confluence identity).
  * `origin: native`     — authored directly in Markdown here; has NO `page_id`
    and NO `source_url`.

A correctly-drafted native page would FAIL the export tool's validator (which
requires `page_id`/`source_url`), so this module reconciles the two under one
set of rules without weakening the export path — it does NOT import or modify
`export-tool` (P6: no cross-package coupling). See `eng.md` §2 for the design.

Used by `.github/workflows/validate-content.yaml` to fail a PR closed when a
content page is malformed or unsafe. Also runnable locally:

    python tools/check_frontmatter.py site/content/        # whole corpus
    python tools/check_frontmatter.py path/to/page.md      # one file
    python tools/check_frontmatter.py --changed-only changed.txt   # CI diff

Thin by design: stdlib + pyyaml only (pyyaml is already a renderer dependency).
Exit 0 iff every file passed; 1 if any file failed; 2 on a usage error. Any
non-zero exit fails CI closed.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# kb_config lives alongside this script in tools/. Make the import work whether
# run as `python tools/check_frontmatter.py` (script dir is on sys.path) or
# imported by pytest from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_config import DEPT_LABELS  # noqa: E402


# --- single sources of truth, re-derived locally (see eng.md §2.5) -----------
#
# These two helpers are a deliberate ~15-line copy of the logic in
# `export-tool/src/su_kb_export/frontmatter.py`. We copy rather than import
# across the export package boundary (P6). The slugify drift guard in
# `test_check_frontmatter.py` asserts this copy stays byte-identical to the
# export source of truth, so the duplication cannot silently diverge.

def slugify(title: str) -> str:
    """Lowercase kebab-case slug from a title. MUST match export's slugify.

    "Claude — Frequently Asked Questions" -> "claude-frequently-asked-questions".
    """
    s = (title or "").lower()
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "untitled"


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_VALID_ORIGINS = ("native", "confluence")
_ALLOWED_AUDIENCE = {"students", "faculty", "staff", "IT"}


# --- frontmatter parsing -----------------------------------------------------

def _split_frontmatter(text: str) -> str | None:
    """Return the YAML frontmatter text, or None if the block is absent.

    Mirrors the renderer's parse convention exactly (`render.py:read_page`):
    a file starts with `---` and the frontmatter is the slice up to the second
    `---`. "What validates" therefore == "what renders".
    """
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def _is_empty(value: Any) -> bool:
    """A field is 'empty' if absent (None) or an empty/whitespace string."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _resolve_origin(fm: dict[str, Any]) -> str:
    """Resolve page origin: explicit `origin:` → page_id inference → native."""
    origin = fm.get("origin")
    if isinstance(origin, str) and origin.strip():
        return origin.strip()
    if not _is_empty(fm.get("page_id")):
        return "confluence"
    return "native"


def _valid_date(value: Any) -> bool:
    """Accept a `YYYY-MM-DD` string OR a PyYAML-parsed `datetime.date`.

    Unquoted `last_modified: 2026-06-08` is loaded by PyYAML as a `date`;
    quoted `'2026-06-08'` stays a string. Both are valid (eng.md §3).
    """
    if isinstance(value, date):  # datetime.date (and datetime, a subclass)
        return True
    if isinstance(value, str) and _DATE_RE.match(value):
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


# --- the validator core ------------------------------------------------------

def validate_text(text: str, filename: str) -> list[str]:
    """Validate one page's frontmatter. Returns a list of error strings.

    Empty list == valid. Each error is `CODE message`. `filename` is used for
    the slug/filename match check (native pages only).
    """
    fm_text = _split_frontmatter(text)
    if fm_text is None:
        return ["E_NO_FRONTMATTER no leading '---' frontmatter block"]

    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0] if str(exc) else "unparseable"
        return [f"E_BAD_YAML frontmatter is not valid YAML: {first}"]
    if not isinstance(parsed, dict):
        return ["E_BAD_YAML frontmatter did not parse to a mapping"]

    fm = parsed
    errors: list[str] = []

    # origin must be valid if explicitly present.
    raw_origin = fm.get("origin")
    if isinstance(raw_origin, str) and raw_origin.strip() and raw_origin.strip() not in _VALID_ORIGINS:
        errors.append(
            f"E_BAD_ORIGIN origin must be one of {_VALID_ORIGINS}, got {raw_origin.strip()!r}"
        )
    origin = _resolve_origin(fm)

    # --- checks common to both origins ---
    if _is_empty(fm.get("title")):
        errors.append("E_MISSING_TITLE title is required and must be non-empty")

    dept = fm.get("department")
    if _is_empty(dept):
        errors.append("E_BAD_DEPT department is required and must be non-empty")
    elif dept not in DEPT_LABELS:
        errors.append(
            f"E_BAD_DEPT department {dept!r} is not a known department "
            f"(allowed: {sorted(DEPT_LABELS)})"
        )

    if not _valid_date(fm.get("last_modified")):
        errors.append(
            "E_BAD_DATE last_modified must be a YYYY-MM-DD date "
            f"(got {fm.get('last_modified')!r})"
        )

    # visibility: required == public for native; for confluence a MISSING value
    # is treated as public (lazy backfill, eng.md §3.1) but a PRESENT wrong
    # value still fails.
    visibility = fm.get("visibility")
    if origin == "native":
        if visibility != "public":
            errors.append(
                f"E_BAD_VISIBILITY visibility must be 'public' (got {visibility!r})"
            )
    else:  # confluence
        if visibility is not None and visibility != "public":
            errors.append(
                f"E_BAD_VISIBILITY visibility must be 'public' if present (got {visibility!r})"
            )

    # tags shape: if present, a list of non-empty strings (empty list OK).
    tags = fm.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or any(
            not isinstance(t, str) or t.strip() == "" for t in tags
        ):
            errors.append("E_BAD_TAGS tags must be a list of non-empty strings")

    # audience shape/values: if present, a list subset of the allowed set.
    audience = fm.get("audience")
    if audience is not None:
        if not isinstance(audience, list) or any(not isinstance(a, str) for a in audience):
            errors.append("E_BAD_AUDIENCE audience must be a list of strings")
        else:
            unknown = [a for a in audience if a not in _ALLOWED_AUDIENCE]
            if unknown:
                errors.append(
                    f"E_BAD_AUDIENCE audience has unknown value(s) {unknown} "
                    f"(allowed: {sorted(_ALLOWED_AUDIENCE)})"
                )

    # --- origin-specific checks ---
    if origin == "confluence":
        if _is_empty(fm.get("page_id")):
            errors.append("E_MISSING_CONFLUENCE_FIELD confluence page requires non-empty page_id")
        if _is_empty(fm.get("source_url")):
            errors.append("E_MISSING_CONFLUENCE_FIELD confluence page requires non-empty source_url")
    else:  # native
        if _is_empty(fm.get("description")):
            errors.append("E_MISSING_DESC native page requires a non-empty description")
        if not _is_empty(fm.get("page_id")):
            errors.append(
                "E_NATIVE_HAS_CONFLUENCE_FIELD native page must NOT carry page_id "
                "(did you paste an exported page's header?)"
            )
        if not _is_empty(fm.get("source_url")):
            errors.append(
                "E_NATIVE_HAS_CONFLUENCE_FIELD native page must NOT carry source_url "
                "(did you paste an exported page's header?)"
            )
        # slug/filename match — native only (authors hand-type the filename in
        # the GitHub UI; exported filenames are slug-built by construction).
        title = fm.get("title")
        if isinstance(title, str) and title.strip():
            stem = Path(filename).stem
            expected = slugify(title)
            if stem != expected:
                errors.append(
                    f"E_SLUG_MISMATCH filename stem {stem!r} != slugify(title) {expected!r} "
                    f"(rename the file to {expected}.md)"
                )

    return errors


def validate_file(path: str | Path) -> list[str]:
    """Validate one markdown file by path. Returns error strings (empty=valid)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"E_UNREADABLE could not read file: {exc}"]
    return validate_text(text, p.name)


# --- CLI ---------------------------------------------------------------------

def _iter_md_paths(paths: list[str]) -> list[Path]:
    """Expand args (files or dirs) into a sorted list of *.md files."""
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md":
            out.append(p)
    return out


def _changed_only_paths(list_file: str) -> list[Path]:
    """Read newline-delimited paths; keep only site/content/**.md that exist."""
    out: list[Path] = []
    try:
        lines = Path(list_file).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"usage error: cannot read --changed-only file {list_file!r}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    for line in lines:
        rel = line.strip()
        if not rel or not rel.endswith(".md"):
            continue
        # normalize separators; only validate content pages that still exist.
        norm = rel.replace("\\", "/")
        if "site/content/" not in norm:
            continue
        p = Path(rel)
        if p.exists():
            out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate su-kb-site content frontmatter (the publish gate)."
    )
    parser.add_argument(
        "paths", nargs="*",
        help="markdown files or directories. No args → validate site/content/**/*.md",
    )
    parser.add_argument(
        "--changed-only", metavar="FILE",
        help="read newline-delimited changed paths; validate only site/content/*.md among them",
    )
    parser.add_argument("--quiet", action="store_true", help="print only failures")
    args = parser.parse_args(argv)

    if args.changed_only:
        targets = _changed_only_paths(args.changed_only)
    elif args.paths:
        targets = _iter_md_paths(args.paths)
    else:
        targets = sorted(Path("site/content").rglob("*.md"))

    if not targets:
        # Nothing to validate is a pass (e.g. a PR that touched no content md).
        if not args.quiet:
            print("0 files, 0 passed, 0 failed (nothing to validate)")
        return 0

    failed = 0
    for path in targets:
        errors = validate_file(path)
        if errors:
            failed += 1
            for err in errors:
                print(f"FAIL {path}: {err}")
        elif not args.quiet:
            print(f"OK   {path}")

    total = len(targets)
    print(f"{total} files, {total - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
