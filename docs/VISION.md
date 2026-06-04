---
version: 1.1
ratified: 2026-06-01
last_amended: 2026-06-01
governance: VISION supersedes STATUS/logs on conflict. Amending it requires a dated version
            bump + a one-line changelog entry below, never a silent rewrite.
---

# Vision — su-kb-site

## North star
A Syracuse-owned, markdown-native knowledge base the university hosts and controls
end-to-end — not a rented hosted wiki — readable by both humans and AI, so SU owns its
institutional knowledge instead of renting it.

## Who it's for
SU teams who need their institutional knowledge owned and controllable (starting with the
ITS Data & AI workspace), the people who browse it, and the Claude agents that fetch it via
`WebFetch`. Without this, SU's knowledge stays locked inside a vendor's proprietary wiki
that the university neither controls nor can make cleanly AI-readable.

## The need
Renting a hosted wiki (Confluence) means no real control over hosting, formatting, access,
or AI-readiness, and content trapped in a proprietary format. SU wants to own the whole
stack — plain files it hosts, styles, gates, and feeds to AI on its own terms.

## What it must always be (principles)
1. **SU-owned, end-to-end.** SU controls hosting, formatting, access, and AI-readiness. No rented wiki as the system of record.
2. **Markdown-native.** Content is plain, portable, inspectable markdown — never locked in a proprietary store.
3. **Dual-consumer by design.** Every page serves both a human browsing and Claude's `WebFetch`; neither is an afterthought.
4. **Public-safe by construction.** Access-restricted content is never published; the pipeline fails closed.
5. **Multi-department-ready.** The structure supports other SU workspaces from day one, even when only one has content.
6. **Thin, inspectable tooling.** The build stays small enough to read end-to-end and free of SSG-framework machinery — no framework creep.

## Leading indicators
- Pages served as both HTML and `.md`, with wikilinks that survive `WebFetch` intact.
- Zero access-restricted pages ever reaching the public site (leak-guard stays green).
- A new department could onboard its content without touching the renderer.
- Stakeholders (Aaron's team) adopt or extend it rather than asking for a hosted wiki.

## Out of scope — do NOT revisit
- **Confluence as a sync target.** It's the legacy origin we're migrating *off*, not a destination to keep in lockstep.
- **The prior `su-kb-pipeline` architecture** (FastMCP + FTS5 + RAG chat/web/access). Frozen artifact — salvage by copying only; don't rebuild that path here.
- **Per-user RBAC / authentication inside this prototype.** Everything is public on GH Pages; gated access is a later phase, not a prototype concern.
- **Production migration to SU's GitHub org** and the eventual three-repo split — Aaron's team owns that call; the prototype lives in one repo.

## Changelog
- v1.0 (2026-06-01): ratified. Authored from the reconciled 2026-06-01 STATUS scope + ADR-0002/0003 as the first VISION-layer pilot.
- v1.1 (2026-06-01): softened Principle 6 — dropped the tactical "single-file renderer" wording (an implementation detail whose line-count gate ADR-0002 already retired) in favor of "small enough to read end-to-end, no framework creep." Per /audit-vision WARN.
