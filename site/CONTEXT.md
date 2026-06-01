# site/ + renderer context

How the public GitHub Pages site is built. Source Markdown lives in `site/content/`; the **thin Python renderer** ([`tools/render.py`](../tools/render.py)) reads it and emits the static site to `site/_site/` (gitignored). There is **no SSG framework** — the renderer is a single ~500-line script that fills Jinja2 templates from [`_design/`](../_design/). (Quartz was used during the spike and then dropped — see [ADR-0002](../docs/decisions/0002-pivot-from-quartz-to-thin-renderer.md).)

## Audience

A Python/frontend agent or developer changing the renderer, the templates, the CSS, or the content.

## Where things live

- `site/content/` — source Markdown (8-field frontmatter, relative `.md` links). `content/data-ai/` is the first department tree.
- `tools/render.py` — the renderer: markdown-it-py (GFM + callouts + footnotes) + Pygments → HTML, injected into Jinja2 templates; also emits the byte-faithful `.md` mirror, `llms.txt`, `sitemap.xml`, `robots.txt`, and per-section hub pages.
- `tools/kb_config.py` — pure display data (labels, group order, card copy, callout SVGs, URLs). Edit copy here, not in `render.py`, to keep the renderer thin.
- `_design/` — the clementine design system: `tokens.css`, `docpage.css`, `landing.css`, and the `*.html.jinja` templates the renderer fills.

## Patterns used

- **Dual output**: every page is reachable at both `/path.html` (for humans) and `/path.md` (raw Markdown, for Claude `WebFetch`); `/llms.txt` orients the skill.
- **Clementine styling**: SU navy/orange tokens (`--su-blue: #000E54`, `--su-orange: #F76900`) + Sherman Sans, section ordering from clementine.syr.edu.
- **Cache-busting**: stylesheet/script URLs are content-hashed (`?v=`) so redeploys bypass the GitHub Pages browser cache.

## When working here

- Build locally: `pip install markdown-it-py mdit-py-plugins pygments jinja2 pyyaml` then `python tools/render.py` → `site/_site/`. Pages use an absolute `/su-kb-site` base path, so serve under that prefix to preview (or just push and let CI render).
- Content is currently **seeded from a Confluence export** (see `export-tool/`), but the target state is **authoring Markdown directly in `site/content/`** — the university owns and edits these files, not a hosted wiki. Editing a page = editing its Markdown here.
- Keep the renderer under control: `render.py` is logic, `kb_config.py` is data, `_design/` is presentation. New display copy → `kb_config.py` or a template, not `render.py`.

## Anti-patterns

- Don't reintroduce a Confluence "source of truth" / live-sync framing in the UI. This site *is* the source; the export tool is a one-time migration, not a sync (see project [CLAUDE.md](../CLAUDE.md) "Vision & scope").
- Don't add access-classification / RAG / MCP / chat code. Public GH Pages = world-readable; those modules were intentionally cut.
- Don't commit `site/_site/` — it's generated; CI renders it on deploy.
- Don't add schema.org / JSON-LD as a primary play (weak empirical evidence — see the 2026-05-28 deep-research report).
