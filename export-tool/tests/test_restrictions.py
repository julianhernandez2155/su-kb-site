"""Public-only access classifier — fixtures for restricted / public / inherited.

Network-free: a FakePuller returns canned `/restriction/byOperation` payloads
keyed by entity id, so the classifier logic is exercised without touching
Confluence. Mirrors the salvage source's restriction tests, scoped to the
binary `is_public` question (ADR-0003).
"""

from __future__ import annotations

import re
from pathlib import Path

import httpx

from su_kb_export.puller import _scan_for_restricted_pages, _write_exclusions_report
from su_kb_export.restrictions import (
    AncestorRestrictionCache,
    classify_page_access,
    is_public,
    read_restriction_present,
    v1_rest_base_from_v2,
)

# The 3 known read-restricted Summer-Intern pages (plan §Stage 6 / checklist).
RESTRICTED_INTERN_IDS = ["1068171339", "1069318154", "1069350926"]

_RESTRICTED_READ = {
    "read": {"restrictions": {
        "user": {"results": [{"accountId": "abc"}], "size": 1},
        "group": {"results": [], "size": 0},
    }}
}
_CLEAN_READ = {
    "read": {"restrictions": {
        "user": {"results": [], "size": 0},
        "group": {"results": [], "size": 0},
    }}
}


class FakePuller:
    """Stand-in for ConfluencePuller: serves restriction + ancestor data locally."""

    def __init__(self, *, restricted=(), errors=(), ancestors=None):
        self.api_base = "https://su-jsm.atlassian.net/wiki/api/v2"
        self.restricted = {str(x) for x in restricted}
        self.errors = {str(x) for x in errors}
        self._ancestors = {str(k): [str(a) for a in v] for k, v in (ancestors or {}).items()}
        self.byop_calls: list[str] = []  # entity ids whose byOperation was fetched

    def _get(self, url: str, params=None):
        m = re.search(r"/content/([^/]+)/restriction/byOperation", url)
        assert m, f"unexpected URL: {url}"
        entity_id = m.group(1)
        self.byop_calls.append(entity_id)
        if entity_id in self.errors:
            req = httpx.Request("GET", url)
            resp = httpx.Response(403, request=req)
            raise httpx.HTTPStatusError("403 Forbidden", request=req, response=resp)
        return _RESTRICTED_READ if entity_id in self.restricted else _CLEAN_READ

    def get_page_ancestors(self, page_id: str):
        return [{"id": a} for a in self._ancestors.get(str(page_id), [])]


# --- read_restriction_present --------------------------------------------------

def test_read_restriction_present_clean():
    assert read_restriction_present(_CLEAN_READ) is False
    assert read_restriction_present({}) is False


def test_read_restriction_present_user_or_group():
    assert read_restriction_present(_RESTRICTED_READ) is True
    group_only = {"read": {"restrictions": {"group": {"results": [{"id": "g"}], "size": 1}}}}
    assert read_restriction_present(group_only) is True


def test_read_restriction_present_size_falls_back_to_len():
    no_size = {"read": {"restrictions": {"user": {"results": [{"accountId": "a"}]}}}}
    assert read_restriction_present(no_size) is True


def test_update_restriction_does_not_count_as_read():
    # Only `read` governs visibility; an update-only restriction is still public.
    update_only = {"update": {"restrictions": {"user": {"results": [{"accountId": "a"}], "size": 1}}}}
    assert read_restriction_present(update_only) is False


# --- v1 base derivation --------------------------------------------------------

def test_v1_rest_base_from_v2():
    assert (v1_rest_base_from_v2("https://su-jsm.atlassian.net/wiki/api/v2")
            == "https://su-jsm.atlassian.net/wiki/rest/api")
    assert (v1_rest_base_from_v2("https://api.atlassian.com/ex/confluence/abc/wiki/api/v2")
            == "https://api.atlassian.com/ex/confluence/abc/wiki/rest/api")


# --- classify_page_access / is_public ------------------------------------------

def test_public_top_level_page():
    puller = FakePuller()
    page = {"id": "100"}
    result = classify_page_access(puller, page, AncestorRestrictionCache(puller))
    assert result.is_public is True
    assert result.reason is None
    assert is_public(puller, page, AncestorRestrictionCache(puller)) is True


