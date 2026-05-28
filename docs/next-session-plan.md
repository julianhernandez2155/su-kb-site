---
title: Next-session execution plan — Quartz → thin renderer pivot
status: ready to execute
date: 2026-05-28
supersedes_intent_of: ADR-0001
---

# Next-session execution plan — pivot from Quartz to a thin Python renderer

## Goal

Ship `su-kb-site` as a working public KB at <https://julianhernandez2155.github.io/su-kb-site/> with:

1. A clean GFM markdown corpus (no Obsidian-isms) auto-generated from Confluence
2. A thin Python renderer + Jinja2 templates (~150 lines target, ≤300 hard ceiling) producing styled HTML for humans + raw `.md` mirror for Claude `WebFetch`
3. 29 ITSAI pages rendered and deployed
4. `_design/` accessibility blockers fixed
5. ADR-0002 documenting the pivot

**Why this shape:** the AI council (R2 synthesis in this session, 2026-05-28) converged from opposite directions on this answer. The empirical wikilink-through-WebFetch test killed Quartz's load-bearing justification. The Skeptic's "no build" Option D collapsed under the realization that `_design/docpage.html` hardcodes the sidebar in two places and the article body is HTML (not markdown). The honest minimum is a thin renderer — bigger than nothing, smaller than Quartz.

## Critical constraint — DON'T MODIFY THE PRIOR PROJECT

The previous prototype lives at `SU_AI_Intern/prototypes/su-kb-pipeline/`. It is a **frozen artifact** — represents shipped Phase 1.1 work, has its own PR, its own STATUS, its own internal logic.

**This session must NOT modify any file under `SU_AI_Intern/prototypes/su-kb-pipeline/`.** Salvage by copying source files INTO `su-kb-site/export-tool/src/su_kb_export/`, then editing the copies. The originals stay as-is.

If a copied module needs upstream fixes that would benefit the prior project, note them in the session log — don't touch them this session.

## What to read first when starting the new session (in order)

1. **This file** — `docs/next-session-plan.md` (the playbook)
2. **`docs/STATUS.md`** — current state of `su-kb-site`
3. **`docs/decisions/0001-quartz-v4-as-ssg.md`** — the decision being superseded
4. **`_design/design-notes.md`** — what the design is and how it was meant to port
5. **`_design/codex-review-2026-05-28.md`** — Codex's AA-contrast + sidebar + scrollspy findings
6. **`_test-wikilinks/README.md`** — context for the empirical test that justifies the pivot
7. **The 3 council R2 transcripts** are NOT persisted; the synthesis is in this plan's "Why this shape" above

## The decision being executed

Pivot from **ADR-0001 (Quartz v4)** to a **thin Python renderer**. The new decision will be **ADR-0002** (write it in Stage 6 below).

