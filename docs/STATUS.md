# Project Status — su-kb-site

_Last updated: 2026-06-08_

> **Reconciliation note (2026-06-01):** the prior snapshot was written mid-pivot on 2026-05-28 and missed the **7 commits that *executed* the pivot that same evening**. This update realigns STATUS with git reality — Stages 1–8 are done and live; Stage 9 + cleanup remain.

## Current focus

**Scope:** a **Syracuse-owned, markdown-native knowledge base** the university hosts and controls end-to-end on GitHub Pages — full control over hosting, formatting, access, and AI-readiness, instead of renting a hosted wiki. Two consumers — humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill. This is a **demo scoped to the ITS Data & AI workspace**; content was migrated out of that team's Confluence space to seed it, but Confluence is the legacy origin we're moving off, not a sync target. Multi-department-ready from day 1; other SU workspaces can follow. (Full vision in the project [CLAUDE.md](../CLAUDE.md).)

**State (2026-06-01, reconciled against git):** The Quartz→thin-renderer pivot wasn't just decided — it was **executed and shipped the same evening (2026-05-28)**. Live site is up and green: thin Python renderer in production, a real **29-page ITSAI corpus** deployed, hub pages + collapsible sidebar redesigned. Stages 1–8 of `next-session-plan.md` are effectively done. ADR-0001 superseded by [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md).

**Update (2026-06-01 evening):** public-only access classification ([ADR-0003](decisions/0003-public-only-access-classification.md)) is shipped and live. The export now classifies each page by its Confluence read restrictions and publishes only public ones; restricted pages are skipped with a leak-guard backstop. Live re-export confirmed the 3 restricted intern pages excluded and all 29 public pages published.

**Update (2026-06-08):** the **authoring workflow shipped.** `faculty-page-authoring` is built and committed across RPI Phases 1–3, and **validated live on SU Claude Enterprise** — a real page drafted by the skill (with no hand-editing) is live on GitHub Pages and passes the validator. The publish gate (`check_frontmatter.py` + CI + the restricted-merge model, [ADR-0004](decisions/0004-human-gate-via-restricted-merge-access.md)) is committed but **not yet enforcing**: it goes live only when branch protection is flipped on the pushed repo.

**Next:** Push `main`, then flip branch protection (require PR + required `validate` check + restrict merge) and run the blocked-PR test — the live fail-closed proof. (See "What's next.")

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
- **AI-retrieval surfaces hardened + `agent_site_bench` benchmark** (committed `7861382`, 2026-06-04) — expanded the generated `robots.txt` AI/search-crawler allowlist (OpenAI / Anthropic / Perplexity / Google / Apple bots) and machine-surface emission in [`tools/render.py`](../tools/render.py) + [`tools/kb_config.py`](../tools/kb_config.py); new [`tools/agent_site_bench/`](../tools/agent_site_bench/) CLI harness compares this site vs Shahaan's `su-kb-pages-demo` on machine-surface discovery + the `llms.txt`→`.md` retrieval path (no-paid `--surface-only` probe + optional OpenRouter agent-loop + judge). Findings in [`docs/AI_RETRIEVAL_OPTIMIZATION_REPORT_2026-06-03.md`](AI_RETRIEVAL_OPTIMIZATION_REPORT_2026-06-03.md). **Generated-surface-only** — no edits to `site/content/`, design, or layout

## What's next

Stages 1–8 of [`docs/next-session-plan.md`](next-session-plan.md) (2026-05-28) and the public-only classifier ([ADR-0003](decisions/0003-public-only-access-classification.md), 2026-06-01) shipped and are live. The **authoring workflow** (`faculty-page-authoring`) is now built, committed (5 commits, 2026-06-08), and live-validated; the remaining work is GitHub-side gate activation:

1. **Push `main`** — reconcile first (the live-test page was merged via the GitHub web UI and isn't local): `git fetch origin && git pull origin main && git push origin main`.
2. **Flip the gate on** ([`branch-protection.md`](../rpi/faculty-page-authoring/implement/branch-protection.md), task 1.7): require a PR + the required `validate` status check + restrict merge to maintainers (CODEOWNERS-required review stays **off** per [ADR-0004](decisions/0004-human-gate-via-restricted-merge-access.md)). Then run the **blocked-PR test** (1.8/3.2) — a deliberately-invalid page must fail CI and be unmergeable. This is the one piece of the v1 definition-of-done still outstanding.
3. **Phase 0.2** — confirm the maintainer set (who holds merge rights) with Aaron.
4. **Phase 4 fast-follows** (not v1 blockers): `visibility: public` backfill over the 29 legacy pages + the export tool; optional fix for the renderer's `> [!note]-` callout collapse (some exported mentorAI pages render degraded — found 2026-06-08).

The drafter itself (`skill/drafter/`) is proven: installed on SU Claude Enterprise, it drafted a real page that passed the validator with zero edits and went live. Research framing (CONDITIONAL GO, the schema fork, GATE 0) is now historical — see [`rpi/faculty-page-authoring/`](../rpi/faculty-page-authoring/) for the full plan + implementation record.

> Renderer size note: `tools/render.py` is 517 lines, but ADR-0002's amendment **retired the 300-line hard gate** — the operative constraint is "single-file, inspectable, no SSG-framework creep," which it still satisfies. No action needed.

## Active decisions

- [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md) — Pivot from Quartz to a thin Python renderer (supersedes [ADR-0001](decisions/0001-quartz-v4-as-ssg.md))
- [ADR-0003](decisions/0003-public-only-access-classification.md) — Public-only publication via export-time access classification
- [ADR-0004](decisions/0004-human-gate-via-restricted-merge-access.md) — Human publish-gate via restricted merge access, not CODEOWNERS-required review

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

- **GATE 0 (authoring guardrails) — RESOLVED.** Rather than wait on Robert's files, we **built the gate ourselves** (`check_frontmatter.py` + `validate-content.yaml` + `CODEOWNERS` + PR template, committed 2026-06-08). The native/export schema fork was reconciled via an explicit `origin:` discriminator. What remains is settings-only (flip branch protection), not code.
- **Has Aaron seen the live site and asked for more, or is the research memo (Stage 9) the actual deliverable?** Worth a 1:1 conversation before Stage 9 lands.
- **What name does Aaron's team pick for the production repo?** Working name is `su-kb-site`; renames are cheap before public launch.
