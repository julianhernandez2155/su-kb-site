# Codex design review — SU ITS Data & AI KB

## TL;DR
Iterate before porting. The visual direction is strong enough to keep, but the current design fails signoff on accent-color contrast, 360px navigation overflow, mobile doc-page ordering, and unreliable TOC active-state behavior.

Testing note: the in-app browser blocked direct `file://` navigation, so I used a no-build static preview of the same `_design/` files at `http://127.0.0.1:8801/`. That changes the copy-button fallback from a `file://` fetch failure to a local 404, but it exercises the same fallback branch and the same rendered HTML/CSS/assets.

## Screenshots
- Landing: [1440](screenshots/codex-review-2026-05-28/landing-1440.png), [1024](screenshots/codex-review-2026-05-28/landing-1024.png), [768](screenshots/codex-review-2026-05-28/landing-768.png), [480](screenshots/codex-review-2026-05-28/landing-480.png), [360](screenshots/codex-review-2026-05-28/landing-360.png)
- Doc page: [1440](screenshots/codex-review-2026-05-28/docpage-1440.png), [1024](screenshots/codex-review-2026-05-28/docpage-1024.png), [768](screenshots/codex-review-2026-05-28/docpage-768.png), [480](screenshots/codex-review-2026-05-28/docpage-480.png), [360](screenshots/codex-review-2026-05-28/docpage-360.png)
- Key states: [landing skip focus](screenshots/codex-review-2026-05-28/landing-focus-skip.png), [landing primary hover](screenshots/codex-review-2026-05-28/landing-hover-primary-button.png), [tool-card area](screenshots/codex-review-2026-05-28/landing-hover-featured-card.png), [doc skip focus](screenshots/codex-review-2026-05-28/docpage-focus-skip.png), [sidebar hover](screenshots/codex-review-2026-05-28/docpage-hover-sidebar.png), [TOC hover](screenshots/codex-review-2026-05-28/docpage-hover-toc.png), [H2 hover](screenshots/codex-review-2026-05-28/docpage-hover-h2.png), [copy feedback](screenshots/codex-review-2026-05-28/docpage-copy-flash.png)

## Blocker findings
1. Accent surfaces fail WCAG AA for normal-size text
   References: `_design/tokens.css:288`, `_design/tokens.css:302`, `_design/docpage.css:340`, `_design/docpage.css:426`, `_design/docpage.css:553`
   Repro: inspect the primary CTA, copy-as-markdown button, inline code, and blue tip callout. Calculated contrast: white on `#f76900` is 3.01:1; inline code `#d74100` on `#fef0e6` is 4.05:1; tip title/icon `#2b72d7` on `#e9f4ff` is 4.20:1. The button text is not large enough to qualify for the relaxed large-text threshold.
   Recommended fix: use `--su-orange-dark` or navy text on orange surfaces, darken the inline-code foreground/background pairing, and use navy for tip titles/icons or darken the blue.

2. Nav overflows at 360px
   References: `_design/tokens.css:490`, `_design/tokens.css:503`, `_design/landing.html:23`, `_design/docpage.html:23`
   Repro: open the 360px screenshots. The GitHub nav item is clipped off the right edge on both templates.
   Recommended fix: at small widths, hide the GitHub link, collapse nav links into a menu, or shorten to two links. Do not rely only on hiding `.nav-brand-label`; the right-side link set is still too wide.

3. Mobile doc page opens on a long sidebar, not the article
   References: `_design/docpage.html:37`, `_design/docpage.html:39`, `_design/docpage.html:88`, `_design/docpage.css:29`, `_design/docpage.css:133`
   Repro: open the 768/480/360 doc screenshots. At <=880px the layout is one column, but the full navigation sidebar appears before the article, so mobile readers land on a navigation wall instead of the page title/content.
   Recommended fix: on mobile, make the sidebar a collapsed disclosure, move it after the article with CSS order, or replace it with a compact section picker.

## Important findings
1. TOC active-section highlighting is not reliable
   References: `_design/docpage.html:405`, `_design/docpage.html:414`, `_design/docpage.html:425`
   Repro: click through TOC entries. Observed states: `#retention` highlighted `#premium`; `#premium` highlighted `#setup`; `#related` stayed on `#setup`; the first heading sometimes had no active state.
   Recommended fix: replace the current IntersectionObserver-only approach with a scroll-position algorithm that selects the last heading above a top threshold, initializes once on load/hashchange, and updates after TOC clicks.

2. External-link indicator is scoped too narrowly
   References: `_design/docpage.css:497`, `_design/landing.html:313`, `_design/landing.html:331`, `_design/landing.html:363`, `_design/docpage.html:353`
   Repro: footer external links have no `::after` indicator. Trust-banner CTAs use hand-typed arrows, not the CSS rule. Browser inspection returned `content: none` for footer http links.
   Recommended fix: add a shared rule for `.site-footer a[href^="http"]::after`, `.trust-banner a[href^="http"]::after`, and article/action links as needed, with opt-out classes for buttons that already include an icon.

