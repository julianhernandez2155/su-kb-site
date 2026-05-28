---
title: Pin Quartz v4 as the static site generator
status: superseded by [0002-pivot-from-quartz-to-thin-renderer.md](0002-pivot-from-quartz-to-thin-renderer.md)
date: 2026-05-28
deciders: Julian Hernandez
consulted: deep-research report (2026-05-28); CC Knowledge Base patterns
---

# ADR-0001 — Pin Quartz v4 as the static site generator

## Context and problem statement

The new site needs a static site generator that (a) ships to GitHub Pages, (b) parses Obsidian-style `[[page-id - title]]` wikilinks natively without preprocessing, (c) handles YAML frontmatter as first-class metadata, and (d) leaves room for custom plugins (we need to emit a parallel `.md` mirror and a root `llms.txt`).

Five candidates evaluated: Quartz (v4 and v5), Jekyll, Hugo, Astro Starlight, MkDocs-Material.

## Decision drivers

- **First-class `[[wikilink]]` support** is mandatory (existing corpus has ~29 pages already in this format from the prior `su-kb-pipeline` export)
- **YAML frontmatter** preserved as-is (existing schema has 20+ fields; rewriting cost is real)
- **GH Pages deployment** must work out of the box
- **Plugin extensibility** for emitting `.md` mirror + `llms.txt`
- **Production-readiness for a 6-week MVP** — no half-finished plugin ecosystems

## Considered options

| Option | Wikilinks | Frontmatter | GH Pages | Plugin ext. | Production-ready |
|---|---|---|---|---|---|
| **Quartz v4** | ✅ Native via `ofm.ts` parser | ✅ gray-matter + js-yaml | ✅ Native | ✅ Plugin system | ✅ 12.3k stars, daily commits, 3.8k forks in prod |
| Quartz v5 | ✅ Native | ✅ Native | ✅ Native | ✅ Modular plugins-per-repo | ⚠️ Plugin ecosystem 3 months old; most plugins ≤2 stars, single maintainer |
| Jekyll | ❌ Abandoned plugins (last touched 2021) | ✅ Native | ✅ Native | ⚠️ Plugin allowlist on GH Pages | ❌ Wikilinks dead |
| Hugo | ❌ Community shortcodes only; brittle | ✅ Native | ⚠️ Requires Actions | ⚠️ Shortcodes | ⚠️ r/ObsidianMD threads describe weeks of regex-fighting |
| Astro Starlight | ❌ No native; requires custom Remark plugin | ✅ Native | ⚠️ Requires Actions | ✅ Strong | ✅ Production-ready, but wikilinks are a porting project |
| MkDocs-Material | ⚠️ Bolt-on (`mkdocs-roamlinks-plugin`, lossy) | ✅ Native | ✅ Native | ✅ Strong plugin ecosystem | ✅ Production-ready, but Obsidian fidelity is weak |

## Decision outcome

**Chosen option: Quartz v4.**

Quartz v4 is the only SSG with native first-class Obsidian-flavored markdown parsing (wikilinks, callouts, embeds, frontmatter) in its core transformer. Per the deep-research report, the relevant code lives at [`quartz/plugins/transformers/ofm.ts`](https://github.com/jackyzha0/quartz/blob/v4/quartz/plugins/transformers/ofm.ts) and parses `[[target]]`, `[[target#heading]]`, `[[target|alias]]`, and `![[embed]]` — the exact syntax our corpus uses. Frontmatter handling at [`frontmatter.ts`](https://github.com/jackyzha0/quartz/blob/v4/quartz/plugins/transformers/frontmatter.ts) coalesces our existing field aliases (`tags`/`tag`, `aliases`/`alias`, multiple `last_modified` variants) — no schema migration required.

**v4 pinned over v5** because v5's plugin-per-repo architecture (under `quartz-community/*`) is only 3 months old as of 2026-05; most plugins have ≤2 stars and one maintainer. v4 has 3,858 forks in production. We can revisit v5 once its plugin ecosystem stabilizes (~Q4 2026).

## Decision gate (escape hatch)

If integrating Codex's clementine styling into Quartz's component model fights for **more than 2 days** during the Stage 2 spike, fall back to **MkDocs-Material + `mkdocs-roamlinks-plugin`**. The wikilink fidelity loss is real (relative-link rewriting required at build time) but the styling and theming ergonomics are stronger. Document the fallback in a new ADR.

## Consequences

### Positive
- Existing `[[page-id - title]]` wikilinks in the salvaged corpus need zero rewriting for source markdown
- YAML frontmatter passes through unchanged
- The Quartz plugin model gives us a clean hook to add `emit-md-mirror.ts` and `emit-llms-txt.ts`
- Active community + maintainer; well-documented

### Negative
- Quartz is digital-garden-shaped by default (graph view, backlinks, popovers); we'll override those components to match clementine's institutional-marketing aesthetic — non-trivial
- Quartz's TypeScript build pipeline is heavier than e.g. plain Jekyll
- Pinning v4 means we'll eventually need a migration to v5

### Neutral
- Multi-department structure is just folder-shape; Quartz doesn't care about it

## Sources consulted

- Deep-research report: `deep-research/reports/2026-05-28-llm-fetch-and-obsidian-ghpages.md` (full evidence + Disagreement Ledger)
- CC KB note: [[folder-architecture-mistakes]] (mistake #7 — don't over-build before using; informs the v4-not-v5 call)
- r/ObsidianMD threads (Quartz v5 release 2026-05-21, Hugo wikilinks cautionary tale 2026-05-06)
- GitHub source inspection: [jackyzha0/quartz/v4/](https://github.com/jackyzha0/quartz/tree/v4) `ofm.ts` + `frontmatter.ts`
