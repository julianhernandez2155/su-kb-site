# agent_site_bench

CLI-first benchmark harness for comparing two GitHub Pages knowledge-base sites on agent, crawler, and LLM usability. It audits machine-readable surfaces, probes the `llms.txt` -> Markdown retrieval path, runs an OpenRouter tool-calling fetch loop, judges answer quality, and writes both `results.json` and `report.html`.

This tool is intentionally scoped away from the live site implementation. It does not modify `_design/`, `site/content/`, or `tools/render.py`. The report includes a design guard: do not recommend copying lower-polish UI patterns from a comparison site; machine-surface improvements should preserve or improve Julia's existing clementine-quality design.

## Setup

From this directory:

```powershell
cd tools/agent_site_bench
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the examples before editing:

```powershell
Copy-Item config.example.yaml config.yaml
Copy-Item questions.example.yaml questions.yaml
```

Set the OpenRouter key either in the shell or in a local `.env` file:

```powershell
$env:OPENROUTER_API_KEY = "..."
```

Do not commit `.env`; the repo already ignores it.

## Run

```powershell
python -m agent_site_bench.cli run --config config.yaml --questions questions.yaml --out results/latest
```

For a no-paid run that exercises surface discovery plus the `llms.txt` -> Markdown retrieval probe:

```powershell
python -m agent_site_bench.cli run --config config.yaml --questions questions.yaml --out results/surface-only --surface-only
```

## What This Tests

This is not classic vector-store RAG. The SU knowledge-base pattern is static-site retrieval:

1. The installed skill routes an SU AI question to the site.
2. The agent fetches `/llms.txt`.
3. The agent picks one or more relevant `.md` pages.
4. The agent answers from fetched Markdown and cites provenance.

The no-paid retrieval probe tests that path directly by fetching `llms.txt`, ranking its Markdown links against each question, fetching the top candidates, and recording fetch count, bytes, status codes, and expected-page hit rank when `expected_urls` are provided.

## Model Requirements

The primary benchmark only supports OpenRouter chat-completions models that can return OpenAI-compatible `tool_calls`. The agent model must be able to call the provided `fetch_url` tool. If a model answers from prior knowledge, never calls the tool, or returns provider-specific non-tool actions, that run should be treated as invalid for the primary benchmark.

The judge model should reliably follow JSON instructions. If it returns non-JSON text, the harness saves the raw response and marks `judge_parse_error`.

## Outputs

The output folder contains:

- `surface_audit.json` - machine-surface audit for each site.
- `retrieval_probes.json` - no-paid `llms.txt` to Markdown retrieval checks for each question and site.
- `agent_runs/*.json` - per-question, per-site fetch-loop transcript.
- `judge/*.json` - per-question judge result or raw parse failure.
- `results.json` - combined machine-readable benchmark output.
- `report.html` - human-readable report with surface audit, fetch-count-to-answer, answer quality, and keep/borrow/fix/investigate/do-not-regress sections.

Generated outputs under `tools/agent_site_bench/results/` are gitignored.
