---
title: Design notes — SU ITS Data & AI KB
date: 2026-05-28
---

# Design notes

The design source-of-truth for the SU ITS Data & AI knowledge base. Two templates (landing + doc page) and a shared token system. Standalone HTML/CSS/JS — to be ported into Quartz's Preact components in a follow-up step.

## Aesthetic direction

**Confident institutional.** Refined minimalism with intentional moments of color and motion. Navy-dominant, orange as a precise accent (not splashed everywhere). Sherman Sans throughout. Subtle typographic scale, generous reading rhythm, light elevation on cards.

What this **isn't**:
- Not generic docs-template / not a SaaS-marketing knock-off
- Not the official Clementine product (no character, no chat-widget chrome, footer disclaimer)
- Not Quartz's digital-garden default (no graph view, no Explorer file tree, no popovers)
- Not maximalist — restraint over density

What this **is**:
- A docs site that takes itself seriously
- A landing that says *"this is a real institutional resource"* in the first 2 seconds
- A doc page that reads like Anthropic's or Stripe's docs

## Files in this directory

| File | Purpose |
|---|---|
| `tokens.css` | The design system: fonts, design tokens, reset, accessibility primitives, shared components (buttons, nav, footer, eyebrow, badge). Loaded first on every page. |
| `landing.html` + `landing.css` | Template 1 — site root + department landings. Section order: nav, hero, tool cards, trust banner, footer. |
| `docpage.html` + `docpage.css` | Template 2 — every individual KB article. 3-column grid: sidebar / content / TOC. |
| `copy-markdown.js` | The "Copy as markdown" button behavior. Fetches `<currentPath>.md` and copies to clipboard with visible feedback. Falls back to article text if the `.md` mirror is missing. |
| `assets/` | Sherman Sans `.woff2` (3 weights), `syracuse-logo-orange.svg`, `background.png`. Self-contained so the standalone HTML opens correctly with `file://`. |

To preview locally: open `landing.html` or `docpage.html` directly in a browser. No build step.

## Design moves that earn their space

1. **Hero is single-column, typographic.** Clementine has a 2-column hero with a character on the right. We can't reuse the character (brand-boundary), and an empty right column looks weak. Single-column hero with a centered, large H1 + accent-tinted "AI" word + translucent body panel + dual CTAs is the docs-site move. Page-load reveal staggers each hero element by ~80ms for a calm, intentional entrance.

2. **The hero "AI" gets a gradient text-fill** (orange-light → orange → orange-medium). One visible moment of warmth in an otherwise restrained hero. Read by everyone in the first second.

3. **Featured tool card has a gradient border** (orange → blue) — the Claude card. Same pattern clementine uses for the Class Search card. Signals "this is the primary path" without shouting.

4. **Cards have a `::before` accent bar that scales-in on hover** — left-to-right scale from 0 to 1 on the top edge. Quiet but unmistakable feedback. Cards also lift `-4px` (`-6px` for featured) with elevated shadow.

5. **Tool card CTAs nudge the arrow right on hover** — the gap between text and SVG grows by 4px. Microscopic but the kind of micro-interaction that signals craft.

6. **H2 headings in articles get a left-edge orange bar on hover** — fades in via `::before` scaling. Useful for scanning + signals which sections are linkable.

7. **TOC actively highlights the current section** — IntersectionObserver, no scrollspy library needed.

8. **The article's "Copy as markdown" button is the orange accent button**, not a secondary. Highest-friction action on the page; deserves the primary treatment.

9. **Subtle pulsing dot in the hero meta** — "Auto-synced from Confluence ●" — slow opacity pulse signals liveness.

10. **All buttons translate up `-2px` on hover** with deeper shadow. Consistent gesture across primary / secondary / ghost variants.

## Color and typography decisions

- **Sherman Sans for everything** — only font in the stack. Body, headings, code falls through to system monospace (`ui-monospace`, `SF Mono`, `Cascadia Code`).
- **Body text color** is `#1a1a1a` (not pure black; warmer + softer for long-form reading).
- **Links** use `--su-orange-dark` with a subtle underline (`text-decoration-color: rgba(215, 65, 0, 0.4)`). Hover deepens both color and underline alpha — accessible without screaming.
- **Inline code** is orange tint on orange-10 background. Pops without being harsh.
- **Fenced code blocks** are SU-navy `#0b1442` with a thin orange left accent stripe. Owned by SU brand; not GitHub's grey.
- **External links** get an automatic `↗` indicator via CSS `::after`.

