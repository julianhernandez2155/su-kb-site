# Research — Faculty Page Authoring

_RPI Step 2 (Research / GO-NO-GO gate). Generated 2026-06-04. Grounded in the live `su-kb-site` repo state, `docs/VISION.md` (v1.1), and `docs/STATUS.md` (reconciled 2026-06-01)._

---

## Executive Summary

**Recommendation: CONDITIONAL GO.** The *valuable, net-new* half of this feature — a Claude-native drafter that turns source docs into a clean, schema-valid `su-kb-site` page — is feasible **today** on free SU Claude Enterprise, aligns squarely with the VISION's authoring gap, and needs no new infrastructure. But the feature is scoped as an "AI front-end **on top of** Robert's governance back-end," and **GATE 0 fails: that back-end is not in the repo.** None of Robert's six guardrail files exist yet, and the *only* frontmatter validator that does exist (`export-tool`'s) directly contradicts the "native-page convention" this feature depends on. Proceeding is the right call, but only once the publish-gate dependency is resolved — otherwise the drafter feeds an unguarded "merge = publish to a public site" pipeline, which violates VISION Principle 4 (public-safe, fails closed).

---

## Feature Overview

| Field | Value |
|---|---|
| **Name** | Faculty Page Authoring — Claude-native drafting on the contribution guardrails |
| **Type** | New capability (authoring front-end) + workflow/process |
| **Target component** | `su-kb-site` — drafter (new, Claude-side) + GitHub web-UI submission path; consumes `tools/`, `.github/`, `site/content/` |
| **Complexity** | **Medium** (the drafter is simple prompt/skill engineering; the complexity is the unbuilt dependency + a schema reconciliation) |
| **Primary user** | A non-technical SU faculty/staff contributor with SU Claude Enterprise + a GitHub account, who will not open a terminal |

---

## Requirements Summary

**Functional (in scope):**
- A Claude-native **drafter**: source docs + a few answers → clean GFM body + valid 8-field frontmatter, using the native-page convention (omit `page_id` / `source_url`).
- **Placement guidance**: emit the exact target path `site/content/<department>/<area>/<slug>.md` and slug.
- **Terminal-free submission** via the GitHub web UI (create-file → "propose changes" → PR), handing off to CI + CODEOWNERS.
- **Self-serve, human gate retained**: the author opens the PR; a CODEOWNERS reviewer still approves before merge.

**Non-functional / constraints:**
- **Free / no new infrastructure** — rides the existing SU Claude seat + GitHub web UI; no paid API, no hosted backend (honors the API-spend discipline).
- **Schema fidelity** — output must satisfy the exact 8-field schema or CI blocks the PR.
- **VISION alignment** — Principles 2 (markdown-native), 3 (dual-consumer), 4 (public-safe/fails-closed), 6 (thin tooling).
- **Stated dependency** — "assumes Robert's guardrails ship." The REQUEST itself flags this as unverified (Open Q / GATE 0).

---

## Product Analysis

**User value: HIGH.** This closes the exact gap STATUS names as the next focus: *"Authoring workflow — how do we add new markdown pages to the site?"* The export tool only seeds *from* Confluence; without an authoring path, the markdown-native half of the VISION ("SU owns **and maintains** its knowledge") stalls at the migration boundary, and only CLI-fluent staff can contribute. A faculty member with no terminal is precisely the user the current runbook excludes.

**Strategic / VISION alignment: STRONG.**
- Principle 2 (markdown-native): the drafter's output *is* plain GFM + YAML — dead-on.
- Principle 3 (dual-consumer): pages render to HTML and a `.md` mirror and auto-enter `llms.txt` (verified — see Technical Discovery); a drafted page serves both consumers by construction.
- Principle 6 (thin tooling): packaging as a Claude skill/prompt/Project adds **zero** runtime infrastructure — no framework creep.
- Principle 4 (public-safe, fails closed): **this is the tension.** The feature only stays public-safe if the human review gate + automated frontmatter check are actually present. They are not yet (GATE 0). The drafter must not become a fast path to publishing unvalidated pages.

**Internship-fit:** matches Aaron's team norm — *"build a repeatable workflow, not a one-off fix"* — and answers research questions #2 (how to create new articles) and partially #5 (how to keep them updated). The "free only" constraint respects the API-spend discipline.

