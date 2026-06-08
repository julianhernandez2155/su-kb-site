# Implementation Plan — Faculty Page Authoring

_RPI Step 3 (Plan / roadmap). Authored 2026-06-08. Integrates [`pm.md`](pm.md) (requirements),
[`ux.md`](ux.md) (flows + states), and [`eng.md`](eng.md) (technical spec). Grounded in the
CONDITIONAL-GO [research](../research/RESEARCH.md), [`docs/VISION.md`](../../../docs/VISION.md) v1.1,
and the live repo (verified 2026-06-08)._

---

## The shape of this plan in one paragraph

Research returned **CONDITIONAL GO**: the drafter is cheap and high-value, but the governance
back-end it was scoped to sit "on top of" **does not exist** (GATE 0 failed). Julian's 2026-06-08
decision: **we build the whole gate ourselves.** So this is no longer "ship a prompt" — it's
**build the fail-closed publish gate first, then the drafter on top of it.** The ordering is not
cosmetic: per VISION P4, a drafting fast-path into an *unguarded* "merge = publish to the public
internet" pipeline is the one thing the project exists to prevent. Safety before capability.

**Locked decisions** (carried into every phase):
1. **Build the entire governance back-end** (`check_frontmatter.py` + `validate-content.yaml` CI +
   `CODEOWNERS` + PR template). Not waiting on Robert.
2. **Full self-serve faculty path** is the target; the maintainer-assisted **Plan B** ([`pm.md`](pm.md))
   is documented as the fallback if the friction floor or demand don't hold.
3. **Drafter = a Claude Agent Skill** usable in regular SU Claude Enterprise (Agent Skills run in
   Claude.ai/Enterprise now), with an identical copy-paste **prompt** as the no-install fallback.
4. **Schema fork resolved** via an explicit `origin: native | confluence` field ([`eng.md` §2](eng.md)).
5. **`visibility: public`** is always emitted and **CI-enforced** as a fail-closed backstop ([`eng.md` §3.1](eng.md)).

---

## Dependencies & ordering (why this sequence)

```
Phase 0  Pre-flight ───┐ (stakeholder + repo-settings prerequisites; partly parallel)
                       │
Phase 1  The Gate  ◄───┘  MUST land before any drafted page can safely reach main
   │  (check_frontmatter.py → CI → CODEOWNERS → PR template → branch protection)
   ▼
Phase 2  The Drafter      depends on Phase 1's schema rules (the skill restates them)
   │  (skill/SKILL.md + drafter-prompt.md)
   ▼
Phase 3  End-to-end + friction guide   depends on 1 AND 2 (full journey through the gate)
   ┄┄┄┄┄┄┄┄
Phase 4  Fast-follows (post-v1)   none of these block the v1 demo
```

- **Phase 1 is the critical path and the safety floor.** Nothing public-facing ships until the
  gate fails closed. Build it even if Phase 2 slips.
- **Phase 2 cannot be finalized before Phase 1's validator exists** — the drafter's self-check
  ([`eng.md` §6.8](eng.md)) restates the validator's exact rules, so the rules must be pinned first.