3. Copy fallback works, but expected fallback logs a warning
   References: `_design/copy-markdown.js:86`, `_design/copy-markdown.js:105`
   Repro: click "Copy as markdown" in the standalone preview. The label correctly flashes `Copied (plain text)`, but the console logs `[copy-markdown] .md fetch failed...`.
   Recommended fix: keep the visual fallback, but suppress the warning for known local-preview/file-preview failures or gate it behind a debug flag.

4. Reduced-motion support exists, but I could not dynamically emulate it through the available Chrome extension
   Reference: `_design/tokens.css:599`
   Static check: the CSS globally caps animations/transitions to `0.01ms` and disables smooth scrolling under `prefers-reduced-motion: reduce`.
   Remaining verification: run one manual DevTools rendering-panel toggle before signoff.

## Nice-to-haves
1. Add a print stylesheet
   Current state: absent. For policy/docs pages, print should hide nav/sidebar/TOC/footer chrome, keep article content, expand links, and avoid splitting callouts/code blocks badly.

2. Harden long labels
   References: `_design/docpage.css:94`, `_design/docpage.css:163`
   Sidebar titles with spaces should wrap, and breadcrumbs already flex-wrap. Very long unbroken IDs/titles can still overflow because there is no `overflow-wrap: anywhere` on sidebar links or breadcrumb items.

3. Tighten mobile nav hierarchy
   Even at 480px, the nav is close to the edge. A public institutional KB should not depend on every nav label staying short forever.

## Quartz-porting assessment
The porting plan in `_design/design-notes.md:88` is realistic overall, but I would not port it as raw HTML for long. The one-off `index.md` raw HTML path is fine for a spike, but the production landing should become a Quartz/Preact component keyed by frontmatter (`layout: landing`) so the cards, CTAs, and labels are data-driven.

Replacing Explorer with a curated `DocSidebar` holds up. Quartz Explorer is file-tree-shaped, and this design wants department/section/product ordering. A JSON manifest is reasonable if the export-tool generates it, but the more Quartz-native version is a component that reads `allFiles` plus frontmatter fields like `department`, `section`, `nav_order`, and `hidden`. Avoid hand-maintaining a second sidebar source.

The class names are mostly portable, but several selectors assume exact static markup: `.doc > .doc-sidebar + .doc-article + .doc-toc`, `.toc-list`, `.article-footer`, and `.tool-card-footer`. Quartz's default `TableOfContents` emits `.toc` / `.toc-content`, so either adapt the component output or add selector aliases rather than expecting these classes to appear automatically.

For the emitters, use Quartz v4's emitter shape from `_spike/quartz/plugins/emitters/contentIndex.tsx:95` and `write()` from `_spike/quartz/plugins/emitters/helpers.ts:14`.

- `emit-md-mirror.ts`: iterate `ProcessedContent[]`, use `String(file.value)` as the source markdown rather than `file.data.text` (that is plain extracted text for search/RSS), rewrite wikilinks to relative `.md` links using Quartz slug resolution, then `write({ ctx, slug: file.data.slug!, ext: ".md", content })`.
- `emit-llms-txt.ts`: gather published files, sort by department/section/nav order, and write a concise root `llms.txt` with page title, `.md` URL, description, tags, and department headings via `write({ ctx, slug: "llms", ext: ".txt", content })`.

## What I would change first
1. Fix contrast tokens and component states before any Quartz port.
2. Rework mobile navigation: hide/collapse top nav links and make the doc sidebar mobile-collapsible.
3. Replace the TOC scrollspy with a deterministic active-heading algorithm.

## What's actually good
- Sherman Sans is loading: the page assets include all three local `.woff2` files, and `document.fonts.check('16px "Sherman Sans"')` returned true.
- The Clementine character is not used; `_design/assets/img/` only contains `background.png` and `syracuse-logo-orange.svg`, and the disclaimer is visible in both footers.
- The landing feels designed, not templated. The navy image field, centered type, restrained orange accent, and "AI" gradient work.
- The doc typography is comfortable: 17px / 1.75 body rhythm and a 780px article column feel right for Stripe/Anthropic-style docs density.
- Keyboard focus is strong. Tab order reaches the skip link, nav, cards/sidebar/article links/actions, and the orange focus ring is visible.
- Sticky sidebar and TOC work on desktop; after scrolling, both stayed pinned at the nav offset.
- The feature-card gradient border, H2 hover bar, sidebar hover, TOC hover, and copy-button feedback all render as intentional micro-interactions.
