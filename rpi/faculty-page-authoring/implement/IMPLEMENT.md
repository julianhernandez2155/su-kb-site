# Implementation Record — Faculty Page Authoring

**Feature**: faculty-page-authoring
**Started**: 2026-06-08
**Status**: IN_PROGRESS

Grounded in [`plan/PLAN.md`](../plan/PLAN.md) and [`plan/eng.md`](../plan/eng.md). Phases follow
PLAN.md. PLAN Phase 0 (pre-flight) is stakeholder/settings work tracked separately; code
implementation starts at **Phase 1 (the gate)**.

---

## Phase 1: The Gate (safety back-end) — *critical path*

**Date**: 2026-06-08
**Verdict**: **PASS** (files/validator level) — Julian advanced to `--phase 2`, an implicit PASS
on the Phase 1 files. The live fail-closed proof (tasks 1.7/1.8, branch-protection settings +
blocked-PR test) remains Julian-executed on the pushed repo per
[`branch-protection.md`](branch-protection.md); it is the one open item under this phase.

### Deliverables (files committed to the working tree)
- [x] **1.1** [`tools/check_frontmatter.py`](../../../tools/check_frontmatter.py) — native-aware
      validator. CLI (`paths` / `--changed-only` / `--quiet`) + importable
      (`validate_file` / `validate_text`). Origin resolution: explicit `origin:` → `page_id`
      inference → `native`. Mirrors the renderer's `text.split("---", 2)` parse convention so
      "what validates == what renders". `slugify` is a local copy of the export source of truth
      (drift-guarded). `DEPT_LABELS` read from `kb_config` (single-sourced). ~270 lines, stdlib +
      pyyaml only (no new dep, no export-package import — P6).
- [x] **1.2** [`tools/test_check_frontmatter.py`](../../../tools/test_check_frontmatter.py) — 17
      tests: the 13-case matrix (eng.md §9) + origin-resolution coverage + the **slugify drift
      guard** asserting byte-identical output vs `su_kb_export.frontmatter.slugify`.
- [x] **1.3** CI dry-run — `python tools/check_frontmatter.py site/content/` → **29 files, 29
      passed, 0 failed, exit 0**. The `confluence` branch + lazy-`visibility` rule don't break the
      live corpus.
- [x] **1.4** [`.github/workflows/validate-content.yaml`](../../../.github/workflows/validate-content.yaml)
      — `pull_request` trigger on `site/content/**/*.md`, validates the diff via `--changed-only`,
      fails closed. Read-only permissions. Independent of `deploy.yaml` (which is unchanged).
- [x] **1.5** [`CODEOWNERS`](../../../CODEOWNERS) — routes `site/content/**` **and the gate's own
      files** to the reviewer (repo owner as initial steward; SU handle TBD via Phase 0.2).
- [x] **1.6** [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) — the
      publish-safety checklist (public-safe? frontmatter sane? right place? native vs exported?
      visibility present?).
- [ ] **1.7 / 1.8** Branch-protection settings + CI-behavior test — **runbook written**
      ([`branch-protection.md`](branch-protection.md)); the actual settings flip + live-PR test
      require GitHub admin on the pushed repo and are **Julian-executed**, not doable from the
      working tree.

### Files Changed
| File | Change | Lines |
|------|--------|-------|
| `tools/check_frontmatter.py` | add | +~270 |
| `tools/test_check_frontmatter.py` | add | +~190 |
| `.github/workflows/validate-content.yaml` | add | +52 |
| `CODEOWNERS` | add | +21 |
| `.github/pull_request_template.md` | add | +20 |
| `rpi/.../implement/branch-protection.md` | add (runbook) | +60 |
| `deploy.yaml` | **unchanged** | 0 |

### Test Results (self-validation, 2026-06-08)
- **Unit:** `py -3 -m pytest tools/test_check_frontmatter.py -q` → **17 passed** (incl. slugify
  drift guard, which ran — not skipped).
- **Acceptance (dry-run):** validator over the 29 existing pages → **29 passed, exit 0**.
- **Negative (fail-closed):** a native page missing `visibility` + `description` via
  `--changed-only` → `E_BAD_VISIBILITY` + `E_MISSING_DESC`, **exit 1**.
- **Workflow YAML:** parses as valid YAML.
- _Stack note:_ repo Python is the hermes venv without pip/pytest; tests run under `py -3`
  (Python 3.14, pytest 9.0.3) which has pyyaml. The CI workflow installs pyyaml on 3.12.

### Code Review
- Self-validated (unit + integration + negative). Native `/code-review --fix` not auto-run
  (session context budget); available for Julian to run on the diff before commit.

### Notes
- **Not yet committed** (per standing rule: commit only when asked).
- The gate is **files-complete but not settings-active** until 1.7 is done on the pushed repo —
  this is the deliberate, documented boundary (the §8 top risk). Phase 1's success criteria are met
  at the file/validator level; the live fail-closed proof is task 1.8.