**Product red flags:**
- **The friction floor (Open Q2).** "Terminal-free" still requires a GitHub account, repo access, and understanding "propose changes / pull request." For a true non-technical faculty member that is a real, possibly disqualifying, friction — and it **cannot be removed without a backend**, which is explicitly out of scope. This is the product risk that most threatens the goal, and it's a stakeholder question for Aaron, not a code question.
- **No validated demand signal yet.** STATUS Open Question: *"Has Aaron seen the live site and asked for more?"* Build the drafter against a confirmed appetite for self-serve authoring, not a presumed one.

**Product viability: HIGH** for the drafting capability; **MEDIUM** for the end-to-end "faculty self-serves with zero help" promise, gated on the friction-floor reality.

---

## Technical Discovery (verified against the live repo, 2026-06-04)

This is the section that moves the recommendation. Everything below was checked in the actual repo, not assumed.

### GATE 0 — Robert's guardrail back-end is NOT in the repo

The REQUEST scopes this feature as a front-end "on top of the mechanical/governance back-end Robert already designed." That back-end does not exist in `su-kb-site` as of 2026-06-04:

| Expected guardrail file | Status in repo | Evidence |
|---|---|---|
| `tools/new_page.py` (scaffolder) | **ABSENT** | `tools/` = `render.py`, `kb_config.py`, `build-one.py`, `agent_site_bench/` only |
| `tools/check_frontmatter.py` (validator) | **ABSENT** | not present anywhere in tree |
| `.github/workflows/validate-content.yaml` (CI) | **ABSENT** | `.github/workflows/` = `deploy.yaml` only |
| `CODEOWNERS` (human review gate) | **ABSENT** | only a leftover `_spike/.github/pull_request_template.md` from the dead Quartz spike |
| PR template | **ABSENT** (real one) | same — `_spike/` leftover only |
| `skill/SKILL.md` | **ABSENT** | `skill/` contains only `CONTEXT.md`; the manifest itself was never written |

**Conclusion:** the dependency the REQUEST flagged as unverified is confirmed *unmet*. Robert's set is, per the REQUEST, still a proposal in a Downloads doc — it has not landed in the repo. The feature cannot "feed" a back-end that isn't there.

### Schema conflict — the native-page convention contradicts the only validator that exists

The one piece of frontmatter validation logic in the repo is `export-tool/src/su_kb_export/frontmatter.py`. Its `validate()` enforces:

```python
REQUIRED_FIELDS = ("title", "page_id", "department", "source_url", "last_modified")
```

