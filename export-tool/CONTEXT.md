# export-tool/ context

Python **migration tool** that pulls Confluence pages, converts them to clean markdown, and writes them into `../site/content/<department>/`. This is a **one-time seed/migration**, not a live sync — the project is moving *off* Confluence toward markdown-native authoring (see project [CLAUDE.md](../CLAUDE.md) "Vision & scope"). Once content lands in `site/content/`, that markdown is the source going forward. Salvaged from the prior [`su-kb-pipeline`](../../su-kb-pipeline/) project (~30–40% of that codebase carries over; everything chat/web/access was cut).

## Audience

A Python coding agent (or developer) modifying the export pipeline. Assumes familiarity with Confluence's storage XML format, the Atlassian v2 API, and the ADF (Atlassian Document Format) JSON shape.

## Workspace structure (once populated)

- `src/su_kb_export/` — the package itself (importable as `su_kb_export`)
- `scripts/export_space.py` — CLI entry point: `python -m su_kb_export.cli ITSAI`
- `sync_config.yaml` — declares which Confluence spaces to pull, space→department mapping, wrapper-collapse rules
- `tests/` — pytest suite (trimmed from prior 257 to ~120)

## The two publication gates

Two independent filters decide whether a page is written to `site/content/`; a page must clear **both**:

1. **Access gate (public-only, the real visibility boundary)** — [`restrictions.py`](src/su_kb_export/restrictions.py), per ADR-0003. Classifies each page by its Confluence read restrictions (direct + inherited) and skips anything restricted. This is a *binary* `is_public` check — no per-user/RBAC tiers (that's Phase 2). Restricted pages are never written, never committed, and are listed in `.last-exclusions.jsonl`.
2. **Content-quality gate (drafts)** — `SyncConfig.exclusion_reason()`. Name/segment match that keeps `(Test)` drafts + intern scratch off the *published* KB. This is **not** an access control — it answers "is this finished?", not "is this private?".

A build-time **leak guard** (in the puller's export summary, and best-effort in [`../tools/render.py`](../tools/render.py)) fails the build if a page classified restricted is ever found in the output — defense in depth against a future misroute.

## Patterns used

- **Macro-handler registry**: flat dict mapping macro name → handler callable; one entry per supported Confluence macro
- **Strictness boundary**: tolerate unknown macros (warn + continue); hard-fail unparseable XML / missing identity fields (dead-letter)
- **Fallback-first ADF parsing**: prefer storage-XML-shaped `<ac:adf-fallback>` over JSON walker; reuses the macro registry
- **Attachment verifier**: post-conversion check that every emitted reference resolves to a file on disk (false-green prevention)
- **Dead-letter routing**: conversion failures go to a separate folder with full traceback; corpus stays clean
- **Content-hash skip-on-rerun**: per-page `.sync-state.json` makes re-pulls fast (~1.5s no-op for unchanged spaces)
- **Wrapper-collapse**: strip the redundant Confluence ancestors (`AI @ Syracuse University`, `AI`) when computing output paths so URLs are `/data-ai/claude/...` not `/data-ai/ai-at-syracuse-university/ai/claude/...`

## When working here

- Tests live in `tests/`, mirror the `src/` structure
- New macros: one entry in `src/su_kb_export/macros.py` `MACRO_HANDLERS`
- New dependency: justify against existing tools (this code intentionally runs without FastAPI / anthropic / sse-starlette / jinja2)
- The output of this tool is consumed by the renderer (`../tools/render.py`); don't break the 8-field frontmatter contract

## Anti-patterns

- Don't expand the access gate into per-user / per-department RBAC or a load-time check. Public GH Pages is world-readable; the only enforceable model here is the binary, export-time public-only classifier (ADR-0003). RBAC needs a separate authenticated surface — explicit Phase 2.
- Don't lean on the name-based `exclude_*` filter to keep private content off the site. It's a draft filter; read restrictions are what gate visibility (`restrictions.py`).
- Don't add RAG / MCP / chat code back. Those modules were intentionally cut
- Don't write directly to the rendered `../site/public/` output; only to `../site/content/`
