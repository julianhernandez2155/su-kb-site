---
status: accepted
date: 2026-05-28
supersedes: [0001-quartz-v4-as-ssg.md](0001-quartz-v4-as-ssg.md)
deciders: Julian Hernandez
consulted: AI council (3 personas × 2 rounds, 2026-05-28); empirical wikilink-through-WebFetch test (2026-05-28)
---

# 0002. Pivot from Quartz to a thin Python renderer

## Context

[ADR-0001](0001-quartz-v4-as-ssg.md) chose Quartz v4 because it was the only mainstream SSG with first-class Obsidian `[[page-id - title]]` wikilink parsing. The ITSAI corpus (~29 pages, growing to ~150 across departments) was inherited in Obsidian format from the prior `su-kb-pipeline` project. ADR-0001's load-bearing claim was that reimplementing Quartz's `ofm.ts` faithfully (793 lines) was prohibitive.

Three shifts since ADR-0001 invalidate that reasoning:

1. **Empirical test (2026-05-28).** Fixtures pushed to [`_test-wikilinks/`](../../_test-wikilinks/README.md) with 3 corpus pages in two versions (original `[[wikilink]]` syntax + rewritten `[alias](./relative.md)`), fetched via `raw.githubusercontent.com`. Claude's `WebFetch` preserved both formats verbatim through its small-model summarizer, classified them correctly, parsed page-id + title + alias. **Both formats produced equivalent LLM-readable output.** The `.md` mirror with wikilink-rewriting is no longer a technical requirement.

2. **Wikilink-value reframing.** Once "wikilinks survive WebFetch" was confirmed, the deeper question — do they ADD VALUE? — answered no. Wikilinks were valuable when the target was an Obsidian vault (graph view, backlinks, hand-editing). For our setup (Confluence is authoritative; no human edits markdown; consumers are HTML + Claude WebFetch), the page-id is in the URL (`./page-id.md`), title is in target's frontmatter, alias becomes link text. Same information, less Obsidian-specific.

3. **AI council convergence.** Three Agent subagents (Quartz Defender, Custom-Build Advocate, Skeptic) × two rounds. R2 saw the Advocate's narrowed Option C and the Skeptic's refined Option D collapse to functionally the same answer: a thin Python renderer + Jinja2 templates of `_design/`. The Defender walked back the corpus-evidence argument explicitly. Convergence across opposing voices is a strong decision signal.

## Decision

**Drop Quartz v4. Adopt a thin Python renderer + Jinja2 templates over `_design/`.**

Concretely:

- **Export tool**: patch `wikilinks.py` to emit `[alias](./slug.md)` relative markdown links. Patch `frontmatter.py` for an 8-field schema: `title`, `description`, `page_id`, `department`, `source_url`, `last_modified`, `tags`, `audience`. Drop Obsidian image embeds in favor of standard markdown. Slug-only filenames; page-id stays in frontmatter for stable identification.
- **Renderer**: `tools/render.py` — ~150 lines (hard ceiling 300) — reads markdown + frontmatter, renders body via `markdown-it-py` with GFM plugins (callouts, tables, syntax-highlighting via Pygments), injects into Jinja2 templates derived from `_design/landing.html` and `_design/docpage.html`, auto-derives TOC + breadcrumbs + Related sections, emits HTML + raw `.md` mirror + `llms.txt` to `site/_site/`.
- **Deploy**: replace the Quartz GitHub Actions workflow with one that runs `python tools/render.py` and uploads `site/_site/` as the Pages artifact.

Full execution plan: [`../next-session-plan.md`](../next-session-plan.md).

## Decision gate (escape hatch)

