# Engineering Spec — Faculty Page Authoring

_RPI Step 3 (Plan / `eng.md`). Authored 2026-06-08. Grounded in the live `su-kb-site`
repo (verified 2026-06-08), `docs/VISION.md` (v1.1), and the CONDITIONAL-GO research
(`../research/RESEARCH.md`). Locked decisions from Julian 2026-06-08 define scope: **we
build the entire governance back-end ourselves** — Robert's files are not landing._

---

## 0. Scope of this spec (what's net-new and owned here)

The research found **GATE 0 failed**: none of the assumed guardrail files exist in the repo.
Per Julian's 2026-06-08 decision, this feature owns the full publish gate as net-new work,
not "on top of" anyone else's back-end. This spec designs:

1. `tools/check_frontmatter.py` — a native-aware frontmatter validator (CLI + importable).
2. `.github/workflows/validate-content.yaml` — CI that validates changed `site/content/**/*.md`
   on PRs and **blocks merge on failure** (fails closed).
3. `CODEOWNERS` — routes `site/content/**` changes to a human reviewer who must approve.
4. `.github/pull_request_template.md` — a publish-safety checklist for the reviewer.
5. The **drafter** — a Claude Skill (+ copy-paste prompt fallback). Content/instructions, **not
   a service**.
6. (Recommended, optional) `tools/new_page.py` — a thin scaffolder. See §7 for the
   build-or-skip call.

Everything stays thin and stdlib-leaning (VISION P6). The only third-party import the
validator needs is `pyyaml`, which the renderer and export tool already depend on.

---

## 1. Architecture overview

```
                         AUTHORING SIDE                              │   PUBLISH SIDE
  (free, no SU infra: SU Claude Enterprise + GitHub web UI)         │ (existing GH Pages)
                                                                     │
 ┌──────────┐   source docs    ┌───────────────────────┐            │
 │ Faculty/ │ ───────────────► │  Claude (the DRAFTER)  │            │
 │  staff   │   + a few Q&A    │  = Skill OR prompt:    │            │
 │  author  │ ◄─────────────── │  schema rules, native  │            │
 └──────────┘   full .md file  │  convention, slug +    │            │
      │         + exact path   │  path + taxonomy +     │            │
      │                        │  "EVERYTHING IS PUBLIC" │            │
      │                        └───────────────────────┘            │
      │ paste file into GitHub web UI                                │
      │ ("Add file" → commit to a branch → "Propose changes")        │
      ▼                                                              │
 ┌─────────────────────────────────────────────────────────────┐    │
 │                  Pull Request to `main`                       │    │
 └─────────────────────────────────────────────────────────────┘    │
      │                                                              │
══════╪══════════════════ TRUST BOUNDARY (the gate) ════════════════╪═══════════════
      │  Both must pass; both fail CLOSED. Neither is optional.      │
      ▼                                                              │
 ┌──────────────────────────────┐   ┌──────────────────────────────┐│
 │ validate-content.yaml (CI)   │   │ CODEOWNERS human review      ││
 │ runs check_frontmatter.py on │   │ • required reviewer on        ││
 │ changed site/content/**/*.md │   │   site/content/**             ││
 │ • non-zero exit BLOCKS merge │   │ • publish-safety checklist    ││
 │ • schema + visibility:public │   │   (PR template): OK to be      ││
 │   enforced                   │   │   PUBLIC? frontmatter sane?   ││
 │                              │   │   right department?           ││
 └──────────────────────────────┘   └──────────────────────────────┘│
      │  (branch protection: both required before "Merge")          │
══════╪══════════════════════════════════════════════════════════════════════════════
      ▼  merge to main
 ┌──────────────────────────────┐                                   │
 │ deploy.yaml (UNCHANGED)      │  python tools/render.py →          │
 │ render → site/_site →        │  HTML + .md mirror + llms.txt +    │
 │ upload-pages-artifact →      │  llms-full.txt + sitemap → Pages.  │
 │ deploy-pages                 │  New page auto-indexed; llms.txt    │
 └──────────────────────────────┘  regenerated → enters retrieval.  │
      ▼
   PUBLIC: human HTML + raw .md mirror + llms.txt entry (dual-consumer, P3)
```

**Key properties (all verified against the repo):**

- **No backend, no paid API.** Drafting rides the existing SU Claude Enterprise seat; submission
  is GitHub's own web UI. Honors the free-only constraint and VISION P6.
