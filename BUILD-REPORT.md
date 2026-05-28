# BUILD-REPORT — su-kb-site renderer (Stage 4 + Stage 5)

Date: 2026-05-28. Scope: implement the thin Python renderer, Jinja templates,
WCAG CSS fixes, and the LLM/WebFetch output layer per the reviewed design specs
and every adversarial must-fix. No live Confluence export, no git, no deploy.

## Files created

| Path | What |
|---|---|
| `tools/render.py` | Full renderer (Stage 5). **299 lines** (ceiling 300). |
| `tools/build-one.py` | Stage 4 PoC — renders only `claude-faq.md` to `_design/output/`. 44 lines. Imports the core from `render.py`. |
| `tools/kb_config.py` | Static config + display data (labels, group order, card copy, callout SVGs, URLs). 56 lines. Pulled out of `render.py` so the renderer logic stays under the ceiling — this is data, not logic. |
| `_design/docpage.html.jinja` | Templatized doc page (chrome + breadcrumbs loop + meta + body + sidebar injected twice + TOC + footer + scrollspy verbatim). |
| `_design/landing.html.jinja` | Templatized landing (data-driven tool cards + counts). |
| `site/content/data-ai/claude/claude-faq.md` | Stage-3-shaped seed (8-field schema, relative `.md` links, GFM alerts) for the smoke test. |
| `BUILD-REPORT.md` | This file. |

## Files modified

| Path | Change |
|---|---|
| `_design/tokens.css` | WCAG finding #4 (360px nav): `.nav-brand { min-width: 0 }`; `@380px` block adds `gap`, `.nav-right { flex-shrink: 0 }`, `.nav-link { white-space: nowrap }`. Plus the shared external-link `↗` rule for footer/trust http links (Codex important-finding #2). |
| `_design/docpage.css` | No change needed — tip callout title/icon already `var(--su-blue)` (15.83:1), inline code already `--su-orange-deep` on `--su-orange-10` (6.60:1). Verified, not re-edited. |
| `_design/landing.css` | No change (its nav/CTAs use the already-accessible shared tokens). |

## render.py line count vs ceiling

**299 / 300.** Under the hard ceiling, so the thin-renderer path holds — the
MkDocs-Material escape hatch was NOT triggered. The single biggest budget risk
(the custom callout plugin) came in at ~50 lines and works; static display data
was moved to `kb_config.py` to protect the budget (templates and config data do
not count against the renderer per the spec).

## Smoke-test result

`python tools/render.py` and `python tools/build-one.py` both succeed (exit 0).
Validated against the seed page + two synthetic pages (since removed):

- **Callouts**: `> [!warning]` / `> [!tip]` render as exact `.callout--warning` /
  `.callout--tip` with inner `svg.callout-icon` + `p.callout-title` + body `<div>`,
  matching `docpage.css`. No stray empty `<p>` (must-fix verified).
- **Code block**: single `<pre><code class="highlight">` with Pygments token spans
  — no nested `<pre>`/`<div>`. `pygments.css` is scoped under `.article-body
  .highlight` with the dark `native` style (legible on the navy `#0b1442` block)
  and the container-background + global `pre{}` base rules stripped (Pygments-vs-CSS
  conflict resolved).
- **TOC**: heading `id`s match TOC `href`s exactly. The 0-H2 page emits NO
  `doc-toc` aside (`{% if toc %}` guard) — no empty rail, no scrollspy flicker.
- **Related dedup**: seed has a hand-authored `## Related` → renderer did NOT
  auto-append (1 `id="related"`). A page WITHOUT `## Related` got exactly 1
  auto-appended Related section with `.html` links (must-fix verified; detection
  is `^##\s+Related\s*$` regex on the SOURCE markdown).
- **.md mirror**: byte-verbatim copy; 0 `[[wikilink]]`, 0 widgets, all 8
  frontmatter fields present and correctly typed (`page_id` quoted, `last_modified`
  `YYYY-MM-DD`, `tags`/`audience` lists).
- **Dual-output parity**: every `.html` has a sibling `.md` at the same path.
- **llms.txt / sitemap.xml / robots.txt**: all emitted, grouped by dept→group in
  `GROUP_ORDER`, descriptions non-empty, sitemap has `lastmod`, robots names all 5
  agents + the absolute Sitemap line.