def test_direct_restriction_blocks():
    puller = FakePuller(restricted={"200"})
    page = {"id": "200"}
    result = classify_page_access(puller, page, AncestorRestrictionCache(puller))
    assert result.is_public is False
    assert result.reason == "read-restricted"
    assert result.restricted_by == ["200"]


def test_inherited_restriction_blocks():
    # Page itself is clean, but an ancestor folder is read-restricted.
    puller = FakePuller(restricted={"ANC"}, ancestors={"300": ["ANC"]})
    page = {"id": "300", "parentId": "ANC"}
    result = classify_page_access(puller, page, AncestorRestrictionCache(puller))
    assert result.is_public is False
    assert result.reason == "read-restricted"
    assert result.restricted_by == ["ANC"]


def test_clean_ancestor_chain_is_public():
    puller = FakePuller(ancestors={"400": ["P1", "P2"]})
    page = {"id": "400", "parentId": "P1"}
    assert is_public(puller, page, AncestorRestrictionCache(puller)) is True


def test_three_known_restricted_intern_pages_are_not_public():
    puller = FakePuller(restricted=set(RESTRICTED_INTERN_IDS))
    cache = AncestorRestrictionCache(puller)
    for pid in RESTRICTED_INTERN_IDS:
        assert is_public(puller, {"id": pid}, cache) is False, pid


def test_access_check_failure_is_conservative():
    # An API error on the page must NOT publish — fail closed.
    puller = FakePuller(errors={"500"})
    result = classify_page_access(puller, {"id": "500"}, AncestorRestrictionCache(puller))
    assert result.is_public is False
    assert result.reason == "access-check-failed"
    assert result.error


def test_ancestor_error_is_conservative():
    puller = FakePuller(errors={"ANCERR"}, ancestors={"600": ["ANCERR"]})
    result = classify_page_access(puller, {"id": "600", "parentId": "ANCERR"},
                                  AncestorRestrictionCache(puller))
    assert result.is_public is False
    assert result.reason == "access-check-failed"


def test_ancestor_cache_dedupes_shared_parent():
    # Two siblings under the same clean ancestor → ancestor checked once.
    puller = FakePuller(ancestors={"a": ["SHARED"], "b": ["SHARED"]})
    cache = AncestorRestrictionCache(puller)
    classify_page_access(puller, {"id": "a", "parentId": "SHARED"}, cache)
    classify_page_access(puller, {"id": "b", "parentId": "SHARED"}, cache)
    assert puller.byop_calls.count("SHARED") == 1


# --- leak guard + exclusion report (puller helpers) ----------------------------

def _write_page(root: Path, pid: str) -> Path:
    p = root / f"{pid}.md"
    p.write_text(f"---\npage_id: '{pid}'\ntitle: P{pid}\n---\nbody\n", encoding="utf-8")
    return p


def test_scan_for_restricted_pages_detects_leak(tmp_path: Path):
    _write_page(tmp_path, "777")  # restricted, should NOT be on disk
    _write_page(tmp_path, "888")  # public, fine
    leaked = _scan_for_restricted_pages(tmp_path, {"777"})
    assert leaked == ["777"]


def test_scan_for_restricted_pages_clean(tmp_path: Path):
    _write_page(tmp_path, "888")
    assert _scan_for_restricted_pages(tmp_path, {"777"}) == []
    assert _scan_for_restricted_pages(tmp_path, set()) == []


def test_exclusions_report_roundtrip(tmp_path: Path):
    import json

    report = tmp_path / ".last-exclusions.jsonl"
    rows = [
        {"page_id": "1", "title": "Secret", "reason": "read-restricted", "restricted_by": ["1"]},
        {"page_id": "2", "title": "(Test) Draft", "reason": "draft", "detail": "title prefix '(Test)'"},
    ]
    _write_exclusions_report(report, rows)
    parsed = [json.loads(line) for line in report.read_text(encoding="utf-8").splitlines()]
    assert parsed == rows
    # Paper trail carries titles + ids + reason only — never page body.
    assert all(set(r) <= {"page_id", "title", "reason", "restricted_by", "detail"} for r in parsed)