- **The gate is the only thing between a draft and the public internet.** CI (machine) +
  CODEOWNERS (human) both fail closed. This is the VISION P4 enforcement point.
- **`deploy.yaml` does not change.** The new CI is additive and independent; see §4.
- **Auto-indexing confirmed** (`render.py`): `load_corpus()` globs `site/content/**/*.md`;
  `emit_llms_txt()` rebuilds `llms.txt` from the full page set every build; `deploy.yaml` runs
  the renderer on every push to `main`. A merged page enters HTML, the `.md` mirror, and the
  retrieval index with **no manual page-map sync**. (Research's "Robert §8" concern is moot —
  re-verified.)

---

## 2. The schema reconciliation (heart of the spec)

### 2.1 The fork

The 8-field schema is documented in `export-tool/src/su_kb_export/frontmatter.py`:

```
title, description, page_id, department, source_url, last_modified, tags, audience
```

The export validator's `REQUIRED_FIELDS` is:

```python
REQUIRED_FIELDS = ("title", "page_id", "department", "source_url", "last_modified")
```

A **native** page (authored here, never in Confluence) legitimately has **no `page_id` and no
`source_url`** — those identify a Confluence origin. So a correctly-drafted native page would
**fail** the export validator. The two halves of the corpus must validate under reconciled —
not contradictory — rules, under **one** validator (`check_frontmatter.py`), **without weakening
the export path**.

### 2.2 The discriminator — branch on origin via an explicit `origin:` field, with `page_id` as the inference fallback

**Decision: add one explicit frontmatter field, `origin:`, with values `native` | `confluence`.**
The drafter always emits `origin: native`. The export tool's output is treated as
`origin: confluence` (it has `page_id` + `source_url` by construction; see §2.5 for the
non-invasive way the export side keeps validating).

`check_frontmatter.py` resolves origin in this precedence order:

1. If `origin:` is present and valid → use it. (Explicit, self-documenting, the intended path.)
2. Else if `page_id` is present and non-empty → infer `confluence` (back-compat for the 28
   already-exported pages, none of which carry `origin:`).
3. Else → infer `native`.

**Why an explicit field rather than pure `page_id`-presence inference (the discriminator
alternatives):**

- *Pure folder-based* (e.g. "native lives under `summer-intern-2026/`") — **rejected.** Native
  pages must be free to slot anywhere in the taxonomy (`claude/`, `gemini/`, a new area). Tying
  origin to a folder fights the renderer's department-from-frontmatter-or-folder design and
  re-couples placement to meaning.
- *Pure `page_id`-presence inference* — **viable and used as the fallback**, but as the *sole*
  rule it's a silent, implicit contract: a drafter that accidentally emits an empty `page_id: ''`
  would be misclassified, and a reviewer reading the file can't see "this is a native page" — they
  have to infer it from an absence. Absences make poor contracts on a public-publish path.
