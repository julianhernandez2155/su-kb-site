# Project Status — su-kb-site

_Last updated: 2026-05-28_

## Current focus

**Scope:** building a public GitHub Pages knowledge base that replaces Confluence for SU's ITS Data & AI department. Two consumers — humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill. Multi-department-ready from day 1; AI department is the seed.

**State (2026-05-28):** Stage 1 — initial scaffold. Folder tree created; root `CLAUDE.md`/`README.md`/`.gitignore`/`.env.example` written; per-workspace `CONTEXT.md` stubs in place. GitHub repo creation + Quartz spike next.

**Next:** Stage 2 — Quartz spike inside `_spike/` to verify clementine styling integrates cleanly. If it fights for >2 days, fall back to MkDocs-Material (decision gate documented in [ADR-0001](decisions/0001-quartz-v4-as-ssg.md)).

## What's working

- Folder tree per the approved plan ([C:\Users\julia\.claude\plans\fully-plan-plan-out-tranquil-sunbeam.md](file:///C:/Users/julia/.claude/plans/fully-plan-plan-out-tranquil-sunbeam.md))
- Root orientation files (`CLAUDE.md` with routing table, `README.md` with setup, `.gitignore`, `.env.example`)
- Per-workspace `CONTEXT.md` stubs in `export-tool/`, `site/`, `skill/`

## What's next

In order:

1. **Initialize git + create GitHub repo** (`julianhernandez2155/su-kb-site`, private initially)
2. **Stage 2 — Quartz spike**: `npx quartz create` in `_spike/`, drop Codex's clementine assets into `_spike/quartz/styles` + `_spike/quartz/static`, adapt layouts to the clementine class names, render 3 hand-written seed pages
3. **Stage 3 — promote spike to `site/`** once styling fit is confirmed; delete `_spike/`
4. **Stage 4 — salvage and adapt the export-tool** from `../su-kb-pipeline/src/sukb/ingest/`
5. **Stage 5 — run export against ITSAI** with wrapper-collapse config
6. **Stage 6 — add `.md` mirror + `llms.txt` emitter plugins**
7. **Stage 7 — write the Claude skill**
8. **Stage 8 — empirical wikilink-through-WebFetch test** (cheap; high-information)

Full breakdown in the approved plan file.

## Active decisions

- [ADR-0001](decisions/0001-quartz-v4-as-ssg.md) — Pin Quartz v4 as the SSG; v5 plugin ecosystem too immature for a 6-week MVP

## Recent pivots

- (2026-05-28) Architecture pivot from prior `su-kb-pipeline` (FastMCP + FTS5 + RAG) to static GH Pages + Claude skill + WebFetch — driven by Aaron's 2026-05-20 direction. ~30–40% of the prior code (the Confluence-export half) salvages; everything chat/web/access is cut.

## Out of scope (for this prototype)

- Production migration to SU's GitHub org (Aaron's team controls)
- Per-user RBAC / authentication (everything is public on GH Pages)
- Other departments beyond AI (structure supports them; content awaits)
- The eventual three-repo split (one repo for prototype)
- Codex's accessibility audit + link-checking CI (deferred to v1.1)
- The "Copy as markdown" per-page button (v2)

## Open questions

- **Will Quartz's component model accept clementine styling cleanly?** Answer comes from Stage 2 spike; 2-day budget before fallback to MkDocs-Material
- **Does Claude `WebFetch` resolve `[[page-id - title]]` wikilinks semantically, or do we need the `.md` mirror with rewritten relative links?** Answer comes from Stage 8 empirical test
- **What name does Aaron's team pick for the production repo?** Working name is `su-kb-site`; renames are cheap before public launch
