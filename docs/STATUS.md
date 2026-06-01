# Project Status — su-kb-site

_Last updated: 2026-06-01 (reconciled against git)_

> **Reconciliation note (2026-06-01):** the prior snapshot was written mid-pivot on 2026-05-28 and missed the **7 commits that *executed* the pivot that same evening**. This update realigns STATUS with git reality — Stages 1–8 are done and live; Stage 9 + cleanup remain.

## Current focus

**Scope:** a **Syracuse-owned, markdown-native knowledge base** the university hosts and controls end-to-end on GitHub Pages — full control over hosting, formatting, access, and AI-readiness, instead of renting a hosted wiki. Two consumers — humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill. This is a **demo scoped to the ITS Data & AI workspace**; content was migrated out of that team's Confluence space to seed it, but Confluence is the legacy origin we're moving off, not a sync target. Multi-department-ready from day 1; other SU workspaces can follow. (Full vision in the project [CLAUDE.md](../CLAUDE.md).)

**State (2026-06-01, reconciled against git):** The Quartz→thin-renderer pivot wasn't just decided — it was **executed and shipped the same evening (2026-05-28)**. Live site is up and green: thin Python renderer in production, a real **29-page ITSAI corpus** deployed, hub pages + collapsible sidebar redesigned. Stages 1–8 of `next-session-plan.md` are effectively done. ADR-0001 superseded by [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md).

**Next:** (1) **Stage 9 — Aaron's research memo**, the actual internship deliverable; (2) triage uncommitted content (a new `guides/` page + 3 `summer-intern-2026/` test pages + stray seed/test files); (3) reckon with [`tools/render.py`](../tools/render.py) at **517 lines, past ADR-0002's 300 hard ceiling**; (4) close BUILD-REPORT's remaining gaps.

## What's working

- **Live GitHub Pages site at <https://julianhernandez2155.github.io/su-kb-site/>** — HTTP 200, **thin Python renderer** output (no Quartz), clementine-derived styling (SU navy/orange tokens, Sherman Sans local fonts), real ITSAI corpus rendering
- **Thin Python renderer** ([`tools/render.py`](../tools/render.py) + [`tools/kb_config.py`](../tools/kb_config.py)) + Jinja2 templates in `_design/` — dual HTML+`.md` output, llms.txt/sitemap/robots, custom callout plugin, scrollspy TOC, collapsible grouped sidebar, redesigned directory hub pages
- **Real 29-page ITSAI corpus** committed under `site/content/data-ai/` (claude/, clementine-platform/, copilot/, gemini/, ai-general-information/) with attachments — the live Confluence export ran
- **Salvaged export-tool** — full `su_kb_export` package copied from su-kb-pipeline into `export-tool/` (puller, adf, converter, macros, frontmatter, wikilinks, state, dead_letter) with its test suite
- GitHub Actions workflow at `.github/workflows/deploy.yaml` — builds with the renderer, auto-deploys on push to `main` (last run green, 2026-05-28 22:15)
- AA-contrast blockers from the design review fixed (see [BUILD-REPORT.md](../BUILD-REPORT.md)); `_test-wikilinks/` fixtures confirmed wikilinks survive WebFetch (committed `99e6d70`)
- **Confluence framing removed from the public site** (2026-06-01) — hero/trust/footer reframed to "SU-hosted / markdown-native"; the false "auto-synced / last sync" claims are gone (uncommitted)
- **`render.py` date-sort bug fixed** (2026-06-01) — `related_for()` no longer crashes on unquoted `last_modified`; build green with all content (36 pages) (uncommitted)

## What's next

Stages 1–8 of [`docs/next-session-plan.md`](next-session-plan.md) shipped on 2026-05-28 (export-tool salvage, renderer, live export, deploy, redesign). What actually remains:

1. **Execute [`docs/plan-public-only-access.md`](plan-public-only-access.md)** ([ADR-0003](decisions/0003-public-only-access-classification.md)) — re-add the access classifier so only public pages publish (the export currently has no real visibility check). Code work is no-API; the live re-export is token-gated.
2. **Commit + push** — nothing from 2026-06-01 (Confluence removal, render fix, context reframe, docs) is live until pushed to `main`. List files explicitly.
3. **Stage 9 — Aaron's research memo** — the actual internship deliverable per `SU_AI_Intern/CLAUDE.md`. Not started.
4. **Triage uncommitted content** — a new `guides/approved-tools-comparison.md`, 3 `summer-intern-2026/` test pages (julian/rob/shahaan; these are the restricted/intern-scratch examples), and stray seed/test files (`claude/claude-faq.md`, `test-resume-tailor-machine-brain*`). Decide per-file: commit real content, gitignore or delete test scaffolding.
5. **BUILD-REPORT remaining gaps** — directory-index pages (`/data-ai/claude/` may 404), `og:image` PNG fallback, decide whether the unused `audience` field stays or drops to a 7-field schema.

> Renderer size note: `tools/render.py` is 517 lines, but ADR-0002's amendment **retired the 300-line hard gate** — the operative constraint is "single-file, inspectable, no SSG-framework creep," which it still satisfies. No action needed.

## Active decisions

- [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md) — Pivot from Quartz to a thin Python renderer (supersedes [ADR-0001](decisions/0001-quartz-v4-as-ssg.md))
- [ADR-0003](decisions/0003-public-only-access-classification.md) — Public-only publication via export-time access classification

## Recent pivots

- (2026-05-28 evening) [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md) supersedes [ADR-0001](decisions/0001-quartz-v4-as-ssg.md). Trigger: empirical wikilink-through-WebFetch test confirmed wikilinks survive WebFetch intact; AI council R2 converged on thin Python renderer over Quartz.
- (2026-05-28) Architecture pivot from prior `su-kb-pipeline` (FastMCP + FTS5 + RAG) to static GH Pages + Claude skill + WebFetch — driven by Aaron's 2026-05-20 direction. ~30–40% of the prior code (the Confluence-export half) salvages; everything chat/web/access is cut.

## Out of scope (for this prototype)

- Production migration to SU's GitHub org (Aaron's team controls)
- Per-user RBAC / authentication (everything is public on GH Pages)
- Other departments beyond AI (structure supports them; content awaits)
- The eventual three-repo split (one repo for prototype)
- Modifications to the prior `su-kb-pipeline` project (frozen artifact — salvage by COPYING only)

## Open questions

- **Has Aaron seen the live site and asked for more, or is the research memo (Stage 9) the actual deliverable?** Worth a 1:1 conversation before Stage 9 lands.
- **What name does Aaron's team pick for the production repo?** Working name is `su-kb-site`; renames are cheap before public launch.
