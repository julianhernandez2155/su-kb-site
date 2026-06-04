# AI Retrieval Optimization Report - 2026-06-03

Scope: Julia's `su-kb-site` versus Shahaan's `su-kb-pages-demo`, focused on fast WebFetch-style retrieval for Syracuse University AI support questions.

Design guard: Julia's clementine-quality visual design is a protected strength. The recommendations here borrow only machine-surface ideas that preserve or improve that design. Do not copy lower-polish UI patterns from the comparison site.

## What we are testing

The goal is not traditional vector RAG. The current student workflow is closer to agentic web retrieval:

1. A student asks an SU AI question in ChatGPT, Claude, Gemini, Perplexity, or another tool.
2. A preloaded skill or instruction tells the agent where the SU knowledge base starts.
3. The agent should fetch a compact routing surface, ideally `llms.txt`.
4. The agent should choose the right Markdown page, fetch that `.md`, and answer with provenance.

So the benchmark should measure:

- Can the agent discover the machine-readable surface?
- Does `llms.txt` route the question to the right `.md` page quickly?
- Does the fetched Markdown carry enough provenance to cite the original source?
- How many fetches, bytes, and redirects are needed before the answer is ready?

## Research takeaways

- The `llms.txt` convention is best treated as an inference-time routing index. It is most useful when the user, skill, or tool explicitly asks the model to fetch it first. Source: [llms.txt proposal](https://llmstxt.org/).
- `llms-full.txt` is an optional full-corpus companion. It is useful for small, stable documentation sites or one-shot deep context, but should not be the default for ordinary student questions because it costs more tokens and bytes. Source: [agent-readiness `llms-full.txt` spec](https://specification.website/spec/agent-readiness/llms-full-txt/).
- Retrieval crawlers and training crawlers are different. OpenAI documents `OAI-SearchBot`, `ChatGPT-User`, and `GPTBot`; Anthropic documents `Claude-User`, `Claude-SearchBot`, and `ClaudeBot`; Perplexity documents `PerplexityBot` and `Perplexity-User`; Google robots handling remains centered on Googlebot, while `Google-Extended` is not a Googlebot replacement. Sources: [OpenAI crawlers](https://platform.openai.com/docs/bots), [Claude web fetch](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool), [ClaudeBot support](https://support.claude.com/en/articles/8896518-what-is-claudebot), [Perplexity bots](https://docs.perplexity.ai/guides/bots), [Google robots.txt docs](https://developers.google.com/search/reference/robots_txt).
- X/Grok documentation explicitly advertises `/llms.txt`, `/llms-full.txt`, and `.well-known` variants as machine-readable docs surfaces. Source: [X API llms.txt docs](https://docs.x.com/tools/llms-txt).

## Before-fix scan summary

Live scan was run against:

- Julia: `https://julianhernandez2155.github.io/su-kb-site/`
- Shahaan: `https://shahaank.github.io/su-kb-pages-demo/itsai/`

| Surface | Julia live before fixes | Shahaan `/itsai/` route |
|---|---:|---:|
| Homepage | 200 | 200 |
| `robots.txt` at configured route | 200 | 404 |
| `sitemap.xml` at configured route | 200 | 404 |
| `llms.txt` at configured route | 200 | 404 |
| `llms-full.txt` at configured route | 404 | 404 |
| Markdown page twins | 29/29 sampled OK | linked pages OK from project root |
| Markdown `source_url` frontmatter | 29/29 sampled OK | not detected in sample |
| Homepage Markdown alternate | not present | present |
| JSON-LD | not detected | present |

Important nuance: Shahaan's machine surfaces work at the project root, `https://shahaank.github.io/su-kb-pages-demo/`, where `llms.txt` and `llms-full.txt` are available. They do not work at the provided `/itsai/` skill route. That means Shahaan's site has useful machine-surface ideas, but the configured entry point is fragile for a preloaded skill.

## Fixes applied

These changes are generated retrieval surfaces only. They do not edit `site/content/`, `_design/` styling, the live design language, or the user-facing layout.

- Expanded generated `robots.txt` retrieval allowlist in `tools/kb_config.py`:
  - OpenAI: `OAI-SearchBot`, `ChatGPT-User`, `GPTBot`
  - Anthropic: `Claude-User`, `Claude-SearchBot`, `ClaudeBot`, `anthropic-ai`
  - Perplexity: `PerplexityBot`, `Perplexity-User`
  - Google and general search: `Googlebot`, `Google-Extended`
  - Additional documented AI/search crawlers: `Applebot`, `Applebot-Extended`, `DuckAssistBot`
- Enriched generated `llms.txt` in `tools/render.py`:
  - Keeps the fast routing-index role.
  - Adds tags and audience terms to each entry.
  - Adds small retrieval aliases for high-value ambiguous pages: Claude products, Claude purchase/API access, NotebookLM, mentorAI API, and approved tools.
  - Explicitly tells agents to fetch the chosen `.md` page and cite `source_url` frontmatter.
- Added generated `llms-full.txt`:
  - Concatenates the public Markdown corpus with per-page metadata.
  - Includes `url`, `markdown_url`, `source_url`, `page_id`, tags, audience, and last-modified metadata.
  - Intended as an optional full-context fallback, not the default skill target.
- Added generated root `index.md`:
  - Gives agents a Markdown homepage if they start at the site root.
  - Links directly to `llms.txt`, `llms-full.txt`, and major sections.
- Added `.well-known/llms.txt` and `.well-known/llms-full.txt` copies inside the GitHub Pages project path.
- Added HTML `<link rel="alternate">` entries for `index.md`, `llms.txt`, and `llms-full.txt`.
- Added JSON-LD:
  - Homepage and hub pages emit `CollectionPage`.
  - Doc pages emit `TechArticle` with Markdown encoding and `citation` pointing to frontmatter `source_url`.

## Local verification after fixes

Local render passed:

```powershell
python tools/render.py
```

Result:

- Rendered 29 pages and 7 index pages.
- No broken-link warnings were printed.
- Generated `site/_site/llms.txt`: 10,874 bytes.
- Generated `site/_site/llms-full.txt`: 160,217 bytes.
- Generated `site/_site/index.md`: 1,263 bytes.
- Generated `site/_site/.well-known/llms.txt` and `.well-known/llms-full.txt`.
- JSON-LD was detected in the generated homepage and a generated doc page.

Local no-paid retrieval probe over the generated site:

| Question | Expected Markdown page rank | Top result |
|---|---:|---|
| Claude Chat vs Code vs API | 1 | `Understanding Claude Products: Chat, Code, and API` |
| NotebookLM study/research support | 1 | `How to use Google NotebookLM` |
| mentorAI API guidance | 1 | `mentorAI - Using the API` |

Smoke checks passed:

```powershell
python -m compileall tools/agent_site_bench/agent_site_bench tools/render.py
python -m unittest discover -s tests
```

No paid OpenRouter benchmark calls were run.

## Keep, borrow, fix, investigate, do not regress

Keep:

- Julia's existing visual system and clementine design quality.
- `llms.txt -> .md page -> source_url` as the primary retrieval path.
- Per-page Markdown twins with frontmatter provenance.
- The copy/raw Markdown affordances on doc pages.

Borrow:

- Shahaan's `llms-full.txt` idea, but use it as a fallback rather than the default.
- Shahaan's homepage Markdown alternate idea.
- Shahaan's JSON-LD idea, as supplemental metadata.

Fix:

- After deployment, confirm the new public URLs return 200:
  - `https://julianhernandez2155.github.io/su-kb-site/llms-full.txt`
  - `https://julianhernandez2155.github.io/su-kb-site/index.md`
  - `https://julianhernandez2155.github.io/su-kb-site/.well-known/llms.txt`
  - `https://julianhernandez2155.github.io/su-kb-site/.well-known/llms-full.txt`
- Keep the skill pointed at Julia's project root or `/llms.txt`, not a section path that lacks machine files.

Investigate:

- Whether the org skill should force the exact first fetch to `/llms.txt` or allow homepage-first discovery.
- Whether the benchmark should add a live ChatGPT/Claude/Gemini manual run log after deployment.
- Whether a section-level `data-ai/llms.txt` would help if future skills start inside `/data-ai/`.

Do not regress:

- Do not remove `source_url` from Markdown frontmatter.
- Do not make `llms-full.txt` the normal path for every question.
- Do not optimize for passive crawler discovery at the expense of the actual skill/WebFetch workflow.
- Do not copy lower-polish UI patterns from the comparison site.

## Manual ChatGPT test protocol

Use this after the site is deployed. Paste the following into ChatGPT with browsing/web access enabled:

```text
You are testing a public Syracuse University ITS Data & AI knowledge-base retrieval workflow.
Do not answer from memory.

Start by fetching this URL:
https://julianhernandez2155.github.io/su-kb-site/llms.txt

Then:
1. Choose the most relevant Markdown URL from llms.txt for the question below.
2. Fetch that .md URL.
3. Answer in 5 bullets or fewer.
4. Cite the fetched Markdown URL.
5. If the Markdown frontmatter has source_url, cite that too.
6. End with a tiny audit block:
   - URLs fetched
   - Fetch count
   - Whether you used HTML, Markdown, or llms-full.txt

Question: What is the difference between Claude Chat, Claude Code, and Claude API access at Syracuse University, and how do I request each?
```

Expected behavior:

- It should fetch `llms.txt`.
- It should choose `/data-ai/claude/understanding-claude-products-chat-code-and-api.md` for the main conceptual answer.
- It may also fetch `/data-ai/claude/purchase-claude-code-and-claude-api-access.md` if the request/purchase part needs more detail.
- It should report Markdown use and cite `source_url`.

Run the same script with these questions:

```text
How can someone at Syracuse use Google NotebookLM for study or research support?
```

Expected primary page:

```text
https://julianhernandez2155.github.io/su-kb-site/data-ai/gemini/how-to-use-google-notebooklm.md
```

```text
Where should a developer look for mentorAI API guidance, and what setup or security details matter?
```

Expected primary page:

```text
https://julianhernandez2155.github.io/su-kb-site/data-ai/clementine-platform/mentorai-using-the-api.md
```

## CLI benchmark path

For no-paid surface and retrieval probes:

```powershell
cd "C:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site\tools\agent_site_bench"
python -m agent_site_bench.cli run --config config.yaml --questions questions.yaml --out results/latest --surface-only
```

For a real OpenRouter agent/judge benchmark, only run after setting `OPENROUTER_API_KEY` and intentionally approving paid calls for that session:

```powershell
cd "C:\Users\julia\OneDrive - Syracuse University\Desktop\Workspace\SU_AI_Intern\prototypes\su-kb-site\tools\agent_site_bench"
python -m agent_site_bench.cli run --config config.yaml --questions questions.yaml --out results/latest
```

Primary agent model requirement: the model must support OpenAI-compatible tool calls through OpenRouter. The benchmark's primary path gives the agent only the configured start URL and a `fetch_url` tool, then measures how quickly it reaches the right Markdown and answer.