The feature's **native-page convention says to OMIT `page_id` and `source_url`** (they're Confluence-only). So a page drafted to spec would **fail** the only validator currently in the codebase. This validator is export-path-only (it's inside `su_kb_export`), so it isn't wired into authoring — but it signals the schema fork Robert's unbuilt `check_frontmatter.py` must resolve: *a native page legitimately has no `page_id`/`source_url`, while an exported page requires them.* Whoever builds `check_frontmatter.py` must branch on page origin (native vs exported) or the two halves of the corpus will validate under contradictory rules. This is a concrete design decision, not a detail — and it lands in the **plan** phase.

### What already works in the author's favor (resolves two open questions)

- **Placement without `new_page.py` (Open Q4): WORKS.** `render.py:142` resolves a page's department as `dept = meta.get("department") or parts[0]` — i.e. from the `department` frontmatter field, falling back to the first folder segment. A native page pasted at `site/content/<dept>/<area>/<slug>.md` with correct frontmatter is picked up by the renderer and sidebar automatically. `new_page.py` is a *convenience* scaffolder, not a hard requirement — the drafter emitting the full file + exact path is sufficient.
- **Skill page-map sync (Open Q6): MOOT — not a blocker.** `render.py` `emit_llms_txt()` regenerates `llms.txt` (the retrieval index) from the page set on every build, and `deploy.yaml` runs the renderer on push to `main`. So a merged page auto-enters the index. `skill/CONTEXT.md` confirms the design is "thin skill, fat index — most routing intelligence lives in `llms.txt`, not the skill; if the site reorganizes, only `llms.txt` changes." There is **no manual `SKILL.md` page-map to keep in sync**. Robert's §8 concern doesn't apply to this architecture.
- **Department/area selection (Open Q5): EASY.** The taxonomy is small and legible from the tree: `site/content/data-ai/{ai-general-information, claude, clementine-platform, copilot, gemini}`. The drafter can infer area from content and/or present the existing folder list to choose from.
- **8-field schema is documented and stable.** `frontmatter.py` documents each field, the date-only `last_modified` convention, and `slugify()`/`canonical_filename()` — the drafter can reproduce the exact slug and field set deterministically.

### Reusable vs. net-new

- **Reuse:** the 8-field schema definition, `slugify`/path conventions, the renderer's auto-indexing, the existing `data-ai/` taxonomy, GitHub's native web create-file/PR flow.
- **Net-new:** the drafter prompt/skill/Project itself (the AI task); and — outside this feature's stated scope but blocking it — Robert's validator + CI + CODEOWNERS publish gate, and a reconciled native-vs-export frontmatter schema.

---

## Technical Analysis

**Technical feasibility of the drafter itself: HIGH.** It's prompt/skill engineering against a known, small, documented schema with no runtime dependencies. SU Claude Enterprise can do it today.

**Feasibility of the full self-serve promise: MEDIUM, gated.** It depends on (a) an unbuilt governance back-end and (b) the friction-floor product reality.

**Recommended approach (for the plan phase):**
1. **Packaging (Open Q3):** lead with a shared **Claude Enterprise Project** (or a copy-paste prompt) as the distributable for non-technical staff who have SU Claude but *not* Claude Code — a Claude *skill* only reaches Claude Code users. A skill can be a secondary artifact for technical maintainers. (Plan should confirm what SU Claude Enterprise supports for shared Projects.)
2. **Sequence the dependency:** either (a) wait for Robert's guardrails to land, or (b) **co-build the minimal gate** — `check_frontmatter.py` + a `validate-content.yaml` CI job + a `CODEOWNERS` — as a prerequisite slice. The drafter is low-value-and-unsafe without the fail-closed gate.
3. **Resolve the schema fork** before coding the drafter's frontmatter output: decide how `check_frontmatter.py` treats native pages (omit `page_id`/`source_url`) vs exported pages (require them).
4. **Decide the `visibility: public` field (Open Q7):** whether the drafter always emits it and whether it's added to the validator as a fail-closed backstop to human review.

**Complexity: Medium.** Drafter = Simple. The blocking dependency + schema reconciliation + the (separate) governance build = the real work.

### Technical risks & mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Building on an absent back-end** (GATE 0) | **High** | Make Robert's guardrails (validator + CI + CODEOWNERS) a hard prerequisite or an explicit co-built slice before the drafter ships. |
| **Schema fork** (native omits the two fields the only validator requires) | High | Resolve in plan: `check_frontmatter.py` branches on page origin. Don't weaken the export path. |
| **No fail-closed gate → unvalidated page reaches public site** | High (VISION P4) | Drafter ships only alongside CI frontmatter check + CODEOWNERS human approval. Consider `visibility: public` backstop (Q7). |
| **Friction floor** (GitHub account/PR literacy) | Medium–High (product) | Validate acceptable with Aaron; lower with a single deep link into the create-file UI + a one-page screenshot guide. Cannot be removed without a backend (out of scope). |
| **Drafter emits subtly invalid frontmatter** (YAML quoting, date format) | Medium | Give the drafter the exact `frontmatter.py` field/format rules; CI is the catch-all backstop. |
| **Demand not yet confirmed** | Medium | Confirm Aaron wants self-serve authoring before investing in the full path (STATUS open question). |

---

## Strategic Recommendation

**Decision: CONDITIONAL GO.** **Confidence: High** (on the engineering reality; the empirical gate was checked directly in the repo).

**Rationale.** The drafter is the right feature pointed at the right gap — it's the markdown-native authoring half the VISION needs, it's free, and it adds no framework creep. RPI's research gate did exactly what it's for: the empirical GATE 0 check found that the governance back-end this feature is scoped to sit "on top of" **does not exist yet**, and that the native-page convention conflicts with the only validator in the repo. That doesn't kill the feature — it re-sequences it. Build it, but not before the fail-closed publish gate is real, because shipping a fast drafting path into an unguarded "merge = publish public" pipeline would violate the one VISION principle (public-safe, fails closed) the whole project is built to protect.

**Conditions to clear before / during planning:**
1. **GATE 0:** Robert's validator + CI + CODEOWNERS either land in the repo or are adopted into this feature's scope as a prerequisite slice. The drafter does not ship alone.
2. **Schema reconciliation:** decide how native pages (no `page_id`/`source_url`) and exported pages coexist under one `check_frontmatter.py`.
3. **Friction-floor sign-off:** confirm with Aaron that a GitHub-account + web-PR flow is acceptable for the target faculty user (and whether demand for self-serve authoring is real).
4. **Packaging decision (Q3):** confirm SU Claude Enterprise's shared-Project capability so the drafter reaches non-Claude-Code users.

**Alternatives considered:**
- **Decline / defer the whole thing:** rejected — the authoring gap is the named next priority and the drafter is cheap.
- **Ship the drafter alone, now:** rejected — unsafe without the fail-closed gate; would let unvalidated pages reach the public site.
- **Reframe to "AI-assisted authoring for the technical maintainer" (drop the faculty self-serve promise):** a viable reduced-scope fallback if the friction floor proves disqualifying — still delivers the drafter value without over-promising on the non-technical user. Worth holding as the plan's Plan B.

---

## Open-Questions Resolution

| # | Question | Status after research |
|---|---|---|
| 1 | GATE 0 — are Robert's guardrails in the repo? | **RESOLVED: No.** All six files absent; `skill/SKILL.md` also absent. Dependency unmet. |
| 2 | Friction floor (GitHub account / PR literacy) acceptable? | **OPEN — stakeholder call.** Real risk; can't be removed without a backend. Lower with a deep link + guide. Needs Aaron. |
| 3 | Packaging: skill vs Project vs prompt? | **GUIDANCE:** lead with shared Claude Enterprise Project / prompt for non-Claude-Code staff; skill secondary. Confirm Enterprise capability in plan. |
| 4 | Placement without `new_page.py`? | **RESOLVED: Works.** `render.py` derives `department` from frontmatter-or-folder; full-file-paste at the right path suffices. |
| 5 | Department/area selection by a non-technical author? | **RESOLVED: Easy.** Small, legible taxonomy; drafter infers area + offers the folder list. |
| 6 | Skill page-map sync (Robert §8)? | **RESOLVED: Moot.** `llms.txt` is renderer-generated on every deploy; thin-skill/fat-index means no manual page-map. Not a blocker. |
| 7 | `visibility: public` field as fail-closed backstop? | **OPEN — design decision for plan.** Decide whether drafter always emits it and whether `check_frontmatter.py` enforces it. |

---

## Next Steps

This is a **CONDITIONAL GO** — clear the conditions, then plan.

1. Review this report.
2. **Resolve GATE 0:** confirm whether Robert's guardrails are landing in the repo soon, or fold the minimal gate (validator + CI + CODEOWNERS) into this feature's scope as a prerequisite slice. This is the gating decision.
3. **(Recommended)** Record the CONDITIONAL GO + the GATE 0 / schema-fork findings as an ADR via `/decide faculty-page-authoring approach` (decision-log skill), so the "build the drafter, but gate it on the publish guardrails" rationale is durable.
4. **Ask Aaron** the two stakeholder questions: is self-serve faculty authoring actually wanted, and is the GitHub-web-PR friction acceptable for that user?
5. Once conditions are addressed, proceed to planning: `/rpi:plan "faculty-page-authoring"`. The plan should sequence the governance gate first, reconcile the native/export schema, and choose the drafter's packaging.

---

## Scores

| Dimension | Score |
|---|---|
| Product viability (drafter capability) | **High** |
| Product viability (full faculty self-serve) | **Medium** (friction floor) |
| Technical feasibility (drafter) | **High** |
| Technical feasibility (full path) | **Medium** (gated on unbuilt back-end) |
| VISION alignment | **Strong** (with P4 caveat) |
| **Overall assessment** | **Conditional Go — Medium-High** |

**Top risks:** (1) building on an absent governance back-end; (2) native-vs-export schema fork; (3) the friction floor potentially sinking the non-technical-self-serve goal.
