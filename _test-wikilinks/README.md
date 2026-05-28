# Empirical wikilink-through-WebFetch test

**Purpose:** Settle whether Claude's `WebFetch` tool preserves and semantically interprets `[[page-id - title]]` wikilinks, or whether we need to rewrite them to relative markdown links for the `.md` mirror.

**Test setup:** 3 representative pages from the real ITSAI corpus, each pushed in two versions:

- `with-wikilinks/` — original Obsidian-style `[[<page-id> - <title>|<alias>]]` syntax
- `with-relative/` — rewritten to standard `[<text>](./<page-id>.md)` markdown links

**Files:** all 3 pages have meaningful wikilink density:
- `534642749.md` — Claude Enterprise (5 wikilinks, all with aliases)
- `483525103.md` — AI @ Syracuse University landing (3 wikilinks + 1 image embed)
- `544505857.md` — mentorAI @ SU (3 wikilinks, mix of aliased and bare)

**Fetched via:** `https://raw.githubusercontent.com/julianhernandez2155/su-kb-site/main/_test-wikilinks/<version>/<page-id>.md` (raw markdown, no GH Pages render, no Quartz)

**Status:** delete after the empirical test concludes (per the design-notes' "decision gate" pattern).
