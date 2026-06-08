# UX Brief — Faculty Page Authoring

_RPI Step 3 (Plan). For `su-kb-site`. Companion to `REQUEST.md` + `research/RESEARCH.md` (CONDITIONAL GO). Locked decisions per Julian, 2026-06-08._

---

## 1. Overview

**There is no custom GUI to design.** This feature has no web form, no admin panel, no bespoke editor. The user experience is made of two pre-existing surfaces stitched together:

1. **A drafter conversation** inside SU Claude Enterprise — a packaged Claude Skill (with a copy-paste prompt as fallback) that interviews the author and emits a finished page file + its exact target path.
2. **A terminal-free handoff into GitHub's own web UI** — the author pastes that file into GitHub's "create new file" page, clicks "Propose changes," and a Pull Request opens. CI validation + a human CODEOWNERS review then gate publish.

So the entire UX surface is: **the words the drafter says, the order it asks things, the file it hands back, and the choreography that walks a non-technical faculty member through GitHub's web flow without losing them.** That is what this brief designs. Where a real visual artifact is needed (the screenshot guide), this brief points at the right design skill rather than faking pixel specs.

**Design constraints that shape every decision below:**
- Target user is a **non-technical faculty member**. Has SU Claude Enterprise + a GitHub account. Will NOT open a terminal, clone, or run Python. May not know what a "pull request" or "propose changes" is.
- Output must be **schema-valid GFM + 8-field frontmatter**, native-page convention (OMIT `page_id` and `source_url`).
- **Merge = publish to a PUBLIC site.** No access control (VISION P4). The author must be told this clearly, before they submit — this is a UX safety moment, not fine print.

---

## 2. Primary user flow (end to end)

```
  ┌─────────────────────── INSIDE SU CLAUDE ENTERPRISE ───────────────────────┐
  │                                                                            │
  │  1. Author opens the "SU KB Page Drafter" skill (or pastes the prompt)     │
  │            │                                                               │
  │  2. Author drops in source material + says what the page is about          │
  │            │                                                               │
  │  3. Drafter asks a SHORT set of clarifying questions:                      │
  │       • Which area? (offers the 5-item list, or proposes one)              │
  │       • Who's the audience?  • Confirm the title.                          │
  │            │                                                               │
  │  4. Drafter shows the PUBLIC-publish safety note + asks to confirm         │
  │            │                                                               │
  │  5. Drafter emits, in one message:                                         │
  │       • the complete file (frontmatter + GFM body) in a copy block         │
  │       • the EXACT path:  site/content/<dept>/<area>/<slug>.md              │
  │       • a numbered, copy-ready "how to submit on GitHub" instruction       │
  │         + the deep link into GitHub's create-file page                     │
  └────────────────────────────────┬───────────────────────────────────────────┘
                                    │  (author leaves Claude, opens the link)
  ┌────────────────────────────── ON GITHUB.COM ──────────────────────────────┐
  │  6. Create-file page opens (deep-linked). Author pastes filename + file.   │
  │  7. Author clicks "Commit changes…" → chooses "Create a new branch …       │
  │     and start a pull request" → "Propose changes."                          │
  │  8. PR opens. PR template prompts a one-line "what is this page."           │
  │            │                                                               │
  │  9. CI runs frontmatter validation (pass/fail shown on the PR).            │
  │ 10. A CODEOWNERS reviewer reads it and approves (or requests changes).     │
  │ 11. Merge → the renderer rebuilds → page is LIVE + in llms.txt.            │
  └────────────────────────────────────────────────────────────────────────────┘
```

**Decision points worth calling out:**
- **Step 3 (area):** if the drafter can confidently infer the area from content, it *proposes* it and asks for a yes/no rather than making the author study a taxonomy. If it can't, it offers the 5-item list. (See §3.)
- **Step 4 (public warning):** the author must actively acknowledge "this will be public" before the drafter emits the final file. Don't bury it.
- **Step 7 (the cliff):** this is where a non-technical author is most likely to stall — GitHub's commit dialog uses unfamiliar words ("branch," "pull request"). The drafter's submission instructions and the one-page screenshot guide carry the author across it. This is the single biggest UX risk (RESEARCH Open Q2). See §5.
- **Step 10 (review):** the author should already expect a human review and a possible "please change X" — set that expectation in step 5 so they aren't surprised or alarmed by a change-request.

