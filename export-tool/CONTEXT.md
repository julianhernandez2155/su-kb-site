# export-tool/ context

Python tool that pulls Confluence pages, converts them to clean markdown, and writes them into `../site/content/<department>/`. Salvaged from the prior [`su-kb-pipeline`](../../su-kb-pipeline/) project (~30–40% of that codebase carries over; everything chat/web/access was cut).

## Audience

A Python coding agent (or developer) modifying the export pipeline. Assumes familiarity with Confluence's storage XML format, the Atlassian v2 API, and the ADF (Atlassian Document Format) JSON shape.

## Workspace structure (once populated)

- `src/su_kb_export/` — the package itself (importable as `su_kb_export`)
- `scripts/export_space.py` — CLI entry point: `python -m su_kb_export.cli ITSAI`
- `sync_config.yaml` — declares which Confluence spaces to pull, space→department mapping, wrapper-collapse rules
- `tests/` — pytest suite (trimmed from prior 257 to ~120)

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
- The output of this tool is consumed by Quartz in `../site/`; don't break the frontmatter contract

## Anti-patterns

- Don't add access-classification code back. Public GH Pages = world-readable; access filtering happens at publish-time vetting, not load-time
- Don't add RAG / MCP / chat code back. Those modules were intentionally cut
- Don't write directly to the rendered `../site/public/` output; only to `../site/content/`