If `tools/render.py` crosses ~300 lines, OR if templating fights for more than 1 working session, fall back to **MkDocs-Material** (ADR-0001's original documented escape hatch). The renderer growing past 300 lines is the signal we're building a half-finished SSG; switch to a real one before that happens.

## Consequences

### Positive
- Markdown corpus is portable plain GFM — any future SSG can consume it without an Obsidian-syntax layer
- `_design/` HTML templates become production templates with no Preact port — single source of truth
- `.md` mirror is free: the export tool's markdown IS the mirror; no rewrite step
- Renderer is inspectable in 20 minutes — better handoff posture than Quartz codebase with custom plugins
- Drops `node_modules` (~30k LOC of Quartz internals); smaller dependency surface, faster builds

### Negative
- Bespoke renderer Julian owns; no community / plugin ecosystem
- No free search, RSS, popovers, graph view, dark-mode toggle
- Bus-factor risk: a successor reads one human's code, not a documented framework. Mitigated by small size + Jinja2's universality
- Must write `emit-llms-txt` logic ourselves (~30 lines)

### Neutral
- Multi-department folder structure works equivalently under either path
- GFM callouts render in any compliant markdown processor — not Quartz-specific

## Alternatives considered

- **Stay on Quartz** (Defender's R2 case): viable but narrower than ADR-0001 thought. Plugin ecosystem + bus-factor + dev-server ergonomics are the remaining wins. Lost because the convergence of Advocate + Skeptic on the thin-renderer path was strong signal for our actual scale (~29 → 150 pages).
- **Option B — Python end-to-end** (export tool emits HTML directly): rejected because markdown-as-source-of-truth-on-disk preserves debugging clarity and makes the `.md` mirror trivial.
- **Option D — no build step, hand-author HTML per page**: rejected by the Skeptic in R2 after realizing `_design/docpage.html` hardcodes the sidebar in two places. At 700–1771 words/page × 29 pages, hand-authoring is ~4–6 days and 58 sidebar-edit spots per change.

## Sources consulted

- [_test-wikilinks/README.md](../../_test-wikilinks/README.md) — empirical test setup
- WebFetch results from `raw.githubusercontent.com/julianhernandez2155/su-kb-site/main/_test-wikilinks/...` (2026-05-28)
- AI council R1 + R2 outputs (2026-05-28; synthesized in this ADR's Context section)
- [next-session-plan.md](../next-session-plan.md) — execution plan + decision gates

## Amendment (2026-05-28) — accepted renderer overage

`tools/render.py` grew from **299 → 436 lines** while adding directory-index
generation (an `index.html` + `.md` mirror for the dept root and every
subdirectory that holds pages, so landing-card and breadcrumb links resolve
instead of 404ing). The same change also pulled in adjacent correctness work
that the original estimate didn't anticipate: a clean-rebuild step (stale
orphan HTML/.md from renamed or excluded pages must not linger), per-department
`attachments/` copying, root-absolute sidebar/Related/body-link resolution
(the wrapper-collapsed nesting broke the old flat relative links), and a
post-render link-integrity check that now reports **zero** broken internal
`.html`/image targets under `site/_site`. Pure display data (labels, card copy,
index intros) lives in `kb_config.py`, keeping `render.py` to logic.

This crosses the **300-line decision gate** from the section above. Reviewed
with the gate's *purpose* in mind rather than the number: the gate existed to
catch us building a half-finished SSG. That risk did not materialize. The
renderer is still a single inspectable file of straight-line logic — markdown →
HTML, synthesize index bodies, emit mirrors/llms.txt/sitemap, verify links —
with no plugin system, no config DSL, no routing layer, no incremental-build
machinery. It reads top-to-bottom in well under the "20 minutes" handoff target
ADR-0002 set. The escape hatch (fall back to **MkDocs-Material**) was weighed
and declined: migrating now would be a larger lift than the overage it saves,
and it would discard the bespoke clementine-styled `_design/` templates that are
the whole reason this path was chosen over a generic SSG in the first place.

**Decision:** Julian accepts the overage. The 300-line figure is retired as a
hard gate for this renderer; the operative constraint going forward is
"single-file, inspectable, no SSG-framework creep," which 436 lines still
satisfies. If a *future* feature would require a plugin/config/routing
abstraction (real SSG-shaped complexity), revisit MkDocs-Material then.
