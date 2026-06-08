# skill/ context

Claude skills that live with this site. There are **two distinct skills, each in its own
subfolder** (an Agent Skill is a directory whose `SKILL.md` is its entry point, so two skills
can't share one folder):

| Subfolder | Skill | Direction | Status |
|---|---|---|---|
| `drafter/` | **su-kb-page-drafter** — interviews an author and emits a finished, schema-valid page + path + terminal-free GitHub steps | **write** (authoring into the KB) | built (faculty-page-authoring Phase 2) |
| _(retrieval)_ | the **WebFetch routing** skill students install so Claude answers SU AI questions from this site | **read** (retrieving from the KB) | described below; not yet built |

> Naming note: this folder's identity was originally reserved for the *retrieval* skill (see
> the project README / CLAUDE.md, which call `skill/` "the skill students install to route
> WebFetch"). The drafter is a second, write-side skill added later; rather than collide on a
> single `skill/SKILL.md`, each skill gets a subfolder. When the retrieval skill is built it
> should land at `skill/retrieval/SKILL.md`.

## Audience

A skill-author or Claude-skill maintainer.

## The drafter skill (`drafter/`)

- `drafter/SKILL.md` — the Agent Skill (manifest frontmatter + the full drafting instructions).
- `drafter/drafter-prompt.md` — the **identical** instruction body as a no-install copy-paste
  prompt (the guaranteed-reachable fallback if Agent Skills can't be installed in the author's
  Claude workspace).
- **Single source of truth, two delivery vehicles:** the two files mirror each other and both
  mirror the schema rules in [`tools/check_frontmatter.py`](../tools/check_frontmatter.py) (the
  authoritative publish gate). Change one, change all three. Spec:
  [`rpi/faculty-page-authoring/plan/eng.md` §6](../rpi/faculty-page-authoring/plan/eng.md).

## The retrieval skill (read side — not yet built)

The Claude skill that students and staff install to route Claude's `WebFetch` tool at this site
when they ask SU AI questions.

### Workspace structure (when built)

- `retrieval/SKILL.md` — the skill manifest (description, trigger phrases, routing instructions)

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