- **The two stakeholder questions** (Aaron: is self-serve wanted? is the GitHub-PR friction
  acceptable?) are **not on the engineering critical path** — Phases 1–2 are worth building
  regardless, because both serve the maintainer path too. They gate only the *full self-serve
  promise* (Phase 3's framing) and the choice to invest in the friction-lowering guide. Surface
  them early (Phase 0) but don't block the gate on them.

---

## Phase 0 — Pre-flight (unblock conditions)

**Goal:** clear the cheap prerequisites and surface the stakeholder calls before code.

| # | Task | Complexity | Notes / Owner |
|---|---|---|---|
| 0.1 | Confirm SU Claude Enterprise supports installing an **Agent Skill** for non-technical staff (vs. only the copy-paste prompt). | Low | If no → prompt is the lead, skill is deferred. Doesn't block Phase 1. |
| 0.2 | Identify the real **CODEOWNERS reviewer handle** (Julian as steward initially; confirm with Aaron whether an SU/IT handle should be added). | Low | Needed before Phase 1.3. |
| 0.3 | **Ask Aaron the two stakeholder questions** (self-serve demand; GitHub-PR friction acceptability). Capture the answer in STATUS. | Low | Async; gates Phase 3 framing + Plan-A-vs-B, not the gate build. |
| 0.4 | **(Recommended)** Record the CONDITIONAL-GO + "build the gate ourselves" decision as an **ADR** via `/decide faculty-page-authoring approach`. | Low | Makes the re-sequencing durable beyond `eng.md`. |

**Success criteria:** packaging affordance known; reviewer handle chosen; Aaron has the two
questions; the approach decision is recorded.

**Validation checkpoint:** ☐ Phase 0 items resolved or explicitly deferred-with-reason before
Phase 1 merges.

---

## Phase 1 — The Gate (safety back-end) · *critical path*

> **Status: [x] PASS (files/validator)** — 1.1–1.6 done + self-validated; **1.7/1.8 open**
> (branch-protection settings + live blocked-PR test, Julian-executed). See
> [`implement/IMPLEMENT.md`](../implement/IMPLEMENT.md) and
> [`implement/branch-protection.md`](../implement/branch-protection.md).

**Goal:** an invalid or unsafe content PR **cannot merge**. This is the VISION-P4 enforcement point.
Maps to [`pm.md`](pm.md) US-8/US-9 (reviewer approves; CI catches malformed frontmatter) and
[`eng.md` §§2–5, §10](eng.md).

| # | Task | Complexity | Depends on |
|---|---|---|---|
| 1.1 | Build [`tools/check_frontmatter.py`](../../../tools/check_frontmatter.py) — native-aware validator, CLI + importable (`validate_file`/`validate_text`), exit non-zero on any failure. Schema branch per [`eng.md` §2.4](eng.md); per-field checks per [`eng.md` §3](eng.md). | **Medium** | — |
| 1.2 | Unit tests for the validator (the 13-case matrix in [`eng.md` §9](eng.md)), including the **`slugify` drift guard** vs the export source of truth. | Medium | 1.1 |
| 1.3 | **CI dry-run over the 28 existing exported pages** — `python tools/check_frontmatter.py site/content/` must exit 0 (proves the `confluence` branch + lazy-`visibility` rule don't break the live corpus). | Low | 1.1 |
| 1.4 | Add [`.github/workflows/validate-content.yaml`](../../../.github/workflows/validate-content.yaml) — PR trigger on `site/content/**/*.md`, validates the diff, fails closed. Coexists with `deploy.yaml` untouched ([`eng.md` §4](eng.md)). | Low–Med | 1.1 |
| 1.5 | Add `CODEOWNERS` routing `site/content/**` **and the gate's own files** to the reviewer ([`eng.md` §5.1](eng.md)). | Low | 0.2 |
| 1.6 | Add [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) — the publish-safety checklist ([`eng.md` §5.2](eng.md)). | Low | — |
| 1.7 | **Flip two branch-protection settings on `main`:** require the `validate-content` check **and** require review from Code Owners. *(Repo settings, not files — the gate is not real until this is done.)* | Low | 1.4, 1.5 |
| 1.8 | **CI-behavior test:** open a throwaway PR with a deliberately-invalid page → confirm CI fails and **Merge is blocked**; fix → confirm green → Merge enabled ([`eng.md` §9](eng.md)). | Low | 1.7 |

**Success criteria:**
- A native page drafted to spec passes; a page missing `visibility`, carrying a stray `page_id`, or
  with a bad date/slug **fails** and **cannot be merged**.
- The 28 existing pages still validate (no regression).
- `deploy.yaml` is byte-for-byte unchanged.

**Validation checkpoint:** ☐ The §8-top risk is retired — *the files-plus-settings actually block a
bad PR*, proven by task 1.8, not assumed.

---

## Phase 2 — The Drafter (skill + prompt)

> **Status: [~] In progress — files done + self-validated, pending user validation.** Built at
> `skill/drafter/SKILL.md` + `skill/drafter/drafter-prompt.md` (own subfolder, not `skill/SKILL.md`
> — see the recorded deviation in [`implement/IMPLEMENT.md`](../implement/IMPLEMENT.md)). Dry-run
> output validates clean (task 2.4).

**Goal:** a non-technical author turns source docs into a clean, schema-valid file + exact path,
entirely inside SU Claude. Maps to [`pm.md`](pm.md) US-1…US-5, [`ux.md`](ux.md) (drafter conversation
design + all interaction states), and [`eng.md` §6](eng.md).

| # | Task | Complexity | Depends on |
|---|---|---|---|
| 2.1 | Write `skill/drafter-prompt.md` — the instruction body: role + **"everything is PUBLIC" warning**, native convention (`origin: native`, no `page_id`/`source_url`, `visibility: public`), exact 8-field+governance template, `slugify` rule with worked examples, path template + taxonomy, GFM body rules (dual-consumer), the GitHub handoff steps, and the pre-handoff self-check ([`eng.md` §6](eng.md)). | **Medium** | 1.1 (rules must be pinned) |
| 2.2 | Wrap the same body as `skill/SKILL.md` (Agent Skill manifest + instructions) — single source of truth, two delivery vehicles. | Low | 2.1 |
| 2.3 | Encode the **conversation design** from [`ux.md`](ux.md): propose-and-confirm question order (department/area, audience, title), the mandatory public-safety checkpoint before emitting, and the handling for the 7–8 interaction states (empty / gathering / success / ambiguous-area / missing-info / sensitive-source / GitHub-confusion / waiting-for-review). | Medium | 2.1 |
| 2.4 | **Dry-run the drafter** on one real source doc → run its output through `check_frontmatter.py` locally → it passes with zero hand-editing. | Low | 2.1, 1.1 |

**Success criteria:**
- The drafter reliably emits a file that **passes Phase 1's validator on the first try**.
- It refuses / flags source material that looks access-restricted (the safety checkpoint fires).
- It tells the author the exact path and the terminal-free GitHub steps.

**Validation checkpoint:** ☐ Drafter output validates clean (2.4) — the drafter and the gate agree
on the schema.

---

## Phase 3 — End-to-end + friction-lowering guide

> **Status: [~] Doc half done.** 3.3 friction-lowering guide written at
> [`docs/authoring/submit-on-github.md`](../../../docs/authoring/submit-on-github.md) + wired into
> the drafter. **3.1/3.2 (live E2E + negative pass) are Julian-executed** — they need the Phase 1
> branch-protection settings (1.7/1.8) flipped and GitHub actions. 3.4 (STATUS/log/ADR) at session
> close. See [`implement/IMPLEMENT.md`](../implement/IMPLEMENT.md).

**Goal:** prove the whole journey — Claude → GitHub web UI → gate → live site + `llms.txt` — works
for a non-technical author, and lower the one friction risk research flagged. Maps to
[`pm.md`](pm.md) success metrics, [`ux.md`](ux.md) GitHub-handoff section, [`eng.md` §9 end-to-end](eng.md).

| # | Task | Complexity | Depends on |
|---|---|---|---|
| 3.1 | **Run the full manual E2E journey** ([`eng.md` §9](eng.md)): draft → paste into GitHub web UI → PR → CI green → CODEOWNERS review → merge → page live + appears as a new line in `/llms.txt`. | Low–Med | Phase 1, Phase 2 |
| 3.2 | **Negative E2E pass:** draft with `visibility` omitted / an exported header pasted → confirm CI **blocks** before merge (P4 fails closed end-to-end). | Low | 3.1 |
| 3.3 | Write the **one-page GitHub handoff guide** (screenshots + a single deep link into the create-file UI) — the concrete friction-floor mitigation. For real visual polish, hand to the `impeccable` / `ui-ux-pro-max` / `design-review` skills per [`ux.md`](ux.md) rather than hand-rolling. | Low–Med | 3.1; gated by 0.3 (only invest if Aaron confirms the self-serve path) |
| 3.4 | Update `docs/STATUS.md` + write a `docs/log/` entry; if the approach ADR (0.4) wasn't done, do it now. | Low | — |

**Success criteria:**
- A page authored with **zero CLI use** reaches the live site through the gate.
- The negative path is provably blocked.
- A non-technical reader can follow the handoff guide unaided.

**Validation checkpoint:** ☐ The `pm.md` headline metric is met — *a non-technical author lands a
valid public page with no terminal*, and *no unsafe page can*.

---

## Phase 4 — Fast-follows (post-v1, not demo blockers)

| # | Task | Complexity | Trigger |
|---|---|---|---|
| 4.1 | **`visibility: public` backfill PR** over the 28 legacy pages + `export-tool`'s `build_frontmatter`, then make `visibility` unconditionally required ([`eng.md` §3.1](eng.md)). | Low–Med | After v1 is green |
| 4.2 | Optional `tools/new_page.py` scaffolder — **only** for the technical-maintainer (Plan B) path; skip unless that user asks ([`eng.md` §7](eng.md)). | Low | On demand |
| 4.3 | Widen slug-match enforcement to **both** origins if the 28-page dry-run is clean. | Low | If 1.3 clean |
| 4.4 | **Plan B activation** (maintainer-assisted authoring) — invoke only if Aaron's demand sign-off (0.3) doesn't materialize or the friction floor proves disqualifying ([`pm.md`](pm.md) Plan B). | — | Stakeholder-driven |

---

## Testing requirements (rolled up)

| Layer | What | Where |
|---|---|---|
| Unit | 13-case validator matrix + `slugify` drift guard | [`eng.md` §9](eng.md), task 1.2 |
| Acceptance | CI dry-run over 28 existing pages exits 0 | task 1.3 |
| CI behavior | Invalid PR is blocked; fixed PR merges | task 1.8 |
| Integration | Drafter output passes the validator with no edits | task 2.4 |
| End-to-end | Full journey to live site + `llms.txt`; negative path blocked | tasks 3.1, 3.2 |
| Stakeholder (manual) | Friction-floor acceptability + demand | Aaron, task 0.3 (tracked in `pm.md`, not automatable) |

---

## Risk register (carried from research + eng.md, with the owning phase)

| Risk | Severity | Mitigation / owning task |
|---|---|---|
| Gate not actually enforcing (files exist but settings not flipped) | **High (P4)** | Tasks 1.7 + 1.8 — settings + a test that proves blocking |
| Schema fork mis-resolved (native rejected or export weakened) | High | Explicit `origin:` + `page_id` fallback; export validator untouched; 1.3 dry-run |
| Unvalidated/unsafe page reaches public site | High (P4) | Phase 1 entire; `visibility: public` backstop; human checklist |
| Drafter emits subtly-invalid YAML | Medium | Drafter self-check (2.3) + CI backstop (1.4) |
| Friction floor sinks non-technical self-serve | Med–High (product) | 0.3 (Aaron) + 3.3 guide; Plan B (4.4) is the fallback |
| Agent Skill not installable on SU's Enterprise tier | Low | Copy-paste prompt fallback (2.1) always works |
| Demand not confirmed | Medium | 0.3 before investing in 3.3 / full self-serve framing |

---

## Definition of done (v1)

1. **The gate fails closed** — proven by a blocked invalid PR (1.8), with the 28 existing pages
   still green (1.3).
2. **The drafter produces validator-clean pages** that a non-technical author can submit with no
   terminal (2.4 + 3.1).
3. **The full journey works** — a drafted page reaches the live site as HTML + `.md` + an
   `llms.txt` line, through CI + human review (3.1); the unsafe path is blocked (3.2).
4. **It's documented** — STATUS/log updated, approach ADR recorded, handoff guide written (3.3, 3.4).
5. **Thin and reversible** — 6 net-new files, `deploy.yaml` untouched, no new service or paid API
   (VISION P6).

---

## Next steps

1. Review these four plan docs (`pm.md`, `ux.md`, `eng.md`, this `PLAN.md`).
2. **(Recommended)** Record the approach as an ADR — `/decide faculty-page-authoring approach` —
   so the "build the gate ourselves, gate before drafter" rationale is durable (Phase 0.4).
3. Send Aaron the two stakeholder questions (Phase 0.3) — async, doesn't block Phase 1.
4. Begin implementation: `/rpi:implement faculty-page-authoring`, starting at **Phase 1 (the gate)**.
