# Plan — Public-only access classification at export

_Created 2026-06-01. Cold-executable in a fresh session._

## Goal

Make the export tool **only ever publish pages that are public** (no Confluence read
restrictions). Today the export has **no real access check** — restricted pages (e.g. Summer
Intern, Test) stay off the site only by a lucky **name-match** in the content-quality filter.
This plan replaces that luck with a real classifier.

**Decision (this supersedes part of [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md)):**
the site is **public-only**. No private tier, no RBAC, no second repo, no auth. A page is either
publishable (no read restriction) or skipped. RBAC / an authenticated surface for restricted
content is an explicit **Phase 2**, not now (a static site cannot authenticate users — that needs
a separate dynamic surface on SU infra; revisit with Aaron later).

## Why public-only (context for the executor)

- GitHub Pages is static: it serves identical bytes to everyone, no login, no per-user content.
  So RBAC is impossible *on this surface* by construction.
- A public GitHub repo exposes everything in it, **including git history** — so a restricted page
  must never be committed at all, not merely "not rendered."
- Therefore: classify at export, write only public pages, never store restricted content here.

## Pre-flight

1. Read [docs/STATUS.md](STATUS.md) and this plan.
2. Read the prior project's working classifier — it's the salvage source:
   - `../su-kb-pipeline/src/sukb/ingest/restrictions.py`
   - `../su-kb-pipeline/src/sukb/ingest/access.py`
   - `../su-kb-pipeline/src/sukb/ingest/spaces.py`
   - ADRs `../su-kb-pipeline/docs/decisions/0007-…`, `0008-…`, `0009-…` (rationale).
3. **API-spend gate:** salvaging + wiring + testing the code needs **no network**. Only Stage 6
   (the live re-export) uses the Atlassian token = end-user-simulation. Do NOT run Stage 6 without
   Julian's explicit go-ahead.
4. **Don't modify** anything under `../su-kb-pipeline/` — copy modules in, edit the copies.

## Stages

### Stage 1 — Salvage the classifier (code, no API)
Copy the read-restriction detection from `su-kb-pipeline` into
`export-tool/src/su_kb_export/restrictions.py` (+ whatever minimal helper from `access.py`/
`spaces.py` it needs). Adapt imports to the `su_kb_export` package and its `SyncConfig`. Scope it
**down to a binary**: `is_public(page) -> bool` (no read restriction, direct or inherited). Drop
the space-categories / broadly-accessible-spaces / RBAC-metadata machinery — not needed for
public-only. Keep it dependency-light (httpx only, matching the rest of the tool).

### Stage 2 — Wire into the puller (code, no API)
In `puller.py`, classify each page during the pull and **emit only public pages** to
`site/content/`. A restricted page is skipped — not written to disk. Read restrictions come from
the Confluence `/restriction/byOperation/read` data (+ ancestor inheritance) the puller already
has access to. Make the gate stack with the existing content-quality filter: **exclude if
restricted OR draft (`(Test)` etc.)**.

### Stage 3 — Exclusion report (code, no API)
Emit a small manifest of skipped pages — `page_id`, `title`, `reason` (`read-restricted` /
`draft`). **Titles + IDs only, never content.** Write it next to the export output (e.g.
`export-tool/.last-exclusions.jsonl`, gitignored) and print a summary line. This is the paper
trail proving the gate worked.

### Stage 4 — Demote the name filter (code, no API)
Reframe `config.exclusion_reason()` as a content-quality gate only (drafts), now that access is
the real gate. Update the docstring + `export-tool/CONTEXT.md` so the two gates' roles are clear.

### Stage 5 — Leak guard (code, no API)
Add a cheap assertion that **fails the build** if a page classified restricted is ever found in
`site/content/`. Put it in the export summary AND in `tools/render.py` / CI (defense in depth) so
a future misroute can't silently publish. Mirror the spirit of su-kb-pipeline's read-path filter.

### Stage 6 — Live re-export + verify (NEEDS JULIAN'S OK + token; end-user-simulation)
With `ATLASSIAN_EMAIL`/`ATLASSIAN_TOKEN` set: re-run `python export-tool/scripts/export_space.py
ITSAI`. Then:
- Confirm the 3 known restricted Summer-Intern pages (`1068171339`, `1069318154`, `1069350926`)
  are in the exclusion report and absent from `site/content/`.
- **Verify the 29 currently-published pages are all classified public** (catch anything that
  slipped in under the old name-only filter). Diff the new `site/content/` against the committed set.
- Review the exclusion report for surprises.

### Stage 7 — Triage uncommitted content + commit + push
- Resolve the uncommitted working-tree files: the `summer-intern-2026/` test pages (these are the
  restricted/intern-scratch examples — should now be excluded/deleted), the stray
  `claude/claude-faq.md` seed (superseded by `claude-frequently-asked-questions.md`; it also has 2
  broken links), `test-resume-tailor-machine-brain*`, and the new `guides/` page (keep if real).
- List files explicitly for commit (never `git add -A`). Push to `main` → triggers the deploy
  workflow → live site re-renders. **Nothing today is live until this push.**

### Stage 8 — ADR + tests
- Write the superseding ADR: "Public-only publication via export-time access classification"
  (supersedes ADR-0002's "every page exported / no access fields" stance). Capture the public-only
  decision and the Phase-2-RBAC deferral.
- Salvage/adapt the classifier tests from su-kb-pipeline with fixtures (restricted vs public vs
  inherited-restriction cases). No network in tests.

## Decision gates / risks

- **What counts as "public"?** SU Confluence is behind NetID (not anonymous-readable), so "public"
  here means **"no read restriction limiting it to a subset"** — readable by the general SU
  population, the intent being the public KB. Confirm this definition matches Aaron's expectation
  if in doubt. The classifier keys on read restrictions, not on Confluence anonymous access.
- **Pagination:** su-kb-pipeline flagged that `/restriction/byOperation` used `limit: 200`,
  unverified for spaces larger than ITSAI. Fine for the demo; note it for larger spaces.
- **Don't over-salvage:** resist pulling back the full RBAC metadata / space-classifier / identity
  machinery. Public-only needs only the binary read-restriction check.

## Verification checklist

- [ ] `is_public()` returns False for the 3 known restricted Summer-Intern pages (test fixture).
- [ ] Export writes only public pages; restricted ones appear in the exclusion report.
- [ ] Leak guard fails the build when a restricted page is planted in `site/content/` (test it).
- [ ] `python tools/render.py` still builds green (36 pages today).
- [ ] Classifier tests pass with no network calls.
- [ ] (After Stage 6) the 29 published pages are all verified public.

## Out of scope (Phase 2 — not now)

- RBAC / per-user or per-department access control.
- An authenticated dynamic surface for restricted content (would need SU infra + SSO; this is
  where the old `su-kb-pipeline` MCP/access work would converge).
- A "departments author their own markdown → auto-sync" tool (the eventual Confluence replacement).
- Retaining restricted pages locally for future admin use (deferred — public-only means we don't
  store them at all right now).
