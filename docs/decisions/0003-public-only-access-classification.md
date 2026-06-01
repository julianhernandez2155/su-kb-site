---
status: accepted
date: 2026-06-01
supersedes:
deciders: Julian Hernandez
---

# 0003. Public-only publication via export-time access classification

## Context

The site is served on GitHub Pages (free plan → public repo), so it is world-readable and
its git history is public. [ADR-0002](0002-pivot-from-quartz-to-thin-renderer.md) simplified
the frontmatter to 8 fields and dropped all access-classification fields, and BUILD-REPORT
recorded the MVP posture as "public-only, no app-level access control; the real boundary is
Confluence-side RBAC upstream." That posture was never enforced in code: the export tool has
**no access check at all** — it exports every page the sync user's account can read. Restricted
pages stay off the site only because a *name-based* content-quality filter happens to match them
(`(Test)`, `Summer Intern 2026`) — coincidence, not enforcement.

The ITSAI space is **not** entirely public — it contains read-restricted pages (the prior
`su-kb-pipeline` project proved this and built a working read-restriction classifier; ADRs
0007–0009 there). Any restricted page whose name doesn't match the exclusion list would publish
to the open internet.

Two hard constraints frame the options: a public repo exposes everything in it (history
included), and a static site cannot authenticate users. So per-user / per-department RBAC is
impossible on this surface by construction.

## Decision

**The site is public-only, enforced by an export-time access classifier.**

- At export, classify each Confluence page by its read-restrictions (direct + inherited). Publish
  **only** pages with no read restriction. Restricted pages are skipped — not written, not
  committed, not retained in this repo.
- Salvage the binary read-restriction detector from `su-kb-pipeline`'s `restrictions.py` /
  `access.py`, scoped down to `is_public(page) -> bool` (drop the RBAC-metadata / space-category
  machinery — not needed for public-only).
- Add a build-time **leak guard**: the build fails if any page classified restricted is found in
  `site/content/`.
- The name-based filter is demoted to what it is — a content-quality gate for drafts; access
  restriction becomes the real gate (exclude if restricted **or** draft).

RBAC, an authenticated surface for restricted content, and a "departments author markdown →
auto-sync" tool are explicitly **Phase 2** — they need SU infra + SSO and converge with the old
`su-kb-pipeline` access work. Execution plan: [../plan-public-only-access.md](../plan-public-only-access.md).

## Consequences

### Positive
- A real technical guarantee that restricted content never reaches the public site — replaces the
  name-match luck the site relied on.
- Matches the world-readable reality of the deployment surface.
- Keeps the demo simple: one tier, a binary classification, no auth/infra.

### Negative
- Restricted content is not retained here, so there's no head start for a future RBAC tier in this
  repo (deliberate — public-only means don't store it).
- Re-running the export to apply classification needs the Atlassian token (end-user-simulation,
  user-gated).
- The classifier adds a read-restriction API call per page; `/restriction/byOperation` pagination
  is unverified above ITSAI's size (fine for the demo; flagged for larger spaces).

### Neutral
- Folder hierarchy is unchanged — pages are classified and skipped in place, never relocated.
- The 8-field schema is unchanged — classification uses live Confluence API data at export, not
  stored frontmatter fields.

## Alternatives considered
- **Hybrid now (public static site + authenticated RBAC tier).** Rejected for the demo: a static
  site can't authenticate, so RBAC needs a separate dynamic surface on SU infra + SSO + an
  identity bridge. Too large for the internship demo; deferred to Phase 2.
- **Keep the name-based filter only.** Rejected: it's coincidental overlap, not enforcement — a
  restricted page not matching the name list leaks.
- **Pull and retain restricted pages locally / in a private repo for future RBAC.** Considered
  (the "keep them for flexibility" idea) but deferred: public-only means we don't store restricted
  content at all right now.