---

## Phase 2: The Drafter (skill + prompt)

**Date**: 2026-06-08
**Verdict**: **PASS** — Julian advanced to `--phase 3` (implicit PASS), after requesting and
receiving the house-style enhancement (2.3a).

### Deliverables
- [x] **2.1** [`skill/drafter/drafter-prompt.md`](../../../skill/drafter/drafter-prompt.md) — the
      instruction body as a no-install copy-paste prompt: role + "everything is PUBLIC" warning,
      native convention (`origin: native`, no `page_id`/`source_url`, `visibility: public`), the
      exact 8-field+governance template in emit order, the `slugify` rule with 3 worked examples,
      path template + the 5-area taxonomy, dual-consumer GFM body rules, the terminal-free GitHub
      handoff (with the pre-filled `/new/main?filename=` deep link), and the pre-handoff self-check.
- [x] **2.2** [`skill/drafter/SKILL.md`](../../../skill/drafter/SKILL.md) — the same body wrapped as
      an Agent Skill (manifest frontmatter + instructions). **Instruction body verified
      byte-identical** to the prompt (10,666 chars each) — single source of truth, two vehicles.
- [x] **2.3** Conversation design + all interaction states encoded from [`ux.md`](../plan/ux.md):
      propose-and-confirm question order (area → audience → title), the mandatory public-safety
      checkpoint before emit, and an 8-row interaction-state table (empty / gathering / ready /
      ambiguous-area / missing-info / sensitive-source / GitHub-confusion / waiting-for-review),
      plus the Plan-B maintainer-assisted escape hatch.
- [x] **2.3a (added on Julian's request)** A **house-style guide** so drafts match the existing
      corpus's look: page shape (no body H1, `##`/`###` hierarchy, `---` section dividers, clean
      headings), callout usage, bold-term lists, numbered steps, tables for reference matrices,
      cross-link/`## Support`/`## Keep in mind` conventions, and four **page-type skeletons**
      (overview / how-to / FAQ / reference). Drawn from reading 5 representative live pages, and
      **corrected to what this site's renderer actually renders** (see the renderer finding below).
- [x] **2.4** **Dry-run validated** — simulated drafter output for a real source
      (`Using Claude for Syllabus Design`) → [`dryrun/`](dryrun/) → passes
      `check_frontmatter.py` with **zero hand-editing, exit 0**.

### Design deviation from PLAN (recorded)
The plan named the files `skill/SKILL.md` + `skill/drafter-prompt.md`. But the `skill/` folder's
identity is already reserved (in the project README/CLAUDE.md and `skill/CONTEXT.md`) for the
**read-side retrieval skill** (WebFetch routing), which is a *different* skill and not yet built.
An Agent Skill is a folder whose `SKILL.md` is its entry point, so two skills can't share one
`skill/SKILL.md`. Resolution: the drafter lives in its own subfolder **`skill/drafter/`**; the
future retrieval skill gets `skill/retrieval/`. [`skill/CONTEXT.md`](../../../skill/CONTEXT.md)
updated to document the two-skill layout. No behavioral change; only placement.

### Files Changed
| File | Change | Lines |
|------|--------|-------|
| `skill/drafter/SKILL.md` | add | +~210 |
| `skill/drafter/drafter-prompt.md` | add | +~205 |
| `skill/CONTEXT.md` | modify (two-skill layout) | +~30 |
| `rpi/.../implement/dryrun/using-claude-for-syllabus-design.md` | add (test fixture) | +55 |

### Test Results (self-validation, 2026-06-08)
- **Integration (2.4):** drafter dry-run output → `py -3 tools/check_frontmatter.py …` → **OK, exit 0**.
- **Negative (drafter mistakes the gate must catch):** a pasted exported header → `E_NATIVE_HAS_CONFLUENCE_FIELD` ×2; a filename ≠ `slugify(title)` → `E_SLUG_MISMATCH`; both **exit 1**.
- **Single-source check:** SKILL.md and drafter-prompt.md instruction bodies are **byte-identical**.

### Code Review
- Self-reviewed (drift check + validator agreement). These are markdown *content* files (no code
  path), so a `/code-review --fix` pass is low-yield; available for Julian to run on the diff.

### Renderer finding (worth a learnings entry at session close)
Reading the corpus to extract house style surfaced a real rendering issue in
[`tools/render.py`](../../../tools/render.py) `callout_plugin`:
- The kind is collapsed to **only `warning` / `tip` / `note`** (`render.py:72`) — `[!info]`
  renders identically to `[!note]`.
