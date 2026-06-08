"""Unit tests for tools/check_frontmatter.py (the publish gate validator).

Covers the 13-case matrix from eng.md §9 plus the slugify drift guard that
keeps the local slugify byte-identical to the export tool's source of truth.

Run: python -m pytest tools/test_check_frontmatter.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS_DIR)

import check_frontmatter as cf  # noqa: E402


def _codes(errors: list[str]) -> list[str]:
    """First token of each error string == its error code."""
    return [e.split(" ", 1)[0] for e in errors]


# --- frontmatter builders ----------------------------------------------------

def native_fm(**overrides: object) -> str:
    """A valid native page body. Override/remove fields via kwargs.

    Pass a field as None to DELETE it from the block (to test 'missing').
    """
    fields: dict[str, object] = {
        "title": "Onboarding Checklist",
        "description": "What a new intern should do in week one.",
        "department": "data-ai",
        "last_modified": "'2026-06-08'",  # quoted -> str
        "tags": "[onboarding, how-to]",
        "audience": "[students, faculty, staff]",
        "origin": "native",
        "visibility": "public",
    }
    fields.update(overrides)
    lines = [f"{k}: {v}" for k, v in fields.items() if v is not None]
    return "---\n" + "\n".join(lines) + "\n---\n\n# Body\n"


def confluence_fm(**overrides: object) -> str:
    fields: dict[str, object] = {
        "title": "Claude Code Setup",
        "description": "Windows setup guide.",
        "page_id": "'986841103'",
        "department": "data-ai",
        "source_url": "https://answers.atlassian.syr.edu/wiki/x/986841103",
        "last_modified": "'2026-04-15'",
        "tags": "[claude-code, setup]",
        "audience": "[students]",
    }
    fields.update(overrides)
    lines = [f"{k}: {v}" for k, v in fields.items() if v is not None]
    return "---\n" + "\n".join(lines) + "\n---\n\n# Body\n"


# --- the 13-case matrix ------------------------------------------------------

def test_valid_native_passes():
    assert cf.validate_text(native_fm(), "onboarding-checklist.md") == []


def test_native_with_page_id_fails():
    errs = cf.validate_text(native_fm(page_id="'12345'"), "onboarding-checklist.md")
    assert "E_NATIVE_HAS_CONFLUENCE_FIELD" in _codes(errs)


def test_native_missing_visibility_fails():
    errs = cf.validate_text(native_fm(visibility=None), "onboarding-checklist.md")
    assert "E_BAD_VISIBILITY" in _codes(errs)


def test_native_visibility_internal_fails():
    errs = cf.validate_text(native_fm(visibility="internal"), "onboarding-checklist.md")
    assert "E_BAD_VISIBILITY" in _codes(errs)


def test_native_missing_description_fails():
    errs = cf.validate_text(native_fm(description=None), "onboarding-checklist.md")
    assert "E_MISSING_DESC" in _codes(errs)


def test_native_slug_mismatch_fails():
    errs = cf.validate_text(native_fm(), "wrong-name.md")
    assert "E_SLUG_MISMATCH" in _codes(errs)


def test_valid_confluence_passes():
    # No visibility field — lazy backfill treats missing as public for exported.
    assert cf.validate_text(confluence_fm(), "claude-code-setup.md") == []


def test_confluence_missing_source_url_fails():
    errs = cf.validate_text(confluence_fm(source_url=None), "claude-code-setup.md")
    assert "E_MISSING_CONFLUENCE_FIELD" in _codes(errs)


def test_bad_date_format_fails():
    errs = cf.validate_text(native_fm(last_modified="2026/06/08"), "onboarding-checklist.md")
    assert "E_BAD_DATE" in _codes(errs)


def test_unquoted_date_passes():
    # Unquoted YYYY-MM-DD is parsed by PyYAML as a datetime.date — accepted.
    assert cf.validate_text(native_fm(last_modified="2026-06-08"), "onboarding-checklist.md") == []


def test_malformed_yaml_fails():
    text = '---\ntitle: "unterminated\ndepartment: data-ai\n---\n\n# Body\n'
    errs = cf.validate_text(text, "x.md")
    assert "E_BAD_YAML" in _codes(errs)


def test_no_frontmatter_fails():
    errs = cf.validate_text("# Just a heading, no frontmatter\n", "x.md")
    assert _codes(errs) == ["E_NO_FRONTMATTER"]


def test_unknown_audience_fails():
    errs = cf.validate_text(native_fm(audience="[students, alumni]"), "onboarding-checklist.md")
    assert "E_BAD_AUDIENCE" in _codes(errs)


def test_unknown_department_fails():
    errs = cf.validate_text(native_fm(department="data_ai"), "onboarding-checklist.md")
    assert "E_BAD_DEPT" in _codes(errs)


# --- extra origin-resolution coverage ---------------------------------------

def test_native_inferred_when_no_origin_no_page_id():
    # No explicit origin, no page_id -> native branch -> description required.
    errs = cf.validate_text(native_fm(origin=None, description=None), "onboarding-checklist.md")
    assert "E_MISSING_DESC" in _codes(errs)


def test_bad_origin_value_fails():
    errs = cf.validate_text(native_fm(origin="external"), "onboarding-checklist.md")
    assert "E_BAD_ORIGIN" in _codes(errs)


# --- slugify drift guard -----------------------------------------------------

def test_slugify_matches_export_source_of_truth():
    """Local slugify MUST stay byte-identical to export-tool's slugify."""
    export_src = os.path.normpath(
        os.path.join(_THIS_DIR, "..", "export-tool", "src")
    )
    sys.path.insert(0, export_src)
    try:
        from su_kb_export.frontmatter import slugify as export_slugify
    except ImportError:
        pytest.skip("export-tool not importable; drift guard skipped")

    fixtures = [
        "Claude — Frequently Asked Questions",
        "Claude Code Setup",
        "AI / ML at SU: an Overview",
        "  Leading and trailing   ",
        "Résumé tips & tricks!!!",
        "",
        "---",
        "MixedCase With  Multiple   Spaces",
        "Already-kebab-case",
        "Numbers 123 and symbols #$%",
    ]
    for title in fixtures:
        assert cf.slugify(title) == export_slugify(title), f"drift on {title!r}"