---

## 3. The drafter conversation design

The drafter's job is to extract the *minimum* it needs and do everything else itself. A non-technical author should answer at most 3–4 small questions and never see YAML rules, slug algorithms, or folder paths until the finished file appears.

**Opening behavior (when invoked with no material yet):**
> "I'll help you turn your notes into a Syracuse KB page. Paste or upload what you have — a draft, a Word doc, meeting notes, bullet points — and tell me in a sentence what this page should help people do. I'll handle the formatting."

**Question order (ask only what's still unknown; infer the rest):**

1. **Source + intent** — got in the opening. The drafter reads the material first; everything below is asked only if it can't be inferred.
2. **Area / namespace** — the drafter infers from content and *proposes*:
   > "This looks like it belongs under **Claude** (`data-ai/claude`). Sound right? If not, pick one: AI General Information · Claude · Clementine Platform · Copilot · Gemini."
   Confirming is one tap; the author never has to know it maps to a folder.
3. **Audience** — "Who is this page mostly for — students, faculty, staff, or everyone?" Maps to the `audience` frontmatter field.
4. **Title confirmation** — the drafter proposes a clear title and derived slug; author confirms or edits. The slug is shown but explained in plain words ("the page's web address ending").

**The PUBLIC-publish safety note (mandatory, before final emit):**
The drafter must surface this as a clear, plain-language checkpoint — not a footnote:
> "⚠️ Before we finish: **anything published here goes on a public website** — anyone on the internet can read it. There's no private or login-only mode. A Syracuse reviewer will check it before it goes live, but please make sure there's nothing confidential, FERPA-protected, or internal-only in here. Good to continue?"

The drafter also always emits a `visibility: public` line in the frontmatter (see §4) as a fail-closed marker. The conversational warning and the emitted marker are two halves of the same safety design: the warning protects against the author *not realizing*, the marker protects the pipeline against a reviewer *not catching*.

**Burden-minimizing principles:**
- Prefer **propose-and-confirm** over open questions ("Is *Claude* right?" beats "Which folder?").
- Batch questions when possible; never make the author answer one tiny thing at a time across five turns.
- Never expose frontmatter syntax, slug rules, or path conventions as *questions*. They are outputs, not inputs.
- Re-state the public warning if the author pastes material that looks sensitive (see §4 edge cases).

---

## 4. All interaction states

The flow is conversational + handoff, so "states" are conversation conditions, not screens. Every one below must be designed — the non-happy-path states are where this feature succeeds or fails.

| State | When | What the author sees / what the drafter does |
|---|---|---|
| **Initial / empty** | Skill opened, no material yet | The opening invitation (§3). Friendly, one ask: paste your stuff + one sentence of intent. No wall of questions. |
| **In-progress / gathering** | Material received, still resolving area/audience/title | Propose-and-confirm questions, one short batch. A brief "Here's what I've got so far…" recap so the author can correct early. |
| **Success** | Enough info gathered + public note acknowledged | One clean message: the full file in a copy block, the **exact path**, and the numbered GitHub submission steps + deep link. Nothing else competing for attention. |
| **Error — ambiguous area** | Drafter can't confidently infer the namespace | Don't guess silently. Offer the 5-item list and a one-line "what each is for" so a non-expert can choose. If still unsure, default to `ai-general-information` and *say so*. |
| **Error — missing required info** | Can't produce a valid `title`/`description`/`audience` | Ask for the specific missing piece in plain words; never emit an invalid file "to be fixed later." Better to ask than to hand the author a page CI will reject. |
| **Edge — sensitive / access-restricted source** | Source looks internal-only, has logins, student data, "do not distribute," screenshots of private dashboards | **Stop and flag, loudly.** "Some of this looks like it may be internal or confidential. Remember this becomes fully public. Want me to (a) draft only the public-safe parts, or (b) stop here?" This is the fails-closed UX behavior for VISION P4. |
| **Edge — author confused at the GitHub step** | Author comes back saying "I don't see Propose changes" / "what's a branch?" | The drafter offers the one-page screenshot guide link again and a plainer restatement, and surfaces the **Plan B** offer: "Want a Syracuse maintainer to submit this for you? Just send them this file." (See §7.) |
| **Post-submit — waiting for review** | PR opened | Set in step 5 *before* they submit: "After you click Propose changes, a Syracuse reviewer will check the page. You may get a comment asking for a small change — that's normal, not a rejection. Once it's approved and merged, your page goes live automatically." Expectation-setting prevents the "did I break it?" panic. |

**Copy & error messaging** (the words that matter):
- Public warning: see §3 — non-negotiable wording intent: *public, no private mode, reviewer-checked, your responsibility for confidential content.*
- Ambiguous area fallback: "I wasn't sure which area fits, so I put this under **AI General Information**. If it belongs somewhere else, tell me and I'll move it."
- Sensitive-source stop: see table — must offer a safe path forward, not just block.
- Review expectation: "A reviewer will look this over before it's published. A request for changes is normal."
- Success handoff lead-in: "Your page is ready. Here's the file and exactly how to put it on Syracuse's site — no coding or terminal needed. Two short steps."

---

## 5. The GitHub web-UI handoff

This is the highest-friction, highest-risk segment (RESEARCH Open Q2 — the friction floor). The author has a perfect file from Claude and now must get it onto GitHub with zero terminal. Two design moves do the heavy lifting:

**A. A deep link into GitHub's create-file page.**
The drafter emits a ready-to-click URL of the form:
```
https://github.com/<org>/<repo>/new/main?filename=site/content/<dept>/<area>/<slug>.md
```
GitHub's `/new/<branch>?filename=…` route opens the create-file editor **with the path and filename pre-filled**. This removes the two steps most likely to go wrong for a non-technical user: navigating the repo tree to the right folder, and typing the exact path/slug by hand. The author lands on a page that already knows where the file goes; they paste the body and commit. This single deep link is the cheapest, highest-leverage friction reducer in the whole flow — the plan should make emitting it a hard requirement of the drafter.

**B. A one-page screenshot guide ("Put your page on the Syracuse site — 2 steps").**
Lives once in the repo (e.g. `docs/authoring/submit-on-github.md` or a `CONTRIBUTING` section) and is linked from every drafter success message. It must cover exactly the span "I have a file from Claude" → "I opened a PR," with an annotated screenshot per step:

1. Paste the file into the (pre-filled) create-file page.
2. Scroll to the green **Commit changes…** button.
3. In the dialog, choose **"Create a new branch for this commit and start a pull request."** (Plain-language gloss: "this just means 'submit it for review' — you don't need to understand branches.")
4. Click **Propose changes**, then **Create pull request**.
5. "Done. A Syracuse reviewer takes it from here. You'll get an email if they have a question."

Each screenshot should circle/arrow the one element to click and translate GitHub's jargon ("branch," "pull request," "commit") into the plain meaning a faculty member needs ("submit for review"). Per-element annotation matters more than prose.

> **Visual design handoff:** the actual layout, annotation style, callout treatment, and screenshot polish of this one-page guide should be produced with **`ui-ux-pro-max`** (component/visual patterns) or iterated live with **`impeccable`**. Do not hand-roll its pixel spec here — the brief specifies *what each step must communicate*; the visual treatment is a design-skill job. If the guide ships as part of the rendered site, run **`design-review`** against it for a WCAG audit.

**Why not remove the GitHub step entirely?** It can't be — that requires a hosted backend, which is explicitly out of scope (free-only, thin-tooling, VISION P6). The GitHub account + web-PR is the accepted friction floor; the deep link + screenshot guide lower it as far as it can go without infrastructure. Plan B (§7) is the escape hatch when even this is too much.

---

## 6. Accessibility considerations (WCAG 2.2 AA)

Scope note: the rendered KB *site* already has its own design system — not re-spec'd here. This section covers **the authoring guide + the drafter's human-facing copy**, the artifacts this feature actually introduces.

**For the one-page screenshot guide (if rendered as a web page):**
- **Text alternatives (1.1.1):** every screenshot needs descriptive alt text that conveys the *action*, not just "screenshot" — e.g. alt="GitHub commit dialog with 'Create a new branch and start a pull request' selected." The guide must be fully usable by someone who can't see the images: each step's instruction text must stand alone without the picture.
- **Don't rely on color alone (1.4.1):** if arrows/circles highlight a button, also name the button in text ("the green Commit changes button, bottom-left").
- **Contrast (1.4.3 / 1.4.11):** annotation callouts (arrows, circles, captions) over screenshots must meet 4.5:1 for text and 3:1 for the graphical indicators against their backdrop. Screenshots often fail this — verify, don't assume.
- **Keyboard + focus (2.1.1 / 2.4.7):** the guide and the deep link must be fully keyboard-operable with a visible focus indicator; the GitHub deep link is a normal `<a>` — keep it one.
- **Reflow / responsive (1.4.10):** see §responsive below.
- **Headings & structure (1.3.1 / 2.4.6):** numbered steps as a real ordered list with descriptive headings, so screen-reader users can navigate step-to-step.
- **Plain language (3.1.5):** target a general-audience reading level (~8th grade). This is a faculty member outside CS, possibly stressed by unfamiliar tooling. Every GitHub term ("branch," "pull request," "commit," "repository") gets a plain-English gloss on first use. Short sentences. Active voice.

**For the drafter's conversational copy:**
- Plain language, no unexplained jargon — same reading-level bar.
- The public-publish warning must be **unmissable and unambiguous** in wording (an accessibility-of-comprehension issue as much as a safety one): state plainly "anyone on the internet can read this," not "this surface has no access control."
- Confirmations should be answerable with a short word ("yes" / "Claude" / "everyone"), not by parsing a dense menu.

**Responsive behavior (the guide only):**
- Mobile-first. The guide is short and likely read on a laptop beside GitHub, but must reflow cleanly on a phone: single-column, full-width screenshots that remain legible (or tap-to-zoom), no horizontal scroll at 320px (1.4.10). Steps stack vertically; nothing depends on a wide viewport. The drafter conversation itself inherits Claude's own responsive client — not our concern.

---

## 7. Plan B note — maintainer-assisted flow

When the friction floor is too high for a given author (they stall at GitHub, lack repo access, or just want help), the flow degrades gracefully to **maintainer-assisted**:

- **Where it diverges:** steps 1–5 are identical — the author still uses the drafter in SU Claude to produce the finished file + path. The change is at the **handoff**: instead of the author doing steps 6–8 on GitHub, they send the drafter's output (the file block + the path) to a technical maintainer (Julian / future SU steward), who pastes it into GitHub — or runs Robert's fuller CLI runbook (`new_page.py`, local `render.py`, push, PR) — on the author's behalf.
- **UX implication:** the drafter's "confused at GitHub" edge state (§4) should *offer this as a one-click escape*, not treat it as failure: "Want a Syracuse maintainer to put this live for you? Copy this file and send it to them." The author's experience stays inside Claude; the GitHub literacy requirement moves to the maintainer.
- **What stays the same:** the human CODEOWNERS review and CI validation are unchanged — Plan B changes *who drives the web UI*, not whether the publish gate runs. Self-serve vs. assisted both end at the same reviewed merge.
- This is the reduced-scope fallback RESEARCH flagged ("AI-assisted authoring for the technical maintainer") — worth holding even if full self-serve proves friction-bound, because the drafter's value lands either way.
