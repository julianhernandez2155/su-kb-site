# skill/ context

The Claude skill that students and staff install to route Claude's `WebFetch` tool at this site when they ask SU AI questions.

## Audience

A skill-author or Claude-skill maintainer.

## Workspace structure

- `SKILL.md` — the skill manifest (description, trigger phrases, routing instructions)

## Routing logic (the skill's job)

1. User asks an SU AI question (about Claude at SU, Copilot policy, mentorAI/Clementine, etc.)
2. Skill instructs Claude to fetch `https://<owner>.github.io/su-kb-site/llms.txt` first
3. Claude reads the bullet index and identifies the relevant page
4. Claude fetches `<page>.md` (the raw markdown mirror, not HTML — ~10× more token-efficient)
5. Claude answers with citations back to the canonical source URL

## Patterns used

- **Thin skill, fat index**: most routing intelligence lives in `llms.txt` (in the site repo), not in the skill. The skill only needs to know the site root URL and the "fetch llms.txt first" pattern. If the site reorganizes, only `llms.txt` changes — not the skill.
- **Fetch `.md`, not HTML**: every page has a `.md` companion at the same path with `.md` appended. Claude `WebFetch` already sends `Accept: text/markdown, */*` automatically (per @bcherny 2025-11-12) — this alignment is intentional.

## When working here

- Test the skill by installing it locally (`~/.claude/skills/su-kb/`) and asking Claude a real SU AI question
- If the site URL changes, this is the only file that needs updating
- Versioning: bump the `version` field in SKILL.md frontmatter when behavior changes

## Anti-patterns

- Don't embed the site's content in the skill itself. The skill stays small; the site is the source of truth.
- Don't add Anthropic API calls or `pip install` requirements. This is a markdown-only skill.
