# su-kb-site

A **Syracuse-owned, markdown-native knowledge base** the university hosts and controls end-to-end on GitHub Pages. Two consumers: humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill.

## Vision & scope

**Vision** — Pages are authored as plain Markdown (easy to version, diff, and fetch), rendered to a fast human-readable site, and exposed in an LLM-optimized form (raw `.md` mirror + `/llms.txt`) so Claude and other assistants answer from it accurately. The bet: **owning content as Markdown in Git — rather than renting a hosted wiki — gives SU full control over hosting, formatting, access, and AI-readiness.**

**Scope** — This is a **demo scoped to the ITS Data & AI workspace.** Initial content was migrated out of that team's Confluence space to make the demo real, but **Confluence is the legacy origin we're moving off, not a system we sync to** — the target state is authoring directly in Markdown. Structure is multi-department from day one (`/data-ai/` is the first namespace); other SU workspaces can be added later without restructuring. The export tool exists to *seed/migrate* content, not to maintain a live sync.

## Read first

1. [docs/STATUS.md](docs/STATUS.md) — current state, active decisions
2. [README.md](README.md) — what this is + setup
3. [docs/decisions/](docs/decisions/) — ADRs (MADR format)

## Workspaces

| Folder | What it is |
|---|---|
| [docs/](docs/) | STATUS.md + decisions/ + log/ — project tracking via the decision-log skill |
| [export-tool/](export-tool/) | Python migration tool — pulls a Confluence space → `site/content/` (one-time seed, not a live sync). Salvaged from prior su-kb-pipeline |
| [tools/](tools/) | The thin Python renderer (`render.py` + `kb_config.py`) that builds `site/content/` → `site/_site/` |
| [_design/](_design/) | The clementine design system — CSS tokens + Jinja2 templates the renderer fills |
| [site/](site/) | `content/` (source markdown) → `_site/` (rendered output, gitignored) |
| [skill/](skill/) | The Claude skill that students install to route WebFetch to this site |
| ~~`_spike/`, `_test-wikilinks/`~~ | Leftover from the Quartz spike + the WebFetch test — safe to delete (see STATUS "What's next") |

## Routing

| Task | Go to | Read first |
|---|---|---|
| Migrate/seed pages from Confluence | [export-tool/](export-tool/) | `export-tool/CONTEXT.md` |
| Change the renderer or output (HTML/.md/llms.txt) | [tools/](tools/) | `site/CONTEXT.md` |
| Adjust styling or page templates | [_design/](_design/) | `site/CONTEXT.md` |
| Edit content | [site/content/](site/content/) | `site/CONTEXT.md` |
| Edit the Claude skill | [skill/](skill/) | `skill/CONTEXT.md` |
| Record a decision / update status | [docs/](docs/) | `docs/STATUS.md` |

## Conventions

- Source pages are plain **GitHub-Flavored Markdown** with an **8-field YAML frontmatter** (`title`, `description`, `page_id`, `department`, `source_url`, `last_modified`, `tags`, `audience`); in-corpus links are ordinary **relative `.md` links** — *not* Obsidian `[[wikilinks]]` (dropped in [ADR-0002](docs/decisions/0002-pivot-from-quartz-to-thin-renderer.md))
- The renderer is a thin Python script ([`tools/render.py`](tools/render.py)); no SSG framework
- ADRs in `docs/decisions/NNNN-title.md` (MADR format) via the decision-log skill
- Per-workspace `CONTEXT.md` files describe local processes
- Don't commit secrets — `.env` is gitignored

## Don't

- Don't run the prior `su-kb-pipeline` eval/chat/web code from here. That architecture was superseded — see `docs/decisions/`.
