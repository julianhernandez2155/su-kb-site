# PRD — Faculty Page Authoring

_RPI Step 3 (Plan / PRD). Generated 2026-06-08. Grounded in `REQUEST.md`, the CONDITIONAL-GO `RESEARCH.md`, `docs/VISION.md` (v1.1), and `docs/STATUS.md`. Reflects the decisions Julian locked 2026-06-08 (GATE 0 owned by this feature, full self-serve target with a Plan B, drafter packaged as a Claude Skill)._

---

## 1. Feature summary

Faculty Page Authoring lets a non-technical SU faculty/staff member turn "here are some docs, help me write a page" into a clean, schema-valid `su-kb-site` page and get it onto the live site — without opening a terminal, cloning a repo, or running Python. Drafting happens inside SU's existing (free) Claude Enterprise via a packaged Claude Skill; the author pastes the result into GitHub's web "create file" UI and opens a pull request; the page then passes through a **fail-closed publish gate this feature builds** — frontmatter validation in CI plus a human CODEOWNERS review — before merge publishes it. Because the governance back-end the feature was originally scoped to "sit on top of" does not exist in the repo (GATE 0 failed in research), this feature now **owns building that gate** (`tools/check_frontmatter.py`, `.github/workflows/validate-content.yaml`, `CODEOWNERS`, a PR template, and a reconciled native-vs-export frontmatter schema) as well as the drafter that feeds it.

---

## 2. VISION alignment

This feature is the markdown-native authoring half the VISION needs, and it maps cleanly to four of the six principles.