- *Explicit `origin:`* — **chosen.** It is self-documenting (a reviewer sees the intent), it is
  robust (no reliance on a field's absence), and the validator can give a precise error
  (`origin: native must NOT carry page_id`) instead of guessing. The `page_id` fallback preserves
  back-compat so we do **not** have to touch the 28 existing exported files.

This adds a 9th frontmatter key, but it is **origin metadata, not content** — it doesn't widen the
8-field *content* schema the renderer reads (the renderer ignores unknown keys; verified — it only
reads `title/description/department/source_url/last_modified/tags/audience` plus `page_id`). The
schema's documented "8 fields" stay the public content contract; `origin` (and `visibility`, §3)
are governance markers the validator owns.

### 2.3 The field matrix

| Field | `origin: native` | `origin: confluence` (export) | Notes |
|---|---|---|---|
| `origin` | **required** = `native` | optional (inferred from `page_id` if absent) | the discriminator |
| `title` | **required, non-empty** | **required, non-empty** | both |
| `description` | **required, non-empty** | present (may be empty per export rule) | native is stricter: a human-authored page must summarize itself for SEO + LLM snippet (P3) |
| `page_id` | **must be ABSENT or empty** | **required, non-empty** | the fork. Native MUST NOT carry it; presence on a native page is an error |
| `department` | **required, non-empty** | **required, non-empty** | must be an existing dept slug (`data-ai`) |
| `source_url` | **must be ABSENT or empty** | **required, non-empty** | the fork. Native has no upstream source |
| `last_modified` | **required**, `YYYY-MM-DD` | **required**, `YYYY-MM-DD` | date-only; see §3 |
| `tags` | optional; if present, list of strings | optional; list | may be empty `[]` |
| `audience` | optional; if present, subset of allowed | optional; list | default `[students, faculty, staff]`; allowed adds `IT` |
| `visibility` | **required** = `public` | required = `public` (backfilled lazily; see §3) | fail-closed backstop |

"Must be ABSENT or empty" = the field is either not present, or present with `null`/`''`. A
native page with a **non-empty** `page_id` or `source_url` is a **validation error**
(`E_NATIVE_HAS_CONFLUENCE_FIELD`) — that almost always means the author pasted an exported page's
header by mistake, exactly the kind of thing the gate should catch.

### 2.4 How `check_frontmatter.py` validates each origin (the branch rule, in words)

```
resolve origin (explicit origin: → else page_id-presence → else native)
require: title (non-empty), department (non-empty, in known depts),
         last_modified (YYYY-MM-DD), visibility == "public"
if origin == confluence:
    require page_id (non-empty), source_url (non-empty)
if origin == native:
    require description (non-empty)
    forbid non-empty page_id, forbid non-empty source_url
    enforce slug/path rule (filename == slugify(title); §3)
always (both origins):
    tags, audience — if present, must be lists of strings; audience ⊆ allowed set
    YAML must parse; frontmatter block well-formed (--- ... ---)
```

### 2.5 Not weakening the export path

The export tool keeps **its own** `frontmatter.py` and its `REQUIRED_FIELDS` exactly as-is —
`check_frontmatter.py` does **not** import or modify it, so the export contract is untouched. The
two paths stay decoupled (no shared mutable module). `check_frontmatter.py` *re-derives* the small
pure helpers it needs (`slugify`, the date-only check) as a **tiny local copy** rather than
importing across the `export-tool` package boundary, because:

- Importing `su_kb_export.frontmatter` would couple the authoring CI to the export package's
  install/layout (it lives under `export-tool/src/`, a separate package root) — a coupling P6
  warns against.
- The needed logic is ~15 lines of pure stdlib regex. Copying it (with a one-line comment
  citing the source of truth) is thinner than wiring a cross-package import into CI.
- A unit test (§9) asserts the copied `slugify` stays byte-identical to the export one, so the
  duplication can't silently drift.

The exported corpus continues to validate because `check_frontmatter.py`'s `confluence` branch is
a **superset-compatible** restatement of the export `REQUIRED_FIELDS` (it requires the same five
plus `visibility`, which §3 backfills). Running `check_frontmatter.py` over the current 28 pages is
a CI dry-run acceptance test (§9).

---

## 3. `tools/check_frontmatter.py` — spec

**Purpose.** One validator, native-aware, used by CI (and runnable locally). Thin, stdlib +
`pyyaml` only.

**CLI signature.**
```
python tools/check_frontmatter.py [PATH ...]
  PATH   one or more .md files OR directories (recursed for *.md).
         No args → validate every file under site/content/**/*.md.
Options:
  --changed-only FILE   read newline-delimited paths from FILE (CI passes the
                        changed-file list here); validate only those that are
                        under site/content/ and end in .md.
  --quiet               print only failures.
```

**Inputs.** Markdown files with a leading `--- ... ---` YAML frontmatter block. Parsing reuses the
renderer's own split convention (`text.split("---", 2)`) so "what the validator accepts" ==
"what the renderer parses" — a file that validates renders, and vice versa.

**Outputs / exit codes.**
- Human-readable lines to stdout: `OK  <path>` or `FAIL <path>: <CODE> <message>` (one per error).
- A trailing summary: `N files, M passed, K failed`.
- **Exit 0** iff every file passed. **Exit 1** if any file failed (this is what fails CI closed).
  Exit 2 for a usage error (bad args / unreadable path) — also non-zero, so CI still blocks.

**Per-field checks.**

| Check | Code | Rule |
|---|---|---|
| Frontmatter present | `E_NO_FRONTMATTER` | file starts with `---\n` and has a closing `---` |
| YAML parses to a dict | `E_BAD_YAML` | `yaml.safe_load` succeeds and yields a mapping |
| `title` | `E_MISSING_TITLE` | present, non-empty string |
| `description` (native) | `E_MISSING_DESC` | native: present, non-empty |
| `department` | `E_BAD_DEPT` | present, non-empty, ∈ known depts (read from `kb_config.DEPT_LABELS` keys so it stays single-sourced) |
| `last_modified` | `E_BAD_DATE` | matches `^\d{4}-\d{2}-\d{2}$` **and** parses via `date.fromisoformat`. Accepts both a quoted string and a PyYAML-parsed `datetime.date` (the renderer's `related_for` already notes unquoted dates parse to `date`) |
| `page_id` / `source_url` (native) | `E_NATIVE_HAS_CONFLUENCE_FIELD` | must be absent/empty |
| `page_id` / `source_url` (confluence) | `E_MISSING_CONFLUENCE_FIELD` | must be present, non-empty |
| `tags` shape | `E_BAD_TAGS` | if present: a list of non-empty strings (empty list OK) |
| `audience` shape/values | `E_BAD_AUDIENCE` | if present: a list ⊆ `{students, faculty, staff, IT}` |
| `visibility` | `E_BAD_VISIBILITY` | present and == `public` (see §3.1) |
| slug/filename match (native) | `E_SLUG_MISMATCH` | `filename stem == slugify(title)`; uses the local copy of `slugify` |

**Why slug-match is native-only.** Exported filenames are already `slugify(title)` by construction
(`canonical_filename`), but enforcing it on the legacy corpus risks flagging a hand-touched legacy
file; the native path is where authors hand-type filenames in the GitHub UI, so that's where the
check earns its place. (If the dry-run over the 28 pages comes back clean, we can widen it to both
origins — noted as a follow-up, not a v1 requirement.)

**Thinness.** ~120–150 lines: stdlib (`re`, `sys`, `pathlib`, `datetime`, `argparse`) + `pyyaml`.
No new dependency — `pyyaml` is already installed by `deploy.yaml` and used by `render.py`. No
import of the export package (§2.5).

**Importable.** Public function `validate_file(path) -> list[str]` (returns error strings, empty =
valid) and `validate_text(text, filename) -> list[str]`. The `__main__` block wraps these for the
CLI. This lets the unit tests (§9) call the logic directly without spawning a process.

### 3.1 The `visibility: public` field — decision

**Decision: YES — the drafter always emits `visibility: public`, and `check_frontmatter.py`
enforces `visibility == "public"` as a fail-closed backstop. This is a hard CI failure, not a
warning.**

**Justification against VISION P4 ("Public-safe by construction; the pipeline fails closed").**

- On this site, **merge = publish to the public internet.** There is no per-page access control
  (RBAC is explicitly out of VISION scope). So the *only* safe default a page can carry is an
  explicit, machine-checkable assertion that it was authored to be public.
- A required `visibility: public` field turns "is this OK to be public?" from an implicit
  assumption into an **explicit, enforced declaration**. It cannot be satisfied by silence — a
  page that omits it, or that says anything other than `public`, **fails CI and cannot merge.**
  That is "fails closed" in the literal P4 sense.
- It is defense-in-depth layered with the human gate (§5), not a replacement for it: the human
  reviewer still asks "should this actually be public?"; the field guarantees the machine refuses
  anything that doesn't even *claim* to be. If a future phase introduces non-public content, the
  field is already the natural kill-switch (`visibility: internal` → CI rejects it from this public
  repo) — so the marker pays forward into the gated-access phase without rework.
- Cost is near-zero: one line the drafter emits, one regex the validator runs. Cheap insurance on
  the single highest-severity risk (an access-restricted page reaching the public site).

**Backfill for the 28 existing pages.** They predate the field. To avoid a flag-day, the
`confluence` branch treats a **missing** `visibility` as `public` *only for already-merged
exported pages* — i.e. the requirement is enforced on **changed files in a PR** (CI only validates
the diff; §4). A one-time follow-up PR backfills `visibility: public` into the existing exported
pages and into the export tool's `build_frontmatter` so all *future* exports carry it too; after
that, `visibility` can be made unconditionally required. This sequencing keeps the export path
working today without weakening it.

---

## 4. CI design — `.github/workflows/validate-content.yaml`

```yaml
name: Validate content frontmatter
on:
  pull_request:
    paths:
      - "site/content/**/*.md"
jobs:
  validate:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }          # need the merge base to diff
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pyyaml
      - name: List changed content files
        id: changed
        run: |
          git diff --name-only --diff-filter=d \
            origin/${{ github.base_ref }}...HEAD -- 'site/content/**/*.md' > changed.txt
          cat changed.txt
      - name: Validate changed frontmatter
        run: python tools/check_frontmatter.py --changed-only changed.txt
```

**Trigger.** `pull_request` filtered to `site/content/**/*.md`. A PR that touches no content
markdown doesn't run it (and doesn't need to). A PR that does touch content **must** pass it before
merge — enforced by marking this check **required** in branch protection on `main` (a one-time
repo-settings step, documented in the implement phase).

**Why it fails closed.** `check_frontmatter.py` exits non-zero on any failure; GitHub marks the
required check failed; "Merge" is disabled. There is no path where an invalid page merges silently.
`--diff-filter=d` excludes deletions (a deleted file can't be validated and shouldn't block).

**Why validate only changed files.** (a) Speed and signal — the author sees errors about *their*
page. (b) It lets the `visibility` backfill (§3.1) be lazy: untouched legacy pages aren't
re-validated under the new stricter rule until they're edited. A nightly/full sweep can be added
later if drift becomes a concern; v1 validates the diff.

**Coexistence with `deploy.yaml`.** They are independent jobs on different triggers:

| | `validate-content.yaml` | `deploy.yaml` |
|---|---|---|
| Trigger | `pull_request` (content paths) | `push` to `main` + `workflow_dispatch` |
| Job | run validator on the diff | render + deploy to Pages |
| Effect | gate the PR | publish merged content |
| Permissions | default read-only | `pages: write`, `id-token: write` |

No shared concurrency group, no shared steps, no edit to `deploy.yaml`. Validation happens
**before** merge; deploy happens **after**. The validator never deploys; the deploy job never
validates — clean separation, and `deploy.yaml` stays byte-for-byte as it is today.

---

## 5. CODEOWNERS + PR template — the human gate

### 5.1 `CODEOWNERS` (repo root or `.github/CODEOWNERS`)

```
# Any content change requires publish-safety review before merge.
/site/content/**           @<reviewer-handle>

# The governance tooling itself is owned too (don't let the gate be edited unreviewed).
/tools/check_frontmatter.py        @<reviewer-handle>
/.github/workflows/                 @<reviewer-handle>
/CODEOWNERS                         @<reviewer-handle>
/.github/pull_request_template.md   @<reviewer-handle>
```

`@<reviewer-handle>` is the publish-safety reviewer (initially Julian as the technical steward; the
implement phase confirms the real SU handle with Aaron). CODEOWNERS only *requests* review by
default — it becomes a **gate** when branch protection on `main` enables "Require review from Code
Owners." That toggle, plus "require the validate-content check," are the two repo-settings steps
that make the gate real (documented as implement-phase tasks, since they're settings not files).

Note CODEOWNERS also guards the gate's own files — so a PR can't quietly disable the validator or
reroute review.

### 5.2 `.github/pull_request_template.md`

A short checklist the reviewer must satisfy before approving. The body is plain markdown that
GitHub auto-loads into every PR description:

```markdown
## Publish-safety checklist (required before merge)

> Merging to `main` publishes this content to the PUBLIC internet
> (HTML + raw .md + the llms.txt retrieval index). There is no access control.

- [ ] **Public-safe:** This content is OK to be visible to anyone on the internet
      (no FERPA/PII, no internal-only, no access-restricted material).
- [ ] **Frontmatter sane:** Validate-content CI is green. Title, description,
      department, and tags read correctly.
- [ ] **Right place:** The file is under the correct `site/content/<dept>/<area>/`
      and the filename matches the title slug.
- [ ] **Native vs exported:** A net-new page has `origin: native` and NO
      `page_id` / `source_url`. (CI enforces this — confirm it wasn't bypassed.)
- [ ] **visibility: public** is present.

### What is this page? (author fills in)
- Source of the content:
- Department / area:
- Anything a reviewer should double-check:
```

The checklist operationalizes VISION P4 for the human: the top line states the stakes (public,
no access control), and the first box is the one that matters most — *is this content OK to be
public?* CI handles the mechanical checks; the human owns the judgment CI can't make.

---

## 6. The drafter — skill/prompt artifact (content, not a service)

The drafter is **instructions**, not runtime code: a Claude **Agent Skill** (runs in SU Claude
Enterprise / Claude.ai — Agent Skills are supported there now, not just Claude Code) **plus** a
copy-paste prompt fallback for anyone who can't install the skill. No server, no API key, zero new
infrastructure (P6).

**Packaging decision.** Lead with the **Agent Skill** as the primary distributable (installable
once, reusable, discoverable in the SU Claude Enterprise workspace), and ship the **identical
instruction body as a copy-paste prompt** in the repo (`skill/drafter-prompt.md`) as the
no-install fallback. Both carry the *same* schema rules — single source of truth, two delivery
vehicles. (Research recommended a shared Project/prompt because a Claude *Code* skill wouldn't
reach Enterprise users; the resolved understanding is that Agent Skills now run in Enterprise, so
the skill is viable as the lead — with the prompt as the guaranteed-reachable fallback. The
implement phase confirms SU Enterprise's skill-install affordance before committing.)

**Artifact location.** `skill/` (the repo already reserves this folder; today it holds only
`CONTEXT.md`). Add:
- `skill/SKILL.md` — the skill manifest + instruction body.
- `skill/drafter-prompt.md` — the same instructions as a paste-in prompt.

**What the instruction body must contain** (this is the spec for the content of the drafter):

1. **Role + the one warning, up top:** "You draft a page for SU's PUBLIC knowledge base.
   Everything you produce, once merged, is visible to anyone on the internet and to AI agents.
   Never include access-restricted, FERPA/PII, or internal-only material. When unsure, leave it
   out and tell the author."
2. **The native-page convention:** emit `origin: native`; **do NOT** emit `page_id` or
   `source_url` (those are Confluence-only). Emit `visibility: public`.
3. **The exact frontmatter schema + order** the validator and renderer expect, with a worked
   template:
   ```yaml
   ---
   title: <canonical page title>
   description: <one-line summary; SEO + LLM snippet — required, non-empty>
   department: data-ai
   last_modified: <YYYY-MM-DD, today's date>
   tags: [<lowercase-kebab topic tags>]
   audience: [students, faculty, staff]   # add IT only if relevant
   origin: native
   visibility: public
   ---
   ```
   (Order mirrors the export emit order with the two Confluence fields removed and the two
   governance fields appended.)
4. **Slug + filename rule, matching `slugify()` exactly:** lowercase; normalize `—`/`–` to `-`;
   replace every run of non-`[a-z0-9]` with a single `-`; trim leading/trailing `-`; empty →
   `untitled`. Filename = `<slug>.md`. Give 2–3 worked examples (e.g.
   `"Claude — Frequently Asked Questions"` → `claude-frequently-asked-questions.md`) so the model
   reproduces it deterministically.
5. **Path template + taxonomy:** target path is
   `site/content/<department>/<area>/<slug>.md`. Provide the current legible taxonomy so the
   author picks an existing area or proposes a sensible new one:
   - `data-ai/ai-general-information`, `data-ai/claude` (+ `claude/example-uses`),
     `data-ai/clementine-platform`, `data-ai/copilot`, `data-ai/gemini`.
   Instruct: infer the best area from content, then **confirm with the author**, listing the
   options.
6. **Body rules (dual-consumer, P3):** clean GitHub-Flavored Markdown; `##`/`###` headings (the
   renderer builds the ToC and anchors from h2/h3); GitHub-style callouts `> [!warning]` /
   `> [!tip]` / `> [!note]` are supported; in-corpus links are ordinary relative `.md` links
   (NOT `[[wikilinks]]`); a `## Related` section is optional (the renderer auto-generates one from
   shared tags if absent).
7. **The GitHub handoff (terminal-free), as explicit steps:** "Output (a) the full file contents
   in one copy-able block, and (b) the exact path. Then tell the author: go to the repo on
   github.com → **Add file → Create new file** → paste the path into the filename box (GitHub
   creates the folders) → paste the contents → **Commit changes → to a new branch → Propose
   changes** → this opens a Pull Request. A reviewer will check it; once approved and merged, the
   page goes live automatically."
8. **Self-check before handoff:** the drafter restates the validator's rules as a checklist it
   verifies against its own output (no `page_id`/`source_url`; `visibility: public`; date is
   `YYYY-MM-DD`; filename == slug; description non-empty) — so the common CI failures are caught
   before the author ever opens GitHub.

The drafter is plain markdown content. It has **no service, no endpoint, no cost** — it is read by
Claude at drafting time and produces a file. CI + CODEOWNERS remain the authoritative gate; the
drafter's self-check is convenience, not trust.

---

## 7. Reuse vs net-new

| Concern | Reuse (exists, verified) | Net-new (this feature owns) |
|---|---|---|
| 8-field schema definition | `export-tool/.../frontmatter.py` docstring + field list | `origin` + `visibility` governance markers |
| `slugify` / filename convention | logic in `export-tool/.../frontmatter.py` | a ~15-line local copy in `check_frontmatter.py` (drift-tested, §9) |
| Department resolution | `render.py:142` `meta.get("department") or parts[0]` | dept allow-list read from `kb_config.DEPT_LABELS` |
| Auto-indexing / retrieval | `render.py` `load_corpus` + `emit_llms_txt`; `deploy.yaml` on push | nothing — works as-is |
| Taxonomy | `site/content/data-ai/*` tree | nothing — drafter just lists it |
| Submission path | GitHub web UI create-file → PR | nothing — drafter instructs it |
| Frontmatter validation | (export validator — export-path only) | **`tools/check_frontmatter.py`** (native-aware) |
| PR gate (machine) | — | **`.github/workflows/validate-content.yaml`** |
| PR gate (human) | — | **`CODEOWNERS`** + branch-protection toggles |
| Reviewer checklist | — | **`.github/pull_request_template.md`** |
| Drafting capability | SU Claude Enterprise (the model) | **`skill/SKILL.md`** + **`skill/drafter-prompt.md`** |
| Scaffolding a blank page | `render.py` picks up any correctly-placed file | **`tools/new_page.py`** — *recommend SKIP for v1* (below) |

**Net-new file count: 6** (`check_frontmatter.py`, `validate-content.yaml`, `CODEOWNERS`,
`pull_request_template.md`, `skill/SKILL.md`, `skill/drafter-prompt.md`) — **7** if `new_page.py`
is built.

**`new_page.py` — recommend SKIP for v1.** The drafter emits the *full* file (frontmatter + body)
and the exact path; the author pastes it into GitHub's create-file box, which creates folders
automatically; the renderer auto-picks-it-up (verified). A scaffolder that writes an *empty* shell
adds a CLI step the non-technical author can't run anyway, and duplicates slug/path logic that now
lives in both the drafter (instructions) and `check_frontmatter.py` (enforcement). It earns its
place only for the *technical maintainer* fallback path (REQUEST secondary user). Defer it to a
fast-follow if that user asks; don't gate v1 on it. (P6: fewer moving parts.)

---

## 8. Technical risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Gate not actually enforcing** — CODEOWNERS only *requests* review and a CI check is only advisory until branch protection requires it | **High (P4)** | The implement phase MUST flip two repo settings on `main`: "require the validate-content check" + "require review from Code Owners." Add a manual acceptance test (§9) that opens a deliberately-invalid PR and confirms Merge is blocked. The files alone don't make the gate; the settings do. |
| **Schema fork mis-resolved** — native page rejected, or export contract weakened | **High** | Explicit `origin:` discriminator with `page_id`-presence fallback (§2.2); export `frontmatter.py` left untouched; CI dry-run over the 28 existing pages must stay green (§9). |
| **Drafter emits subtly-invalid YAML** — smart-quotes, `last_modified` as a bare date PyYAML reads oddly, tab indentation, a stray `page_id` copied from an exported page | **Medium** | (a) Validator accepts both quoted-string and PyYAML-`date` for `last_modified`. (b) Drafter self-check (§6.8) restates the rules. (c) CI is the catch-all backstop — a bad draft fails the PR, never the public site. (d) `E_NATIVE_HAS_CONFLUENCE_FIELD` specifically catches the "pasted an exported header" mistake. |
| **`visibility` backfill flag-day** — making it required breaks the 28 legacy pages | Medium | CI validates only the diff (§4), and the `confluence` branch treats missing `visibility` as public until a one-time backfill PR lands (§3.1). No flag-day. |
| **Cross-package `slugify` drift** — local copy diverges from export source of truth | Low–Med | Unit test asserts byte-identical output across a fixture set (§9). If it ever diverges, the test fails before merge. |
| **Friction floor** — author still needs a GitHub account + PR literacy (cannot be removed without a backend, which is out of scope) | Medium–High (product) | Out of this spec's engineering control; mitigated by the drafter's explicit step-by-step GitHub handoff (§6.7) + a one-page screenshot guide (implement-phase doc). Acceptability is a stakeholder call for Aaron (carried from research, owned in `pm.md`). |
| **Department typo bypasses taxonomy** — author invents `data_ai` and the renderer happily makes a new dept | Low | `E_BAD_DEPT` checks `department` against `kb_config.DEPT_LABELS` keys; a new department is an intentional, reviewed act, not a typo. |
| **Drafter packaging assumption** — Agent Skills may not be installable in SU's specific Enterprise tier | Low | The copy-paste prompt fallback (`drafter-prompt.md`) is identical and needs no install — it always works. Skill is the convenience lead, prompt is the floor. |

---

## 9. Testing strategy

**Unit tests — `tools/check_frontmatter.py`** (pytest, runnable locally and in CI; call
`validate_text`/`validate_file` directly):

| Case | Expectation |
|---|---|
| Valid **native** page (origin: native, no page_id/source_url, visibility: public, slug matches) | passes, exit 0 |
| Native page **with** a non-empty `page_id` | fails `E_NATIVE_HAS_CONFLUENCE_FIELD` |
| Native page **missing** `visibility` (or `visibility: internal`) | fails `E_BAD_VISIBILITY` |
| Native page **missing** `description` | fails `E_MISSING_DESC` |
| Native page filename ≠ `slugify(title)` | fails `E_SLUG_MISMATCH` |
| Valid **exported** page (page_id + source_url present) | passes — export contract preserved |
| Exported page **missing** `source_url` | fails `E_MISSING_CONFLUENCE_FIELD` |
| `last_modified` = `2026/06/08` or `June 8 2026` | fails `E_BAD_DATE` |
| `last_modified` as PyYAML-parsed `date` (unquoted `2026-06-08`) | passes (both forms accepted) |
| Malformed YAML (bad indentation) | fails `E_BAD_YAML` |
| No frontmatter block | fails `E_NO_FRONTMATTER` |
| `audience: [students, alumni]` (unknown value) | fails `E_BAD_AUDIENCE` |
| `department: data_ai` (not in allow-list) | fails `E_BAD_DEPT` |
| **`slugify` drift guard** | local `slugify` output == export `slugify` output across a fixture title set |

**CI dry-run (acceptance):** run `python tools/check_frontmatter.py site/content/` over the **28
existing exported pages** — must exit 0 (proves the validator doesn't break the current corpus and
the `confluence` branch + lazy-`visibility` rule are correct). Wire this as a one-shot check during
implementation before turning the required-check on.

**CI behavior test:** open a throwaway PR that edits a content page to be invalid → confirm
`validate-content` runs, fails, and (with branch protection on) **blocks Merge**. Then fix it →
confirm green → Merge enabled. This proves the gate fails closed (the §8 top risk).

**End-to-end manual test (the real user journey):**
1. In SU Claude Enterprise, run the drafter on a small source doc → get a full `.md` file + exact
   path.
2. Paste into GitHub web UI (Add file → Create new file → path → contents) → Commit to a new branch
   → Propose changes (PR).
3. Confirm `validate-content` CI goes **green** on the drafted file.
4. CODEOWNERS requests the reviewer; reviewer runs the PR-template checklist; approves.
5. Merge → `deploy.yaml` runs → within a minute or two the page is live at
   `…/su-kb-site/data-ai/<area>/<slug>.html`, the raw `.md` mirror exists, and the page **appears
   as a new line in `/llms.txt`** (proves dual-consumer + auto-indexing, P3).
6. Negative pass: repeat step 1–2 but leave `visibility` off / paste an exported header → confirm
   CI **blocks** at step 3 (proves P4 fail-closed end to end).

**Out of automated scope (manual/stakeholder):** the friction-floor acceptability and demand
confirmation (Aaron) — tracked in `pm.md`, not a test here.

---

## 10. Build sequence (milestones, not timeline)

1. **The gate first (safety before capability).** `check_frontmatter.py` + unit tests → CI
   dry-run green over the 28 pages → `validate-content.yaml` → `CODEOWNERS` +
   `pull_request_template.md` → flip the two branch-protection settings → run the CI-behavior test.
   *Done = an invalid content PR cannot merge.*
2. **The drafter.** `skill/drafter-prompt.md` (the instruction body) → `skill/SKILL.md` wrapper →
   dry-run the drafter on one real source doc and validate its output locally with
   `check_frontmatter.py`. *Done = the drafter reliably emits a file that passes the validator.*
3. **End-to-end + the friction-lowering doc.** Run the full manual journey (§9) → write the
   one-page screenshot guide for the GitHub handoff. *Done = a page drafted in Claude reaches the
   live site and llms.txt through the gate.*
4. **Fast-follows (not v1 blockers):** `visibility` backfill PR over legacy pages + export tool;
   optional `tools/new_page.py` for the technical maintainer; widening slug-match to both origins
   if the dry-run is clean.

Each milestone is independently reversible: the validator and CI can be added without touching
`deploy.yaml`; the drafter is inert content; branch-protection toggles are settings, not code.
