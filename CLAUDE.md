# su-kb-site

Public GitHub Pages knowledge base replacing Confluence for **Syracuse University's ITS Data & AI department**. Built on Quartz v4. Two consumers: humans browsing (clementine.syr.edu styling) and Claude's `WebFetch` via an org-wide Claude skill.

## Read first

1. [docs/STATUS.md](docs/STATUS.md) — current state, active decisions
2. [README.md](README.md) — what this is + setup
3. [docs/decisions/](docs/decisions/) — ADRs (MADR format)

## Workspaces

| Folder | What it is |
|---|---|
| [docs/](docs/) | STATUS.md + decisions/ + log/ — project tracking via the decision-log skill |
| [export-tool/](export-tool/) | Python — converts Confluence → site/content/. Salvaged from prior su-kb-pipeline |
| [site/](site/) | The Quartz v4 project that builds to GitHub Pages |
| [skill/](skill/) | The Claude skill that students install to route WebFetch to this site |
| [_spike/](_spike/) | Disposable — Quartz+clementine styling integration test (delete after Stage 3) |

## Routing

| Task | Go to | Read first |
|---|---|---|
| Export Confluence pages to markdown | [export-tool/](export-tool/) | `export-tool/CONTEXT.md` |
| Adjust styling, add a Quartz plugin, edit content | [site/](site/) | `site/CONTEXT.md` |
| Edit the Claude skill | [skill/](skill/) | `skill/CONTEXT.md` |
| Record a decision / update status | [docs/](docs/) | `docs/STATUS.md` |
| Test Quartz+clementine integration | [_spike/](_spike/) | `_spike/README.md` |

## Conventions

- Frontmatter is Obsidian-style YAML; wikilinks are `[[page-id - title]]` in source markdown
- ADRs in `docs/decisions/NNNN-title.md` (MADR format) via the decision-log skill
- Per-workspace `CONTEXT.md` files describe local processes
- Don't commit secrets — `.env` is gitignored

## Don't

- Don't run the prior `su-kb-pipeline` eval/chat/web code from here. That architecture was superseded — see `docs/decisions/`.
