"""Export-time read-restriction classifier — public-only gate (ADR-0003).

The site is public-only: a page is publishable **iff** it has no Confluence
read restriction, neither directly on the page nor inherited from any ancestor.
This module is the binary salvage of su-kb-pipeline's restriction subsystem
(`restrictions.py` + `access.py`), scoped down to a single question:

    is_public(page) -> bool

Everything else from the prior project — space-audience categories, the
broadly-accessible-space allowlist, the RBAC ``visibility_signal`` vocabulary,
the access frontmatter fields — is intentionally dropped (ADR-0003,
"don't over-salvage"). Public-only needs only the binary read check.

Conservatism (leak-proof default)
----------------------------------
If the restriction check cannot complete — an API error on the page itself or
on any ancestor — the page is treated as **NOT public** (reason
``access-check-failed``). We never publish a page we cannot prove is
unrestricted: an over-skip is recoverable, a leak to the open internet is not.
A token that lacks permission to read restrictions therefore fails *closed* —
every page is skipped, which is loud and obvious (0 pages published), not
silent.

Where the data comes from
--------------------------
Read restrictions come from the Confluence v1 endpoint:

    GET /wiki/rest/api/content/{id}/restriction/byOperation

which returns **direct** (non-inherited) restrictions only. Inherited
restrictions are detected by walking the page's ancestor chain and calling the
same endpoint on each ancestor. Ancestor results are cached per run (a shared
parent folder is checked once, not once per child).

Depends only on ``httpx`` (matching the rest of the export tool).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class AccessResult:
    """Outcome of one page's public-only classification.

    ``reason`` is ``None`` when the page is public; otherwise it is the
    exclusion-report category (``read-restricted`` or ``access-check-failed``).
    ``restricted_by`` lists the page/ancestor ids carrying the restriction
    (ids only — never page content), for the exclusion paper trail.
    """

    is_public: bool
    reason: str | None = None
    restricted_by: list[str] = field(default_factory=list)
    error: str | None = None


def v1_rest_base_from_v2(v2_base: str) -> str:
    """Derive the v1 REST base from the puller's v2 ``api_base``.

    The byOperation restriction endpoint only exists on the v1 REST API, so we
    rewrite the gateway-resolved v2 base to its v1 sibling.

    Examples
    --------
    >>> v1_rest_base_from_v2("https://api.atlassian.com/ex/confluence/abc/wiki/api/v2")
    'https://api.atlassian.com/ex/confluence/abc/wiki/rest/api'
    >>> v1_rest_base_from_v2("https://su-jsm.atlassian.net/wiki/api/v2")
    'https://su-jsm.atlassian.net/wiki/rest/api'
    """
    base = v2_base.rstrip("/")
    if base.endswith("/wiki/api/v2"):
        return base[: -len("/wiki/api/v2")] + "/wiki/rest/api"
    # Fallback: split on /wiki/ and rebuild.
    host = base.split("/wiki/")[0]
    return host + "/wiki/rest/api"


def read_restriction_present(payload: dict[str, Any]) -> bool:
    """True iff a ``/restriction/byOperation`` response shows a *read* restriction.

    The v1 byOperation response shape (observed 2026-05-19 in su-kb-pipeline)::

        {"read":   {"restrictions": {"user":  {"results": [...], "size": N},
                                     "group": {"results": [...], "size": M}}},
         "update": {"restrictions": {...}}}

    ``size > 0`` on either the user or group bucket of the ``read`` operation
    means the page is locked to a subset → restricted. Only the ``read``
    operation governs visibility; ``update`` restrictions don't affect who can
    read, so they're ignored here. Prefers the API's explicit ``size`` field
    and falls back to ``len(results)``.
    """
    read_obj = payload.get("read") or {}
    restrictions = read_obj.get("restrictions") or {}
    user_obj = restrictions.get("user") or {}
    group_obj = restrictions.get("group") or {}

    user_size = user_obj.get("size")
    if not isinstance(user_size, int):
        user_size = len(user_obj.get("results") or [])
    group_size = group_obj.get("size")
    if not isinstance(group_size, int):
        group_size = len(group_obj.get("results") or [])

    return bool(user_size or group_size)


def _fetch_read_restricted(puller: Any, entity_id: str) -> tuple[bool | None, str | None]:
    """Fetch direct read-restriction state for one entity (page or ancestor).

    Returns ``(has_read_restriction, error)``. ``has_read_restriction`` is
    ``None`` when the check errored — callers must treat that as "cannot prove
    public", not as "clean". Shares the puller's authenticated client, 429
    backoff, and rate limit via ``puller._get``.
    """
    v1_base = v1_rest_base_from_v2(puller.api_base)
    url = f"{v1_base}/content/{entity_id}/restriction/byOperation"
    try:
        payload = puller._get(url)
    except httpx.HTTPStatusError as e:
        return None, f"HTTP {e.response.status_code} on byOperation for {entity_id}"
    except httpx.HTTPError as e:
        return None, f"network error on byOperation for {entity_id}: {e}"
    return read_restriction_present(payload), None


class AncestorRestrictionCache:
    """Per-run cache of ancestor read-restriction checks.

    A corpus with a shared 'AI Workspace' parent folder should make one
    restriction call for that ancestor, not one per child. The puller builds a
    single instance per ``pull_space`` and passes it to every classification.
    """

    def __init__(self, puller: Any) -> None:
        self.puller = puller
        self._cache: dict[str, tuple[bool | None, str | None]] = {}

    def is_restricted(self, entity_id: str) -> tuple[bool | None, str | None]:
        if entity_id not in self._cache:
            self._cache[entity_id] = _fetch_read_restricted(self.puller, entity_id)
        return self._cache[entity_id]


def classify_page_access(
    puller: Any,
    page: dict[str, Any],
    cache: AncestorRestrictionCache,
) -> AccessResult:
    """Classify one page for public-only publication.

    ``page`` is a v2 page dict (needs ``id`` and, for inheritance, ``parentId``).
    Checks the page's direct read restriction, then — if it has a parent — walks
    its ancestors and checks each (cached). Any error short-circuits to
    ``access-check-failed`` (not public).
    """
    page_id = str(page.get("id") or "")

    direct, err = _fetch_read_restricted(puller, page_id)
    if err is not None:
        return AccessResult(False, "access-check-failed", error=err)
    if direct:
        return AccessResult(False, "read-restricted", restricted_by=[page_id])

    # Top-level page: no ancestors, no inheritance to check. Avoids an ancestors
    # call for pages that can't inherit a restriction.
    parent_id = str(page.get("parentId") or "") or None
    if not parent_id:
        return AccessResult(True)

    try:
        ancestors = puller.get_page_ancestors(page_id)
    except httpx.HTTPError as e:
        return AccessResult(False, "access-check-failed", error=f"ancestors fetch failed: {e}")

    restricting: list[str] = []
    for a in ancestors:
        aid = str(a.get("id") or "")
        if not aid:
            continue
        a_restricted, a_err = cache.is_restricted(aid)
        if a_err is not None:
            return AccessResult(False, "access-check-failed", error=a_err)
        if a_restricted:
            restricting.append(aid)

    if restricting:
        return AccessResult(False, "read-restricted", restricted_by=restricting)
    return AccessResult(True)


def is_public(puller: Any, page: dict[str, Any], cache: AncestorRestrictionCache) -> bool:
    """Binary public-only gate (ADR-0003 verification checklist).

    Thin wrapper over :func:`classify_page_access` for callers/tests that only
    need the yes/no. ``False`` whenever the page is read-restricted (direct or
    inherited) *or* the restriction check could not be completed.
    """
    return classify_page_access(puller, page, cache).is_public