## Accessibility

- Skip link first (`.skip-link`, focus-revealed at top of page)
- `:focus-visible` outline: `3px solid --su-orange` on every focusable element
- Semantic HTML: `<nav>` / `<main>` / `<article>` / `<aside>` / `<footer>` properly placed
- All images have meaningful `alt`
- Color contrast: body on white ≥ 14:1; orange-dark on white ≥ 5.4:1; white on navy ≥ 15:1 — all WCAG AA+
- `prefers-reduced-motion` honored — animations and transitions cap at 0.01ms, scroll-behavior turns off
- Breadcrumbs use `aria-current="page"`
- Sidebar uses `aria-current="page"` to mark active doc
- TOC list items don't need `aria-current` because the IntersectionObserver runs on scroll — but the visual styling (orange left-border + color) is sufficient signal

## What to port into Quartz, and how

Quartz uses Preact components. Each Quartz component lives at `quartz/components/<Name>.tsx`. The current Quartz default config puts components into 4 slots: `head`, `header`, `beforeBody/left/right`, `footer`. Our design overrides specific component contents AND specific styles.

### Required Quartz changes (Stage 3 work, post-spike)

| Concern | Where | What to do |
|---|---|---|
| Navy nav with logo + label | `quartz/components/Header.tsx` (extend or replace) | Replace with our `.site-nav` markup (logo, divider, brand label, nav links). Mount in `quartz.layout.ts` → `sharedPageComponents.header`. |
| Hero (landing only) | `quartz/components/pages/Content.tsx` for `index.md` | Either (a) a new `<HeroLanding/>` component that renders when `frontmatter.layout === "landing"`, or (b) a dedicated `<HomeLanding/>` page component wired via `Plugin.ContentPage()` slot for the root index. Easiest: render the hero section inside the `index.md` body using Quartz's HTML-passthrough plugin, then style via `.hero` class. |
| Tool cards grid | Same as hero — render in `index.md` body | The grid is just `<div class="tools-grid">` with `<a class="tool-card">` items. Quartz's `ObsidianFlavoredMarkdown` plugin already allows raw HTML in markdown bodies. Long-term, a Quartz transformer plugin could read `frontmatter.tools[]` and emit this grid automatically — defer. |
| Doc page sidebar (left) | Replace `quartz/components/Explorer.tsx` *or* write a sibling component | Quartz's Explorer is a file-tree component built from the content folder. Our design wants a CURATED sidebar (sections + items + nested sublists). Easier path: write a new `<DocSidebar/>` component that reads from a JSON sidebar config (one per department), and swap Explorer for it in `quartz.layout.ts`. |
| Doc TOC (right) | `quartz/components/TableOfContents.tsx` | Quartz already builds a TOC from H2/H3. Restyle via `.doc-toc` / `.toc-list` classes — Quartz emits to `<aside class="toc">` by default; map to our class names with selector overrides in custom.scss. IntersectionObserver active-section JS is in our `docpage.html` `<script>` — port to Quartz's `quartz/components/scripts/toc.inline.ts`. |
| Article meta (last updated, page id, tags) | `quartz/components/ContentMeta.tsx` | Restyle the existing component to match `.article-meta` shape. Quartz reads `frontmatter.tags`, `frontmatter.lastModified` — works as-is. |
| Breadcrumbs | `quartz/components/Breadcrumbs.tsx` | Quartz has this. Restyle to match `.breadcrumbs`. |
| Footer | `quartz/components/Footer.tsx` | Replace contents with our 3-column footer markup + the `.footer-bottom` disclaimer row. |
| Copy as markdown button | New emitter + component | Two parts: (1) write a Quartz emitter `emit-md-mirror.ts` that writes `<page>.md` alongside `<page>.html` for every content page (with wikilinks rewritten to relative `.md` links per the deep-research recommendation), (2) add the button to the article footer component, copy our `copy-markdown.js` into `quartz/components/scripts/copy-markdown.inline.ts`. |
| Hero font/colors | `quartz.config.ts` + `quartz/styles/custom.scss` | Already updated in the spike commit. Carry over to `site/quartz/`. |
| llms.txt | New emitter | `emit-llms-txt.ts` Quartz plugin — generates the root `/llms.txt` from the content collection. Pattern from `cloudflare/cloudflare-docs` `src/pages/llms.txt.ts`. |
| Disable Quartz's graph view + popovers + reader mode | `quartz.layout.ts` | Remove `Component.Graph()` and `Component.Backlinks()` from `defaultContentPageLayout.right`. Remove `Component.ReaderMode()` from the Flex. The result is a docs-shaped layout, not a digital-garden one. |

