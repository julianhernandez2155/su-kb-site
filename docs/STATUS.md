# Project Status — su-kb-site

_Last updated: 2026-05-28 (evening — third session)_

## Current focus

**Scope:** building a public GitHub Pages knowledge base that replaces Confluence for SU's ITS Data & AI department. Two consumers — humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill. Multi-department-ready from day 1; AI department is the seed.

**State (2026-05-28, evening):** Stages 1 + 2 complete; Quartz spike works. **Architecture pivoted: ADR-0001 superseded by [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md)** — empirical wikilink-through-WebFetch test killed Quartz's load-bearing justification; AI council R2 converged on a thin Python renderer + Jinja2 templates of `_design/` (~150-line target, hard ceiling 300, escape hatch to MkDocs-Material).

**Next:** execute [`docs/next-session-plan.md`](next-session-plan.md) in a fresh session — 9 stages, 12–15 hours of work, two explicit decision gates. Stage 1 is the export-tool salvage (COPY from `su-kb-pipeline` into `su-kb-site/export-tool/`; do NOT modify the prior project's files).

## What's working

- Folder tree per the approved plan ([C:\Users\julia\.claude\plans\fully-plan-plan-out-tranquil-sunbeam.md](file:///C:/Users/julia/.claude/plans/fully-plan-plan-out-tranquil-sunbeam.md))
- Root orientation files (`CLAUDE.md` with routing table, `README.md` with setup, `.gitignore`, `.env.example`)
- Per-workspace `CONTEXT.md` stubs in `export-tool/`, `site/`, `skill/`
- **Live GitHub Pages site at <https://julianhernandez2155.github.io/su-kb-site/>** — Quartz v4 build, clementine-derived styling (SU navy/orange tokens, Sherman Sans local fonts), 3 seed pages rendering
- GitHub Actions workflow at `.github/workflows/deploy.yaml` — auto-deploys on push to `main`
- `_design/` HTML/CSS templates with Codex review signoff (4 AA-contrast blockers documented for Stage 2 of next-session-plan)
- `_test-wikilinks/` empirical test fixtures (committed at `99e6d70`) — confirmed wikilinks survive WebFetch intact

## What's next

See [`docs/next-session-plan.md`](next-session-plan.md) for the full 9-stage breakdown. Headline order:

1. **Stage 1 — Salvage export-tool by COPYING from su-kb-pipeline** (~3 hrs; constraint: do NOT modify source project)
2. **Stage 2 — Fix `_design/` AA-contrast blockers** (~3 hrs)
3. **Stage 3 — Schema patch + first export against ITSAI** (~3 hrs)
4. **Stage 4 — `build-one.py` proof-of-concept** (~3 hrs; decision gate at ≤200 lines)
5. **Stages 5–8 — Full renderer + deploy + cleanup** (~6 hrs)
6. **Stage 9 — Aaron's research memo** (~3 hrs; the actual internship deliverable per `SU_AI_Intern/CLAUDE.md`)

## Active decisions

- [ADR-0002](decisions/0002-pivot-from-quartz-to-thin-renderer.md) — Pivot from Quartz to a thin Python renderer (supersedes [ADR-0001](decisions/0001-quartz-v4-as-ssg.md))

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

- **Will the thin renderer stay under 300 lines?** Stage 4 decision gate. If no, take ADR-0002's escape hatch to MkDocs-Material (inherited from ADR-0001).
- **Has Aaron seen the live site and asked for more, or is the research memo (Stage 9) the actual deliverable?** Worth a 1:1 conversation before Stage 9 lands.
- **What name does Aaron's team pick for the production repo?** Working name is `su-kb-site`; renames are cheap before public launch.
