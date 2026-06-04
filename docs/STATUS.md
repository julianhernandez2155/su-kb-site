# Project Status — su-kb-site

_Last updated: 2026-06-01 (reconciled against git)_

> **Reconciliation note (2026-06-01):** the prior snapshot was written mid-pivot on 2026-05-28 and missed the **7 commits that *executed* the pivot that same evening**. This update realigns STATUS with git reality — Stages 1–8 are done and live; Stage 9 + cleanup remain.

## Current focus

**Scope:** a **Syracuse-owned, markdown-native knowledge base** the university hosts and controls end-to-end on GitHub Pages — full control over hosting, formatting, access, and AI-readiness, instead of renting a hosted wiki. Two consumers — humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill. This is a **demo scoped to the ITS Data & AI workspace**; content was migrated out of that team's Confluence space to seed it, but Confluence is the legacy origin we're moving off, not a sync target. Multi-department-ready from day 1; other SU workspaces can follow. (Full vision in the project [CLAUDE.md](../CLAUDE.md).)

**State (2026-06-01, reconciled against git):** The Quartz→thin-renderer pivot wasn't just decided — it was **executed and shipped the same evening (2026-05-28)**. Live site is up and green: thin Python renderer in production, a real **29-page ITSAI corpus** deployed, hub pages + collapsible sidebar redesigned. Stages 1–8 of `next-session-plan.md` are effectively done. ADR-0001 superseded by [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md).

**Update (2026-06-01 evening):** public-only access classification ([ADR-0003](decisions/0003-public-only-access-classification.md)) is shipped and live. The export now classifies each page by its Confluence read restrictions and publishes only public ones; restricted pages are skipped with a leak-guard backstop. Live re-export confirmed the 3 restricted intern pages excluded and all 29 public pages published.

**Next:** Figure out the **authoring workflow** — how do we add new markdown pages to the site? (See "What's next" below.)

## What's working

- **Live GitHub Pages site at <https://julianhernandez2155.github.io/su-kb-site/>** — HTTP 200, **thin Python renderer** output (no Quartz), clementine-derived styling (SU navy/orange tokens, Sherman Sans local fonts), real ITSAI corpus rendering
- **Thin Python renderer** ([`tools/render.py`](../tools/render.py) + [`tools/kb_config.py`](../tools/kb_config.py)) + Jinja2 templates in `_design/` — dual HTML+`.md` output, llms.txt/sitemap/robots, custom callout plugin, scrollspy TOC, collapsible grouped sidebar, redesigned directory hub pages
- **Real 29-page ITSAI corpus** committed under `site/content/data-ai/` (claude/, clementine-platform/, copilot/, gemini/, ai-general-information/) with attachments — the live Confluence export ran
- **Salvaged export-tool** — full `su_kb_export` package copied from su-kb-pipeline into `export-tool/` (puller, adf, converter, macros, frontmatter, wikilinks, state, dead_letter) with its test suite
- GitHub Actions workflow at `.github/workflows/deploy.yaml` — builds with the renderer, auto-deploys on push to `main` (last run green, 2026-05-28 22:15)
- AA-contrast blockers from the design review fixed (see [BUILD-REPORT.md](../BUILD-REPORT.md)); `_test-wikilinks/` fixtures confirmed wikilinks survive WebFetch (committed `99e6d70`)
- **Confluence framing removed from the public site** (committed + live 2026-06-01) — hero/trust/footer reframed to "SU-hosted / markdown-native"; the false "auto-synced / last sync" claims are gone
- **`render.py` date-sort bug fixed** (committed + live 2026-06-01) — `related_for()` no longer crashes on unquoted `last_modified`
- **Public-only access gate live** ([ADR-0003](decisions/0003-public-only-access-classification.md)) — [`export-tool/src/su_kb_export/restrictions.py`](../export-tool/src/su_kb_export/restrictions.py) binary `is_public` (direct + inherited read restrictions, fails closed); puller skips restricted pages and writes a gitignored `.last-exclusions.jsonl`; leak guard in the export summary + `render.py`. Live export confirmed 3 restricted pages excluded, 29 public published. 16 classifier tests; suite 89 passed

## What's next

Stages 1–8 of [`docs/next-session-plan.md`](next-session-plan.md) (2026-05-28) and the public-only classifier ([ADR-0003](decisions/0003-public-only-access-classification.md), 2026-06-01) have shipped and are live. The next focus is authoring:

1. **Authoring workflow — how do we add new markdown pages to the site?** This is the markdown-native authoring half of the vision; the export tool only seeds/migrates *from* Confluence. Explore:
   - **AI-assisted page creation** — "here are some documents, help me draft a page" → a clean markdown page with valid frontmatter.
   - Possibly package this as a **Claude skill** so it's repeatable.
   - An **easy import path** that drops the drafted file into the correct department/ancestor folder with the right 8-field frontmatter, ready for the renderer.

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
