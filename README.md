# su-kb-site

Public knowledge base for **Syracuse University's ITS Data & AI department**, replacing Confluence with a GitHub Pages site styled to match [clementine.syr.edu](https://clementine.syr.edu/).

## What this is

Two consumers, one site:

1. **Humans browse** the rendered HTML at `https://<owner>.github.io/su-kb-site/` (clementine styling — SU navy/orange tokens, Sherman Sans).
2. **Claude's `WebFetch`** reads a parallel `.md` mirror at `https://<owner>.github.io/su-kb-site/<path>.md`, with a curated `/llms.txt` at site root as the LLM-friendly navigation index. An org-wide Claude skill routes student/staff questions to the right pages on this site.

Built on **Quartz v4** for first-class Obsidian-flavored markdown (`[[wikilinks]]`, YAML frontmatter, callouts). Multi-department-ready from day 1: `/data-ai/` is the first department namespace; HR, Registrar, ITHELP etc. can follow under `/<department>/` without restructuring.

## Architecture at a glance

```
Confluence (ITSAI space)
        │
        ▼
Python export-tool ─→ site/content/data-ai/*.md
                              │
                              ▼
                       Quartz v4 build
                              │
            ┌─────────────────┼──────────────────┐
            ▼                 ▼                  ▼
     rendered HTML        `.md` mirror       /llms.txt
            │                 │                  │
            └─────────────────┴──────────────────┘
                              │
                              ▼
                      GitHub Pages (public)
                              │
            ┌─────────────────┴──────────────────┐
            ▼                                    ▼
       Humans browse                  Claude WebFetch (via skill)
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 22+ (for Quartz)
- `gh` CLI authenticated to GitHub
- An Atlassian API token with SU Confluence read access

### Local

```powershell
git clone https://github.com/julianhernandez2155/su-kb-site.git
cd su-kb-site
Copy-Item .env.example .env
# Edit .env — fill in ATLASSIAN_EMAIL, ATLASSIAN_TOKEN

# Export tool (Python)
cd export-tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m pytest

# Site build (after content lands)
cd ..\site
npm install
npm run build
npm run serve   # local preview at http://localhost:8080
```

## Project tracking

Decisions, status, and session logs live under [`docs/`](docs/) via the `decision-log` skill. Read [`docs/STATUS.md`](docs/STATUS.md) for the current state.

## Provenance

Salvaged from the prior [`su-kb-pipeline`](https://github.com/julianhernandez2155/su-kb-pipeline) prototype after the architecture pivoted from FastMCP + FTS5 to a static-site + Claude-skill model. See `docs/decisions/` for the pivot rationale.

This site is **not** the official Clementine product, despite shared styling — see the Codex extraction notes for brand-usage guidance.