- **HTML well-formed**: both doc page and landing parse via `html.parser`.
- **Chrome**: breadcrumbs/sidebar/meta/copy-button/footer-disclaimer all present;
  base_url (`/su-kb-site`) on every asset/link; canonical → `.html`,
  `rel=alternate type=text/markdown` → `.md`; zero "Quartz".

## Must-fix items addressed

1. **linkify build-breaker** — set `linkify: false` in the MarkdownIt config (the
   cheaper, zero-risk choice; Confluence autolinks are already explicit). Done.
2. **Callout inline-strip stray `<p>`** — core rule re-parses the stripped inline
   (`md.parseInline`) instead of nulling children; the title becomes a real
   `p.callout-title`, body re-renders cleanly. Verified no empty `<p>`.
3. **Dependency list** — `linkify-it-py` is installed; config uses `linkify:false`
   regardless, so neither path misleads. Done.
4. **Related double-emit** — detection runs on SOURCE markdown via
   `^##\s+Related\s*$` (MULTILINE), survives anchor-slugging. Verified both ways.
5. **Pygments-vs-navy conflict** — resolved (see smoke-test): `nowrap=True` + dark
   `native` style + scoped, background-stripped `pygments.css`. No nested pre.
6. **Landing "Built on Quartz"** — removed from `landing.html.jinja` footer (and
   the docpage template). copy-markdown.js comment drift is cosmetic (left as-is;
   noted below).
7. **Path contract for directory indexes** — the MVP corpus has no directory-index
   pages yet; leaf pages emit flat `<slug>.html` + `<slug>.md` siblings, satisfying
   the copy-button strip-and-append rule. When group/dept index pages are added,
   the copy button should be leaf-only OR a sibling `<subdir>.md` emitted (flagged
   in Remaining gaps).
8. **md-mirror GFM-alert allowlist** — the `.md` mirror keeps `> [!warning]` etc.
   verbatim (legitimate GFM); the rubric-#2 grep must flag `[[`/`![[` only, NOT
   `[!x]`. Documented here for the lint gate.
9. **mdit-py-plugins has no `[!x]` alert plugin** — confirmed; the custom
   `callout_plugin` is mandatory and is what we shipped.

## Design positions stated (gaps the review flagged in the broader design)

- **Aaron Q4 (access)**: MVP posture is **public-only, no app-level access
  control**. The real boundary is Confluence-side RBAC upstream; page-level
  restriction fields were deliberately dropped from the 8-field schema, and
  `robots.txt` intentionally opens the site to retrieval agents. Stated so the
  Stage-9 memo has a grounded position rather than a hand-wave.
- **`audience` field**: required by the schema and lint-checked, but currently
  has **no output consumer** (not in llms.txt/meta/sidebar). Kept for now as a
  forward hook (e.g., future audience filtering / FAQPage-style signals); decide
  in a later session whether to surface it or drop to a 7-field schema.
- **schema.org / JSON-LD**: intentionally NOT emitted (null empirical evidence).

## Remaining gaps for the human (export + deploy are outside this workflow)

1. **The corpus does not exist yet.** Only the single seed page is present.
   The `~29-page` rubric tests (schema lint across 29, parity count, bullet-per-page
   llms.txt) cannot run until the Stage 3g live Confluence export succeeds. That
   export needs the Atlassian API (end-user-simulation only — needs Julian's
   go-ahead). **Blocking sequencing dependency**, not a design choice. `render.py`
   is gated behind it: it assumes Stage 3 already rewrote wikilinks → relative
   `.md` and emitted the 8-field schema.
2. **copy-markdown.js header comment** still says "Quartz emit-md-mirror plugin"
   (cosmetic; functionally correct). Update to "tools/render.py emits these
   (Stage 5)" when convenient.
3. **Directory-index pages** (`/data-ai/`, `/data-ai/claude/`) are not generated
   yet — the landing cards link to `./claude/` etc. which will 404 until those
   index pages exist or the links point at a leaf. Add group/dept index generation
   (and the copy-button leaf-only guard) when the real corpus lands.
4. **`og:image`**: no per-page or site-default image set (SVG-only logo; OG ignores
   SVG). Add a PNG fallback before relying on social-card previews.
5. **base_url** is hard-coded to `/su-kb-site` (project-page deploy). Change to `""`
   if a custom domain (e.g. `kb.its.syr.edu`) is added via CNAME.