- The **collapsible `> [!note]-` form does NOT collapse** on this site. The alert regex
  (`render.py:39`) captures the trailing `-` into the callout title, so it shows as stray text.
  Several exported mentorAI pages (e.g. `mentorai-settings-options.md`) use `[!note]-` heavily and
  are therefore rendering slightly degraded. **Not fixed here** (out of Phase 2 scope); the drafter
  is told to avoid the `-` form, and this is flagged as a candidate fast-follow / bug.

### Notes
- **Not yet committed** (per standing rule: commit only when asked).
- The drafter's self-check is convenience, not trust — CI (`check_frontmatter.py`) + CODEOWNERS
  remain the authoritative gate (eng.md §6 closing).

---

## Phase 3: End-to-end + friction-lowering guide

**Date**: 2026-06-08
**Verdict**: _partial — doc work done; the live E2E (3.1/3.2) is Julian-executed, pending_

### Deliverables
- [x] **3.3** [`docs/authoring/submit-on-github.md`](../../../docs/authoring/submit-on-github.md)
      — the one-page, terminal-free **"Put your page on the Syracuse site — 2 steps"** guide.
      Covers "I have a file from Claude" → "I opened a PR": GitHub vocabulary glosses (repo /
      commit / branch / PR), Step 1 paste, Step 2 submit, "what happens next" (review
      expectation), the public-site warning, and a Plan-B hand-off. **Accessibility per
      [`ux.md` §6](../plan/ux.md):** every step's text stands alone without the image; three
      `📸 Screenshot to add` placeholders carry action-conveying alt text + "name the button in
      text" captions, ready for a designer (`ui-ux-pro-max`/`impeccable`) to drop real captures in.
- [x] **3.3-wire** Linked the guide from the drafter's GitHub handoff (step 5) in **both**
      `skill/drafter/SKILL.md` and `skill/drafter/drafter-prompt.md` (bodies re-verified
      byte-identical, 13,936 chars).
- [x] **3.1 (drafter half) — PROVEN LIVE, 2026-06-08.** Julian installed the skill on **SU Claude
      Enterprise** (answers **Phase 0.1: skill install IS available on SU's tier**) and ran it on a
      real, hard source (his private Hermes integration plan). The skill: triggered by name,
      **stripped all private context**, **independently verified** the Hermes facts before writing,
      **fired the sensitive-source safety behavior**, did propose-and-confirm (area/audience/title),
      hit the public checkpoint, and emitted a native page that **passes `check_frontmatter.py` with
      exit 0** (fetched from GitHub raw and validated locally). House style followed exactly —
      including the **corrected callout rule** (no collapsible `[!note]-`). Page is live:
      `…/data-ai/ai-general-information/hermes-agent-what-it-is-and-how-to-approach-it-safely.html`;
      the flagged cross-link rewrote to `.html` and resolves (HTTP 200).
- [ ] **3.1 (gate half) / 3.2 — NOT yet proven, and this test went AROUND the gate.** The page
      reached the public site **without** CI/CODEOWNERS, because the Phase 1 gate files are **not
      committed/pushed** and branch protection (1.7) isn't set. Content was intentional + public-safe,
      but this is a live demonstration of the exact VISION-P4 risk the gate exists to close: only the
      drafter's self-check + Julian's judgment stood between draft and public. **To make the gate
      real:** commit+push the Phase 1 files → flip branch protection (1.7) → run the negative/blocked
      PR test (1.8/3.2). Runbook: [`branch-protection.md`](branch-protection.md); spec:
      [`eng.md` §9](../plan/eng.md).
- [ ] **3.4** STATUS/log update + approach ADR — do at session close (`/log`, `/decide`).

### Files Changed
| File | Change | Lines |
|------|--------|-------|
| `docs/authoring/submit-on-github.md` | add | +~115 |
| `skill/drafter/SKILL.md` | modify (guide link) | +3 |
| `skill/drafter/drafter-prompt.md` | modify (guide link) | +3 |

### Test Results (self-validation, 2026-06-08)
- Drafter bodies re-verified **byte-identical** after the wiring edit.
- Guide hygiene: **no** `[[wikilinks]]`, **no** broken collapsible `[!note]-` callouts (it
  follows the house style it documents); both drafter files reference the guide URL.
- Dry-run sample still validates **exit 0**.

### Code Review
- Self-reviewed. Markdown docs only — `/code-review --fix` low-yield; available for Julian.

### Notes
- **Not yet committed** (standing rule).
- **Phase 3 cannot be fully closed this session** — its definition-of-done (a page reaching the
  live site through the gate, and the unsafe path provably blocked) requires Julian's GitHub work
  on the pushed repo. The doc half (the friction-lowering guide) is complete and wired.

---

## Summary

**Phases Completed**: Phase 1 PASS · Phase 2 PASS · Phase 3 **doc half done** (the live E2E
3.1/3.2 + the Phase 1 settings 1.7/1.8 are the remaining Julian-executed, GitHub-side items).
**Final Status**: IN_PROGRESS