**Why not Quartz** (the Defender's case in R2): Quartz's load-bearing reason (native wikilink parsing) is gone now that we're emitting GFM-style relative links at the source. The remaining Defender argument — bus-factor / handoff — flips the other way: a 150-line documented Python script with Jinja2 templates is MORE handoffable than a Quartz codebase with custom plugins, disabled features, and Preact components. A successor can read the renderer in 20 minutes.

**Why not "no build at all"** (the Skeptic's R1 D): `_design/docpage.html` has the sidebar hardcoded in two places (desktop `<aside>` + mobile `<details>`); 29 pages × 2 places = 58 spots to edit per sidebar change. The article body is HTML, not markdown. Hand-authoring 29 pages of 700–1771 words is 4–6 days, not 2. "No build" was never tenable.

**The escape hatch**: if the renderer crosses ~300 lines or fights basic features, switch to **MkDocs-Material** (ADR-0001's documented fallback). Do not let the renderer grow into a half-built SSG.

---

## Stages

Target wall-clock at 20 hrs/week: **12–15 hours total over 4–5 working sessions**. Session 5 (the research memo) is the deliverable Aaron actually asked for — don't drop it.

### Stage 0 — Pre-flight (read-only, ~20 min)

Don't write anything yet. Verify the environment.

```powershell
# Tooling check
node --version    # >= 22
python --version  # >= 3.11
gh --version
git -C "c:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site" status

# Read the orienting files in order (the list above)

# Verify .env has the required credentials
cat .env  # should have ATLASSIAN_EMAIL + ATLASSIAN_TOKEN
```

If `.env` is missing, copy from `.env.example` and ask Julian for the Atlassian token.

### Stage 1 — Salvage the export-tool (~3 hours)

**Goal:** populate `su-kb-site/export-tool/` with the Python modules that handle Confluence parsing, COPIED from `su-kb-pipeline` and adapted in place. Original files untouched.

#### 1a. Set up the workspace

```powershell
$dest = "c:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site\export-tool"
$src = "c:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-pipeline\src\sukb\ingest"

New-Item -ItemType Directory -Path "$dest\src\su_kb_export", "$dest\scripts", "$dest\tests" -Force
```

#### 1b. Copy salvageable modules (don't edit yet)

Copy these from `$src` → `$dest\src\su_kb_export\` UNCHANGED in this sub-stage:

- `puller.py`
- `converter.py`
- `macros.py`
- `adf.py`
- `attachments.py`
- `state.py`
- `dead_letter.py`
- `wikilinks.py` (will be modified in Stage 3)
- `frontmatter.py` (will be rewritten in Stage 3)

Cut entirely (don't copy):

- `access.py`, `restrictions.py`, `spaces.py` (access classification subsystem)

Copy these from `su-kb-pipeline/src/sukb/`:

- `config.py` → adapt to new shape (the new sync_config.yaml is simpler)

#### 1c. Rename package

After the copy, find-replace within `$dest\src\su_kb_export\*.py`:

- Imports `from sukb.ingest.X` → `from su_kb_export.X`
- Imports `from ..config` → `from su_kb_export.config`
- Imports of access/restrictions/spaces modules → DELETE (those code paths get cut)
- The `from .access import` line in `puller.py` line ~21 → delete plus delete all calls to `classify_page_access`, `AncestorRestrictionCache`, `space_audience`, and the `_write_access_outputs` machinery

This is a ~50-line surgical removal in `puller.py`. Walk every reference; don't leave dangling imports.

#### 1d. Set up pyproject.toml + sync_config.yaml

`$dest\pyproject.toml` (trimmed deps — no FastAPI, no anthropic, no uvicorn):

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "su-kb-export"
version = "0.1.0"
description = "Confluence → markdown export tool for su-kb-site"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "lxml>=5.1",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.setuptools.packages.find]
where = ["src"]
```

`$dest\sync_config.yaml` (simplified):

```yaml
# Department mapping: Confluence space_key → site department slug
space_departments:
  ITSAI: data-ai

# Wrapper-collapse: ancestors to skip when computing output paths
# (per user decision 2026-05-28: collapse the redundant Confluence wrappers)
collapse_ancestors:
  - "AI @ Syracuse University"
  - "AI"

enabled_keys:
  - ITSAI

output_dir: ../site/content
api_base: https://su-jsm.atlassian.net/wiki/api/v2
rate_limit_per_sec: 5
```

#### 1e. Copy a trimmed test subset

Copy from `su-kb-pipeline/tests/ingest/` to `$dest/tests/`:

- `test_adf.py`, `test_attachments.py`, `test_converter.py`, `test_macros.py`, `test_state.py`
- `conftest.py` and fixtures

Skip (these test the cut modules):

- `test_access.py`, `test_restrictions.py`, `test_spaces.py`

Run `pytest` from `$dest` to verify ~120 tests pass. If they don't, the salvage is incomplete — debug the import paths before moving on.

**Stage 1 success criterion:** `python -m pytest` in `export-tool/` is green, no imports of deleted access modules anywhere.

---

### Stage 2 — Fix the Codex AA blockers in `_design/` (~3 hours)

Per Codex's `_design/codex-review-2026-05-28.md` (read it first). The four blockers the council Skeptic surfaced:

1. **Primary orange CTA buttons** fail AA contrast on white → use `--su-orange-dark` for white text on orange, OR switch to navy text on the orange background. Verify with the WCAG contrast checker.
2. **"Copy as markdown" button** same issue.
3. **Inline code** orange-on-orange-10 — darken the FG.
4. **Tip callout title + icon** — currently the light-blue `--su-blue-light`; switch to a darker navy.

Plus the non-contrast items the Skeptic flagged:

5. **Mobile nav at 360px** — hide the GitHub link and brand label below 480px (CSS rule in `tokens.css`).
6. **TOC scrollspy** — replace the IntersectionObserver block with the "last heading above threshold" algorithm if Codex's notes call for it. Test on the 70-word Approved Tools page (no H2s) and the 1771-word Claude FAQ (14 H2s).

Touch only `_design/tokens.css`, `_design/docpage.css`, `_design/landing.css`, and the `<script>` block at the bottom of `_design/docpage.html`. Don't restructure HTML.

**Stage 2 success criterion:** open `_design/landing.html` and `_design/docpage.html` in a browser; verify visually that the four blockers are fixed. Run a contrast checker on the buttons and inline code.

---

### Stage 3 — Schema patch + first export (~3 hours)

Now apply the new 8-field schema and drop Obsidian-isms.

#### 3a. Rewrite `frontmatter.py`

The new schema (down from 26 fields):

```yaml
---
title: <canonical title>
description: <one-line summary; load-bearing for SEO meta + LLM snippet>
page_id: '<numeric Confluence page id>'
department: <slug; e.g. data-ai>
source_url: <Confluence URL>
last_modified: <YYYY-MM-DD; not full ISO timestamp>
tags: [<flat list>]
audience: [<students | faculty | staff | IT | ...>]
---
```

Drop entirely:

- `aliases` (unused)
- `visibility_signal`, `restriction_check`, `restriction_source_ids` (access — moot for public site)
- `space_key`, `space_name`, `space_type`, `space_category`, `ancestor_path` (redundant with `department`)
- `version`, `contributors`, `contributors_count` (Confluence account IDs are PII)
- `content_hash`, `synced_at`, `last_sync_status`, `conversion_warnings` (export-tool internals — track in `.sync-state.json` only)
- `doc_type`, `tools`, `topics`, `labels`, `tags_original` (collapse to one `tags` field)
- `days_since_modified`, `maintenance_signal` (derivable from `last_modified`)
- `word_count`, `char_count`, `token_estimate`, `attachment_count` (build diagnostics)

Add:

- `description` — synthesize from first paragraph if Confluence doesn't have an explicit summary
- `department` — from `sync_config.yaml` space → department mapping
- `audience` — default `[students, faculty, staff]` unless the page body suggests otherwise (e.g., "for IT staff" → add IT)

Keep `merge_preserved_keys` / `read_existing_frontmatter` / `find_existing_page_file` / `canonical_filename` (but the filename convention changes — see 3c).

#### 3b. Patch `wikilinks.py`

Change `DefaultLinkResolver.resolve_page_link()` to emit:

- `[<alias-or-title>](./<slug>.md)` — relative markdown link, slug-only filename
- For out-of-corpus: keep the degraded `[title](source_url)` external link

Change attachment / image handling to emit:

- `![<alt-text>](./attachments/<page-id>/<filename>)` — standard markdown image embed
- Drop the `|<size>` Obsidian width suffix

#### 3c. Filename convention change

Old: `<page-id> - <sanitized-title>.md`
New: `<slug>.md` (e.g., `claude-faq.md`)

Page-id moves to frontmatter only. The slug is derived from the title (lowercase, kebab-case).

Update `canonical_filename()` in `frontmatter.py` accordingly. Update `find_existing_page_file()` to search by page_id in frontmatter (not by filename prefix) — this is the rename-safe property.

#### 3d. Strip dead Confluence widgets in `converter.py`

Add a pass that detects and removes lines like:

- `> [!note] Live search widget — view in Confluence`
- `> [!note] Recently-updated widget — view in Confluence`

These are Confluence macros that don't render meaningfully outside Confluence. Have the converter detect by their callout body matching `/widget — view in Confluence/i` and skip them.

#### 3e. Synthesize `description` field

In `converter.py`, after body conversion, extract the first paragraph (or first sentence if the paragraph is long) and set it as the `description` in frontmatter. Trim to ~200 characters. If the body starts with an H2 (no lede), fall back to the title + tagline pattern (`<title> — overview`).

This is the field that becomes the Google snippet AND the LLM-preview. It's load-bearing.

#### 3f. Wrapper-collapse in puller.py

Per `sync_config.yaml`'s `collapse_ancestors`: when computing the output path from `ancestor_path`, filter out names in that list. So a page at `AI @ Syracuse University > AI > Claude > Claude FAQ` writes to `site/content/data-ai/claude/claude-faq.md`, not `site/content/data-ai/ai-at-syracuse-university/ai/claude/claude-faq.md`.

Single ~10-line change to `_resolve_ancestor_path()`.

#### 3g. Run the export

```powershell
cd c:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site\export-tool
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

# Need .env with ATLASSIAN credentials at the repo root
python scripts/export_space.py ITSAI
```

`scripts/export_space.py` is a thin CLI that calls into the puller. Roughly:

```python
import sys
from su_kb_export.config import SyncConfig
from su_kb_export.puller import ConfluencePuller, load_credentials

cfg = SyncConfig.load("sync_config.yaml")
email, token = load_credentials()
puller = ConfluencePuller(cfg, email, token)
for event in puller.pull_space(sys.argv[1]):
    print(f"[{event.kind}] {event.payload}")
```

**Stage 3 success criterion:** `site/content/data-ai/` is populated with ~29 markdown files; each has the new 8-field frontmatter; wikilinks rendered as `[text](./slug.md)`; no dead Confluence widget callouts; descriptions present on every page.

Spot-check 3 pages by eyeball: Claude FAQ, AI @ SU landing, mentorAI.

---

### Stage 4 — Build the proof-of-concept renderer (~3 hours)

**This is the gate.** Write the Advocate's `_design/build-one.py` and see what it actually costs.

Target: process ONE page (the 1,771-word Claude FAQ — the hardest case in the corpus) into the `_design/docpage.html` template via Jinja2.

#### 4a. Write `tools/build-one.py`

```python
# tools/build-one.py — proof-of-concept single-page renderer
# Goal: take site/content/data-ai/claude/claude-faq.md and produce
# _design/output/claude-faq.html using _design/docpage.html as the template.
# If this comes in under ~80 lines and the output renders Codex-clean,
# we proceed. If it bloats, take ADR-0001's MkDocs-Material escape hatch.

# Required deps:
# pip install markdown-it-py mdit-py-plugins pygments jinja2 pyyaml
```

The script should:

1. Read `site/content/data-ai/claude/claude-faq.md`
2. Parse YAML frontmatter via PyYAML
3. Render markdown body via `markdown-it-py` with GFM plugins (tables, strikethrough, task-lists) + callout plugin (for `> [!note]` etc.) + footnote
4. Syntax-highlight fenced code via Pygments (with a small CSS bundle)
5. Convert `_design/docpage.html` into a Jinja template by replacing the hardcoded article body with `{{ body | safe }}`, the breadcrumbs with `{{ breadcrumbs }}`, the article-meta with template variables, and the sidebar with `{{ sidebar | safe }}`
6. Auto-derive TOC from H2/H3 headings in the rendered HTML
7. Render the Jinja template with all the variables
8. Write to `_design/output/claude-faq.html`

Line target: **80 lines for build-one.py + the modified `_design/docpage.html.jinja`**. If the script is over ~200 lines or the template surgery is brittle, that's a signal to stop.

#### 4b. Verify visually

Open `_design/output/claude-faq.html` in a browser. Check:

- Layout matches `_design/docpage.html` (sidebar + content + TOC)
- All 14 H2s render with their accent bars
- All 4 callouts render with the correct color treatment
- The fenced code block (PowerShell install commands) has syntax highlighting
- Breadcrumbs are populated
- Article meta (last-updated, page-id, tags) is populated
- Wikilinks resolve as relative links to siblings (even if those files don't exist yet — that's fine; we're testing the renderer)
- The Copy-as-markdown button works (point it at `claude-faq.md` in the same dir)
- WCAG AA contrast still holds

#### 4c. Decision gate

- **If `build-one.py` came in under ~200 lines AND the output is visually clean** → proceed to Stage 5 (generalize).
- **If `build-one.py` is over 300 lines** → STOP. Take the ADR-0001 escape hatch: implement MkDocs-Material instead. Write ADR-0002 documenting WHY the thin renderer didn't survive contact with reality. The 5 Codex-aware Jinja templates Mkdocs-Material would replace are roughly equivalent work; the bus-factor argument the Quartz Defender made now favors MkDocs over a bespoke build.
- **If the output has visual regressions** → fix templates first; don't generalize broken templates.

**Stage 4 success criterion:** one fully-rendered HTML page that matches `_design/docpage.html` quality. Decision recorded in `docs/log/<date>.md` about whether to proceed to Stage 5 or switch to MkDocs-Material.

---

### Stage 5 — Generalize to the full renderer (~3 hours, only if Stage 4 gates)

Promote `tools/build-one.py` to `tools/render.py`. Add:

1. **Walk all `.md` files under `site/content/`** and render each one
2. **Generate per-department `sidebar.json`** from the content tree (one sidebar per `department` frontmatter value). Sort by ancestor_path order; group by subdirectory
3. **Auto-derive breadcrumbs** from each file's ancestor_path
4. **Auto-derive "Related" section** at the bottom of each page from tag overlap with sibling pages (top 3-5 most-overlapping pages)
5. **Copy each `.md` next to its `.html` as the `.md` mirror** — `fs.copyFileSync` equivalent
6. **Generate `site/_site/llms.txt`** — root index file. Format: `# SU ITS Data & AI Knowledge Base\n\n## Pages\n\n- [<title>](./<dept>/<slug>.md): <description>\n...`. Per-department grouping. Plain markdown.
7. **Generate `site/_site/sitemap.xml`** — standard sitemap with all URLs
8. **Write to `site/_site/`** (this becomes the GH Pages artifact)

Line target: **~150 lines for `render.py`**. Hard ceiling **300 lines**. If it grows past 300, that's the signal Stage 4's decision-gate guards.

```powershell
python tools/render.py
# Output: site/_site/ populated with HTML + .md + llms.txt + sitemap.xml
```

**Stage 5 success criterion:**

- All ~29 corpus pages rendered to `site/_site/data-ai/<slug>.html`
- Each has a corresponding `.md` mirror at `site/_site/data-ai/<slug>.md`
- `site/_site/llms.txt` and `site/_site/sitemap.xml` exist
- Open 5 pages in a browser, all render correctly

---

### Stage 6 — ADR-0002 + STATUS update (~1 hour)

Write the ADR documenting this pivot. Path: `docs/decisions/0002-pivot-from-quartz-to-thin-renderer.md`.

Structure (MADR format):

- **Status**: accepted, supersedes ADR-0001
- **Context**: Empirical wikilink-through-WebFetch test 2026-05-28 killed Quartz's load-bearing justification (native wikilink parsing). Council R2 synthesis converged from opposite directions on "thin Python renderer + Jinja over `_design/`."
- **Decision**: Drop Quartz. Use `tools/render.py` (~150 lines, hard ceiling 300) with Jinja2 templates derived from `_design/`.
- **Consequences**:
  - Positive: smaller surface area; no Quartz dependency; markdown is portable to any future renderer; the renderer is inspectable
  - Negative: bespoke code Julian owns; bus-factor risk; no free search/RSS/dev-server
  - Escape hatch: MkDocs-Material if renderer crosses 300 lines

Then update `docs/STATUS.md`:

- "Current focus" → switch from "Stage 3 (promote spike → site)" to "Thin renderer + corpus export shipped"
- "Recent pivots" → add 2026-05-28 council R2 convergence
- Cite ADR-0002

Append today's session to `docs/log/<date>.md`.

---

### Stage 7 — Deploy + verify (~2 hours)

Replace the existing GH Actions workflow with the new build path.

#### 7a. Update `.github/workflows/deploy.yaml`

Change the build step from Quartz to the Python renderer:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- name: Install renderer deps
  working-directory: .
  run: pip install markdown-it-py mdit-py-plugins pygments jinja2 pyyaml

- name: Render site
  run: python tools/render.py

- uses: actions/upload-pages-artifact@v3
  with:
    path: site/_site
```

Drop the npm + Quartz steps. No more Node in the deploy.

#### 7b. Push + watch

```powershell
git add ...  # all the new files; explicit list, per global rule
git commit -m "Pivot from Quartz to thin Python renderer per ADR-0002"
git push origin main
```

Watch the deploy via `gh run watch`. ~1-2 minutes for the Python renderer (vs Quartz's 2-3 minutes).

#### 7c. Spot-check the live site

Visit `https://julianhernandez2155.github.io/su-kb-site/` and verify:

- Landing page renders with the clementine styling (SU navy/orange, Sherman Sans)
- 5 doc pages spot-checked — Claude FAQ, Claude Code Setup, mentorAI, Approved Tools, Copilot FAQ
- Visit each page's `.md` mirror — e.g., `https://julianhernandez2155.github.io/su-kb-site/data-ai/claude/claude-faq.md` — returns clean markdown with the new 8-field frontmatter
- Visit `/llms.txt` — returns the curated bullet index
- WebFetch one of the live `.md` URLs — confirm the new schema is LLM-readable

**Stage 7 success criterion:** all of the above check out. The live site looks like clementine. The `.md` mirrors are clean.

---

### Stage 8 — Cleanup (~1 hour)

The Quartz spike and the wikilink test fixtures have served their purpose. Remove them so the repo stays tight.

```powershell
$repo = "c:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site"
Remove-Item -Recurse -Force "$repo\_spike"
Remove-Item -Recurse -Force "$repo\_test-wikilinks"
```

Update `CLAUDE.md` routing table:

- Remove `_spike/` row (no longer exists)
- Remove `_test-wikilinks/` if it was added
- Add a `tools/` row pointing at the renderer
- Update the "Workspaces" table to reflect actual state

Commit + push the cleanup as a separate commit (so the diff is reviewable).

**Stage 8 success criterion:** `git status` is clean. Repo is `~10 top-level entries, no dead directories.

---

### Stage 9 — Optional but high-value: Aaron's research memo (~3 hours)

**This is the actual internship deliverable.** Per `SU_AI_Intern/CLAUDE.md`, Aaron's brief was "explore and test ideas for the best method to transcribe data so an AI can ingest it" with 5 questions:

1. How should a "knowledge base" article be formatted for ingestion?
2. What's the best way to create new knowledge base articles, and in what hierarchy?
3. Where should they exist?
4. Who should have access to make, edit, view, or use them?
5. How do we keep them updated?

Write `SU_AI_Intern/research/kb-ingestion-project/2026-Q3-memo.md` with:

- **Question 1 — Format**: The 8-field GFM frontmatter + relative-link markdown shape; cite the empirical WebFetch test as evidence; cite `_design/codex-review-2026-05-28.md` for the human-side accessibility / styling considerations
- **Question 2 — Hierarchy**: Department-namespaced URLs (`/data-ai/`, future `/hr/`); Confluence ancestor hierarchy preserved with the redundant-wrapper collapse; page-ID stable identifier in frontmatter
- **Question 3 — Storage**: GitHub Pages public repo + raw `.md` mirror at the same URLs; cite the dual-format design (HTML for humans, `.md` for Claude WebFetch)
- **Question 4 — Access**: Currently fully public; future `_access/` classification subsystem (designed but cut from this prototype) preserves the slot for RBAC-ready metadata
- **Question 5 — Updates**: Confluence stays authoritative; export tool runs periodically; `.sync-state.json` makes re-runs cheap; git history is the audit trail

Use the live `su-kb-site` as **Exhibit A** — link to specific pages and the `.md` mirror URLs. The memo is the answer; the site is the demo.

This is the work Aaron actually asked for. Don't drop it.

---

## Decision gates summary

| Gate | When | If pass | If fail |
|---|---|---|---|
| Stage 1 success | After salvage | Stage 2 | Re-trim imports; verify no su-kb-pipeline pollution |
| Stage 4 success | After `build-one.py` | Stage 5 | Take ADR-0001 escape hatch: implement MkDocs-Material |
| Stage 5 line ceiling | `render.py` > 300 lines | STOP | Switch to MkDocs-Material |
| Stage 7 visual check | After live deploy | Stage 8 | Roll back, debug, redeploy |

---

## Files to create / modify (representative — not exhaustive)

### New
- `export-tool/pyproject.toml`
- `export-tool/sync_config.yaml`
- `export-tool/src/su_kb_export/{config,puller,converter,macros,adf,wikilinks,frontmatter,attachments,state,dead_letter}.py` (all copied from prior project + adapted)
- `export-tool/scripts/export_space.py`
- `export-tool/tests/{conftest,test_adf,test_attachments,test_converter,test_macros,test_state}.py`
- `tools/render.py`
- `site/content/data-ai/**/*.md` (auto-generated by the export)
- `site/_site/**/*` (auto-generated by render.py)
- `docs/decisions/0002-pivot-from-quartz-to-thin-renderer.md`
- `docs/log/<execution-date>.md`

### Modify
- `_design/tokens.css`, `docpage.css`, `landing.css` — Codex blockers
- `_design/docpage.html` (also rename to `_design/docpage.html.jinja` after templating)
- `.github/workflows/deploy.yaml` — swap Quartz for Python renderer
- `docs/STATUS.md` — reflect the pivot
- `CLAUDE.md` — routing table update

### Delete (in Stage 8)
- `_spike/` — Quartz install (no longer relevant)
- `_test-wikilinks/` — test fixtures (purpose served)

### MUST NOT TOUCH
- Anything under `SU_AI_Intern/prototypes/su-kb-pipeline/` — that project is frozen

---

## Open questions for Aaron (don't block on these)

These came out of the council R2 Skeptic's pushback. Worth a 1:1 conversation but don't gate execution:

1. **Has Aaron seen the live demo and asked for more?** If not, the site is supporting evidence; the memo is the product.
2. **Is the org-wide Claude skill an Aaron-asked-for feature, or Julian's invention?** Affects whether Stage 7's `.md` mirror is load-bearing or nice-to-have.
3. **Confluence public-share** — was that ever evaluated as the answer to Aaron's question 3? If not, mention it in the memo as an alternative considered.

---

## Verification at end of execution

The session is "done" when all of these are true:

- [ ] `python -m pytest` in `export-tool/` is green
- [ ] `site/content/data-ai/` has ~29 markdown files, all with the 8-field frontmatter
- [ ] `tools/render.py` is ≤300 lines (target ~150)
- [ ] `site/_site/` has HTML + `.md` + `llms.txt` + sitemap.xml for every page
- [ ] Live site at <https://julianhernandez2155.github.io/su-kb-site/> renders with clementine styling
- [ ] WCAG AA contrast passes on primary CTA, copy button, inline code, tip callouts
- [ ] `_spike/` and `_test-wikilinks/` deleted
- [ ] ADR-0002 written; STATUS.md updated; daily log entry appended
- [ ] No file under `SU_AI_Intern/prototypes/su-kb-pipeline/` was modified
- [ ] Aaron's research memo started (Stage 9) — at minimum, an outline

If Stage 4's decision gate triggered the MkDocs-Material escape: the same checklist applies but `tools/render.py` is replaced by `mkdocs.yml` + theme overrides, and ADR-0002 documents that path instead.