- **Principle 2 — Markdown-native.** The drafter's output *is* plain GitHub-Flavored Markdown plus an 8-field YAML frontmatter block. No proprietary store, nothing to un-lock later. Dead-on.
- **Principle 3 — Dual-consumer by design.** A page authored to spec is picked up by the existing renderer, which emits both the HTML page and the `.md` mirror and re-generates `llms.txt` on every deploy. The drafted page serves a human reader and Claude's `WebFetch` by construction — neither is an afterthought.
- **Principle 4 — Public-safe by construction (the tension).** Merge = publish to a public site. A fast drafting path into an *unguarded* pipeline would let an unvalidated or access-restricted page reach the public site — the one thing this principle exists to prevent. **Resolution:** this feature does not ship the drafter alone. It builds and ships the fail-closed gate first: CI rejects any PR whose frontmatter is malformed or off-schema, and a human CODEOWNERS reviewer must approve before merge. "Self-serve" means no operator is needed to *draft and submit* — it does **not** mean zero review. The human gate is the publish-safety control and is explicitly retained.
- **Principle 6 — Thin, inspectable tooling.** The drafter adds zero runtime infrastructure (it's a Claude Skill / prompt). The gate we build is a single small validator script plus a CI YAML and a CODEOWNERS file — all readable end-to-end, no SSG framework, no hosted backend, no framework creep.

Principles 1 (SU-owned end-to-end) and 5 (multi-department-ready) are unaffected and preserved: authoring stays in SU's own Git repo, and the drafter writes into the existing `site/content/<department>/<area>/` namespace structure without restructuring.

---

## 3. User personas & use cases

**Primary — Faculty/staff author (non-technical).**
Has SU Claude Enterprise (approved tool, `syr.edu` sign-in) and a GitHub account with repo access. Has never used a terminal, git CLI, or Python. Wants to add or update **one** page. Their job-to-be-done: "Get the knowledge in my head or my source docs onto the team's site, correctly formatted, without learning developer tooling." This is exactly the user the current developer-grade runbook excludes.

**Secondary — Technical maintainer (Julian / future SU steward).**
Comfortable with the CLI. Operates the Plan B "maintainer-assisted" path when the friction floor blocks a faculty member, and owns the gate's upkeep. Can draft on behalf of an author, or take an author's raw content and land the PR for them.

**The reviewer — CODEOWNERS publish-safety gate.**
An admin/IT/steward reviewer listed in `CODEOWNERS`. Reviews every authoring PR before merge. This is the human fail-closed control for Principle 4: confirms the page is public-safe (no restricted content), on-schema, and correctly placed. Not optional, not automatable — retained by design.

---

## 4. User stories

Plan A = self-serve (faculty drafts and submits, no operator). Plan B = maintainer-assisted fallback (see §7).

| # | Story | Plan |
|---|---|---|
| US-1 | As a faculty author, I want to give Claude my source docs and a few answers and get back a complete page (GFM body + valid 8-field frontmatter), so that I don't have to learn the schema or write YAML by hand. | A |
| US-2 | As a faculty author, I want the drafter to help me **update an existing page** by giving it the page's current `.md`, so that I can revise content without breaking its frontmatter, slug, or placement. | A |
| US-3 | As a faculty author, I want the drafter to tell me which `department/<area>` my page belongs in — inferring it from my content and/or offering the existing folder list — so that I pick the right namespace without knowing the repo structure. | A |
| US-4 | As a faculty author, I want the drafter to give me the **exact target path and filename** (`site/content/<department>/<area>/<slug>.md`), so that I paste it into GitHub's "create file" box and the renderer and sidebar pick it up automatically. | A |
| US-5 | As a faculty author, I want a terminal-free submission path with clear steps (create-file-in-browser → "propose changes" → open PR), so that I land my page using only the GitHub web UI. | A |
| US-6 | As a faculty author, I want the drafter packaged as a Claude Skill I can run inside SU Claude Enterprise (with a copy-paste prompt as a fallback), so that I can use it even though I don't have Claude Code. | A |
| US-7 | As a CODEOWNERS reviewer, I want every authoring PR to require my approval before merge, so that no page reaches the public site without a human public-safety check. | A & B |
| US-8 | As a CODEOWNERS reviewer, I want CI to automatically validate frontmatter (schema, required fields, date format, native-vs-export convention) and block the PR on failure, so that I review content and placement, not YAML syntax. | A & B |
| US-9 | As a maintainer, I want a documented CLI fallback to draft a page and open the PR on a faculty member's behalf, so that authoring still works when the GitHub-account / web-PR friction blocks a non-technical author. | B |
| US-10 | As a maintainer, I want the validator to branch on page origin — native pages omit `page_id`/`source_url`; exported pages require them — so that net-new authored pages and migrated Confluence pages both validate under correct, non-contradictory rules. | A & B |

---

## 5. Acceptance criteria

**US-1 — Draft a new page**
- Given source docs and the author's answers, when the drafter runs, then it emits one complete `.md` file: an 8-field frontmatter block (`title`, `description`, `page_id`, `department`, `source_url`, `last_modified`, `tags`, `audience`) using the **native-page convention** (omit `page_id` and `source_url`), followed by a GFM body.
- `last_modified` is emitted in the documented date-only format and is quoted so it does not crash `render.py`'s related-page sort.
- The emitted file passes `tools/check_frontmatter.py` locally with no errors (the drafter must not produce output CI will reject).

**US-2 — Update an existing page**
- Given the current page's `.md`, when the drafter revises it, then `page_id`/`source_url` status, `department`, slug, and target path are preserved unchanged unless the author explicitly asks to move the page.
- The output is the full revised file (not a diff fragment), ready to replace the existing file in the GitHub web editor.

**US-3 — Department/area selection**
- When content is ambiguous, the drafter presents the current `data-ai/` area list (`ai-general-information`, `claude`, `clementine-platform`, `copilot`, `gemini`) and asks the author to confirm, rather than guessing silently.
- The chosen `<area>` matches an existing folder, or the drafter flags that a new area is being created so the reviewer can confirm it.

**US-4 — Placement / path**
- The drafter outputs the exact string `site/content/<department>/<area>/<slug>.md` with a slug produced by the repo's `slugify` convention.
- The `department` frontmatter value matches the first path segment, so `render.py` resolves the page consistently whether it reads the field or the folder.

**US-5 — Terminal-free submission**
- A non-technical author can go from drafted file to open PR using only the GitHub web UI, following a one-page guide (ideally a single deep link into the create-file UI plus screenshots), with no CLI, clone, or local build.

**US-6 — Packaging**
- The drafter is installed and runnable as a Claude Skill inside SU Claude Enterprise by a user who does **not** have Claude Code.
- A copy-paste prompt version produces equivalent output for users who can't or won't install the skill.

**US-7 — Human gate**
- A PR touching `site/content/**` cannot merge without an approving review from a `CODEOWNERS`-listed reviewer (branch protection enforces it).

**US-8 — CI frontmatter validation**
- On every PR touching `site/content/**`, `validate-content.yaml` runs `check_frontmatter.py` and the PR is blocked (failing check) if frontmatter is missing, off-schema, has a malformed date, or violates the native/export convention.
- A deliberately malformed test page fails CI; a correct native page passes.

**US-9 — Plan B maintainer path**
- A maintainer can, from the documented CLI runbook, take an author's raw content, produce a valid page, and open the PR — with the same CI + CODEOWNERS gate applying.

**US-10 — Schema reconciliation**
- `check_frontmatter.py` classifies a page as native vs exported (e.g., by presence/absence of `page_id`/`source_url` or an explicit origin marker) and applies the correct required-field set to each.
- A native page (no `page_id`/`source_url`) passes; an exported page missing `page_id`/`source_url` fails. The export path's existing stricter rule is not weakened.

---

## 6. Success metrics

**Leading (build/demo signals):**
- A non-technical author (or a stand-in simulating one) lands a valid page on the site with **zero CLI use** — drafting in SU Claude, submission via GitHub web UI only.
- CI catches a deliberately malformed frontmatter PR (fails the check, blocks merge) in a test run.
- The drafter's output passes `check_frontmatter.py` on the first try in repeated trials (low rate of CI bounce-backs).
- Time-to-first-PR for a non-technical author measured and reasonable (target: under ~15 minutes from "I have my docs" to "PR open," guide in hand).

**Lagging (it actually worked):**
- **Zero** access-restricted or unsafe pages reach the public site through the authoring path (the Principle 4 hard line; leak-guard + CODEOWNERS stay green).
- At least one real page authored and merged by someone other than the maintainer.
- Aaron's team adopts or extends the path rather than asking for a hosted form/wiki.

---

## 7. Plan B (reduced scope) — maintainer-assisted authoring

**What it is.** The drafter still does the AI work, but a **technical maintainer** (Julian/steward) operates the GitHub side: takes the author's source docs and/or raw content, runs the drafter, and opens the PR on the author's behalf via the CLI runbook. The CI + CODEOWNERS gate is unchanged. The author never touches GitHub.

**When we invoke it.** Either trigger flips us to Plan B:
1. **Friction floor proves disqualifying** — the GitHub-account + repo-access + "propose changes / pull request" path is too much for the target faculty user (an Aaron/stakeholder call, not a code call).
2. **Demand sign-off doesn't materialize** — Aaron does not confirm that faculty *self-serve* authoring is actually wanted, so we don't invest in hardening the full self-serve path.

**What we drop in Plan B.** The faculty-facing GitHub web-UI submission flow (US-5) and its one-page guide become a maintainer runbook instead; US-9 becomes the primary path. We still build and keep everything else — the drafter, the Claude Skill packaging (US-6), and the entire gate (US-7, US-8, US-10). Plan B is a smaller *promise* (AI-assisted authoring for a maintainer), not a smaller *build*; the governance gate and drafter are valuable either way.

---

## 8. Out of scope

Pulled from `REQUEST.md` and the VISION out-of-scope list. Do not build these here:

- A hosted web form, custom backend, or paid LLM API. Drafting rides the free SU Claude seat; submission rides GitHub's web UI. (Cost + thin-tooling.)
- Rewriting or replacing the export tool / its `su_kb_export` package. This feature reconciles the schema in the *new* validator; it does not touch the export pipeline's logic.
- Per-user RBAC / authentication. Everything is public on GH Pages (VISION out-of-scope).
- Confluence sync or migration. This is net-new authoring; the export tool owns seeding from Confluence.
- Removing the human review gate. The CODEOWNERS approval is retained by design (Principle 4).
- Removing the GitHub-account requirement. It can't be removed without a backend (out of scope); accepted as the friction floor.
- A manual `skill/SKILL.md` page-map to keep in sync. Research confirmed `llms.txt` regenerates on every deploy — there is no page-map to maintain (Robert's §8 concern is moot for this architecture).

---

## 9. Open stakeholder questions / assumptions

The plan **proceeds under** these two assumptions; they are surfaced as risks, not resolved here. Both are stakeholder calls for Aaron, not engineering questions.

1. **Demand assumption.** We assume Aaron/the team actually want *self-serve faculty authoring* (not just maintainer-assisted authoring). STATUS still lists this as open: "Has Aaron seen the live site and asked for more?" **If demand is not confirmed, fall back to Plan B (§7).** Action: confirm with Aaron in a 1:1 before investing in hardening the full self-serve flow.

2. **Friction-floor assumption.** We assume a GitHub-account + repo-access + web-PR flow is acceptably seamless for the target non-technical faculty user. This is the product risk most likely to sink the self-serve goal, and it cannot be lowered below "needs a GitHub account" without a backend (out of scope). We mitigate with a single deep link into the create-file UI plus a one-page screenshot guide. **If the friction proves disqualifying, fall back to Plan B (§7).** Action: get Aaron's read on whether the target user can clear it.

**Design decision carried into the build (not a stakeholder question):**
- **`visibility: public` backstop (research Open Q7).** Decide during implementation whether the drafter always emits a `visibility: public` marker and whether `check_frontmatter.py` enforces it as a fail-closed backup to human review. Default lean: emit it and have CI treat absence/`restricted` as a hard block, strengthening Principle 4. This is an in-team design call, owned by the gate build.
