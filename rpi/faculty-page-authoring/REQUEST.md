# Faculty Page Authoring — Claude-native drafting on top of the contribution guardrails

## What
A Claude-native authoring assistant that lets a non-technical contributor (especially an
SU faculty member) turn *"here are some docs, help me write a page"* into a clean,
schema-valid `su-kb-site` page and get it onto the live site — **without touching a
terminal or git**. Drafting happens inside SU's existing (free) Claude Enterprise; the page
lands via GitHub's own web UI; the page then flows through the contribution guardrails
(frontmatter validation in CI + a human CODEOWNERS review) before merge publishes it.

This is the **AI draft-generation front-end** that sits *on top of* the
mechanical/governance back-end Robert already designed
(`new_page.py` scaffolder, `check_frontmatter.py` validator, `validate-content.yaml` CI,
`CODEOWNERS` reviewer, PR template). It does not rebuild that back-end — it feeds it.

## Why
The site pivoted: hand-authored markdown is now the source of truth, and **merge = publish
to a public site**. Robert built the contribution guardrails, but his runbook is
developer-grade — `git checkout -b`, `python tools/new_page.py`, local `render.py`, push, PR.
A faculty member won't (and shouldn't have to) do that. The two missing halves are exactly
the ones a non-technical author needs most:

1. **Draft generation (the AI task):** producing clean GFM + valid 8-field frontmatter from
   raw source docs. Robert's scaffolder writes an *empty* valid shell; it doesn't write the
   page.
2. **A seamless, terminal-free path** for someone who has SU Claude Enterprise and a GitHub
   account but has never used a CLI.

Without this, only technical staff can contribute, and the vision — *SU owns **and
maintains** its knowledge in markdown* — stalls at the migration boundary.

## Who
- **Primary:** a non-technical SU faculty/staff contributor. Has SU Claude Enterprise access
  (approved AI tool, `syr.edu` sign-in) and a GitHub account. Wants to add or update one
  page. Will not open a terminal, clone a repo, or run Python.
- **Secondary:** a technical maintainer (Julian / future SU steward) who can fall back to
  Robert's fuller CLI runbook when needed.
- **The publish-safety reviewer:** the CODEOWNERS admin/IT reviewer who approves before merge
  (the human gate is retained — see Scope).

## Scope
**In:**
- A Claude-native **drafter**: takes source docs + a few answers → clean GitHub-Flavored
  Markdown + a valid **8-field frontmatter** block (`title`, `description`, `page_id`,
  `department`, `source_url`, `last_modified`, `tags`, `audience`), using the **native-page
  convention** (omit `page_id` / `source_url` — they're Confluence-only).
- **Placement guidance**: the drafter tells the author the exact target path
  (`site/content/<department>/<area>/<slug>.md`) and slug, matching Robert's `new_page.py`
  folder/slug convention — so the renderer and sidebar pick the page up automatically.
- A **terminal-free submission path** via the GitHub web UI (create-file-in-browser →
  "propose changes" → PR), handing off to Robert's CI + CODEOWNERS gates.
- **Self-serve authoring with the human publish gate retained**: the faculty member drafts
  and opens the PR themselves (no steward operates the tool), but the CODEOWNERS human
  reviewer still approves before merge. "Self-serve" = no operator needed, **not** zero
  review.
- **Free only**: drafting on SU Claude Enterprise; submission on GitHub web UI. No paid LLM
  API, no hosted backend.
- Integrate with — not duplicate — Robert's guardrail files.

**Out:**
- A hosted web form / custom backend / paid LLM API (cost + thin-tooling principle).
- Replacing or rewriting Robert's `new_page.py` / `check_frontmatter.py` / CI / CODEOWNERS —
  reuse them as the back-end.
- Removing the human review gate (explicitly kept; see VISION principle 4).
- Per-user RBAC / authentication (everything is public on GH Pages — VISION out-of-scope).
- Confluence sync / migration (the export tool's job; this is **net-new** authoring).
- Eliminating the GitHub-account requirement (can't be removed without a backend — accepted
  as the friction floor; see Open questions).
- Building the Skill page-map auto-sync (Robert's §8 item) — related but a separate concern;
  noted as an open question only.

## Constraints
- **Free / no new infrastructure.** SU Claude Enterprise + GitHub web UI only; no new API
  key, no backend to host. Honors the API-spend discipline (drafting rides the existing
  Claude seat, not a metered key).
- **VISION alignment.** Principle 4 (public-safe, fails closed) → human gate retained.
  Principle 6 (thin, inspectable tooling, no framework creep). Principle 2 (markdown-native
  output). Principle 3 (dual-consumer — every page must serve both a human reader and
  Claude's `WebFetch`).
- **Schema fidelity.** Output must satisfy the exact 8-field schema and native-page
  convention that Robert's `check_frontmatter.py` enforces, or CI will block the PR.
- **Depends on Robert's guardrails landing.** As of 2026-06-04 those six files are a proposal
  (in a Downloads doc), **not yet merged** into the repo — this feature assumes they ship.

## Open questions
*(for `/rpi:research` to resolve — GO/NO-GO gate)*

1. **GATE 0 — is Robert's guardrail set actually in the repo?** `tools/new_page.py` and the
   CODEOWNERS/CI files are not present yet. Research must verify their real state before
   building on top of them.
2. **The friction floor.** The GitHub web-UI path still requires a faculty member to have a
   GitHub account, repo access, and to understand "propose changes / pull request." Is that
   acceptably seamless, or does it sink the goal — and is there a *free* way to lower it
   further (e.g. a guided issue-form, a single deep link into the create-file UI)?
3. **Packaging of the drafter.** Installable Claude *skill* vs a shared Claude.ai/Enterprise
   *Project* vs a copy-paste *prompt* — which is most distributable to non-technical staff
   who have SU Claude but **not** Claude Code?
4. **Draft → placement handoff without `new_page.py`.** Should Claude emit the full file +
   exact path for the author to paste into GitHub's "create file" box? Will that reliably
   match Robert's folder/slug convention without the author running the scaffolder?
5. **Department/area selection.** How does a non-technical author pick the right
   `department/<area>` namespace — does the drafter infer it from content, or offer a list?
6. **Skill page-map sync (Robert §8).** A new page needs a line added to `skill/SKILL.md`'s
   page map — a developer step a faculty member can't do. Does this need to move into CI
   before self-serve is genuinely real?
7. **`visibility: public` field (Robert §7 gap).** Should the drafter always emit a
   `visibility: public` marker as a fail-closed backup to human review — and does that field
   need to be added to the validator's schema?