### Style port strategy

1. **Copy `_design/tokens.css` into `site/quartz/styles/tokens.scss`** (rename to `.scss`, no syntactic changes needed — CSS is valid SCSS).
2. **Make `site/quartz/styles/custom.scss` import `tokens` first**, then override Quartz's component-specific stylesheets via the `:where()` selector or class overrides as needed.
3. **Copy `landing.css` and `docpage.css` into `site/quartz/styles/`** as `landing.scss` and `docpage.scss`. They'll be loaded once Quartz's component CSS bundling picks them up via the `Plugin.ComponentResources()` emitter.
4. **Override Quartz's color tokens** in `quartz.config.ts` to match our SU palette (already done in the spike).
5. **Drop the Explorer-related styles** in `quartz/components/styles/explorer.scss` and replace with our `.doc-sidebar` markup once the new `<DocSidebar/>` component lands.

### What stays as-is in Quartz

- Quartz's `ObsidianFlavoredMarkdown` transformer (handles `[[wikilinks]]`, callouts, embeds) — keep.
- Quartz's `GitHubFlavoredMarkdown` (tables, task lists) — keep.
- Quartz's `SyntaxHighlighting` (shiki) — keep, restyle the theme.
- Quartz's `ContentIndex` emitter (sitemap, RSS) — keep.

## Caveats and gotchas

1. **Background image is a copy of clementine's hero `background.png`.** Acceptable for a Syracuse-internal site that doesn't claim to be Clementine. If brand review pushes back, replace with a CSS gradient mesh or a commissioned abstract.

2. **The `.hero h1 .accent` gradient text** assumes the word being styled wraps gracefully. If the H1 ever spans multiple lines on a narrow viewport, the gradient still works but the accent may visually fragment. Acceptable.

3. **The IntersectionObserver TOC** uses `rootMargin: "-30% 0px -60% 0px"` to bias toward sections near the upper third of the viewport. Tuned for content-heavy doc pages; may need adjustment for very short articles.

4. **External link `↗` indicator** is added via CSS `::after`. It won't work for buttons styled as links. Use a hand-placed `↗` in those cases (we did this in the trust-banner CTAs).

5. **`copy-markdown.js` falls back to article text** if the `.md` fetch fails (e.g. during local `file://` preview where no `.md` exists alongside `.html`). Visible feedback differs: "Copied as markdown" vs "Copied (plain text)" — useful debug signal.

6. **Sidebar content is hardcoded in `docpage.html`** for the spike. In production, generate per-department from the content tree (Quartz component) or from a JSON manifest the export-tool writes.

## What to verify visually before sign-off

Open `landing.html` in a browser; confirm:
- [ ] Sherman Sans loads (no fallback to Verdana)
- [ ] Hero gradient overlay reads dark enough that the white H1 has 7:1+ contrast
- [ ] Hero "AI" gradient text renders (orange wash)
- [ ] All 6 tool cards are visible and clickable; Claude card has the gradient border
- [ ] Trust banner has the radial gradient atmosphere (orange wash top-right, blue bottom-left)
- [ ] Footer disclaimer about "not the official Clementine product" is visible

Open `docpage.html` in a browser; confirm:
- [ ] 3-column layout at desktop width; collapses to 2 at <1180px and 1 at <880px
- [ ] Sidebar scrolls independently of the article
- [ ] TOC right rail highlights the active section as you scroll
- [ ] Breadcrumbs flow on narrow widths
- [ ] Callouts (warning, tip) have correct color treatment
- [ ] Code block has the navy background + orange left stripe
- [ ] Inline code is orange-on-orange-10 tint
- [ ] "Copy as markdown" button flashes "Copied (plain text)" on click (no `.md` exists in `file://` preview, so fallback fires — expected)

Once those check out, port into Quartz per the table above.
