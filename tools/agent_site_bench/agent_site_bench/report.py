from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any


DESIGN_GUARD = (
    "Do not recommend copying lower-polish UI patterns from the comparison site. "
    "Borrow only machine-surface ideas that preserve or improve Julia's existing clementine-quality design."
)


def new_results(config_summary: dict[str, Any], config_path: str, questions_path: str) -> dict[str, Any]:
    return {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config_path": config_path,
            "questions_path": questions_path,
            "design_guard": DESIGN_GUARD,
        },
        "config_summary": config_summary,
        "surface_audit": {},
        "retrieval_probes": [],
        "agent_runs": [],
        "judgments": [],
        "errors": [],
    }


def write_report(out_dir: str | Path, results: dict[str, Any]) -> tuple[Path, Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    results_path = out_path / "results.json"
    report_path = out_path / "report.html"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8")
    report_path.write_text(render_html_report(results), encoding="utf-8")
    return results_path, report_path


def render_html_report(results: dict[str, Any]) -> str:
    action_lists = build_action_lists(results)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Site Benchmark Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.5; margin: 2rem; color: #172033; }}
    h1, h2 {{ color: #000E54; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #d7dce8; padding: 0.5rem; vertical-align: top; text-align: left; }}
    th {{ background: #f4f6fb; }}
    code {{ background: #f4f6fb; padding: 0.1rem 0.25rem; border-radius: 3px; }}
    .guard {{ border-left: 4px solid #F76900; padding: 0.75rem 1rem; background: #fff7f0; }}
    .muted {{ color: #596070; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
    .panel {{ border: 1px solid #d7dce8; padding: 1rem; }}
    ul {{ padding-left: 1.25rem; }}
  </style>
</head>
<body>
  <h1>Agent Site Benchmark Report</h1>
  <p class="muted">Generated {escape(results.get("meta", {}).get("created_at", ""))}</p>
  <p class="guard"><strong>Design guard:</strong> {escape(results.get("meta", {}).get("design_guard", DESIGN_GUARD))}</p>

  <h2>Surface Audit</h2>
  {render_surface_audit(results.get("surface_audit", {}))}

  <h2>Retrieval Probe</h2>
  {render_retrieval_probes(results.get("retrieval_probes", []))}

  <h2>Fetch Count To Answer</h2>
  {render_fetch_counts(results.get("agent_runs", []))}

  <h2>Answer Quality</h2>
  {render_answer_quality(results.get("judgments", []))}

  <h2>Keep / Borrow / Fix / Investigate / Do Not Regress</h2>
  <div class="grid">
    {render_action_panel("Keep", action_lists["keep"])}
    {render_action_panel("Borrow", action_lists["borrow"])}
    {render_action_panel("Fix", action_lists["fix"])}
    {render_action_panel("Investigate", action_lists["investigate"])}
    {render_action_panel("Do Not Regress", action_lists["do_not_regress"])}
  </div>

  {render_errors(results.get("errors", []))}
</body>
</html>
"""


def render_surface_audit(surface_audit: dict[str, Any]) -> str:
    if not surface_audit:
        return "<p>No surface audit results.</p>"
    rows = []
    for site_name, audit in surface_audit.items():
        fetched = audit.get("fetched", {})
        root_status = _status(fetched.get("homepage"))
        robots = _status(fetched.get("robots.txt"))
        sitemap = _status(fetched.get("sitemap.xml"))
        llms = _status(fetched.get("llms.txt"))
        llms_full = _status(fetched.get("llms-full.txt"))
        rows.append(
            "<tr>"
            f"<td>{escape(site_name)}</td>"
            f"<td>{escape(root_status)}</td>"
            f"<td>{escape(robots)}</td>"
            f"<td>{escape(sitemap)}</td>"
            f"<td>{escape(llms)}</td>"
            f"<td>{escape(llms_full)}</td>"
            f"<td>{len(audit.get('markdown_twin_links', []))}</td>"
            f"<td>{len(audit.get('markdown_copy_affordances', []))}</td>"
            f"<td>{len(audit.get('markdown_frontmatter_source_urls', []))}</td>"
            f"<td>{len(audit.get('json_ld_blocks', []))}</td>"
            f"<td>{len(audit.get('broken_machine_surface_urls', []))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Site</th><th>Home</th><th>robots.txt</th><th>sitemap.xml</th>"
        "<th>llms.txt</th><th>llms-full.txt</th><th>.md Links</th><th>Markdown/Copy</th>"
        "<th>source_url</th><th>JSON-LD</th><th>Broken</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_fetch_counts(agent_runs: list[dict[str, Any]]) -> str:
    if not agent_runs:
        return "<p>No agent fetch-loop runs.</p>"
    rows = []
    for run in agent_runs:
        rows.append(
            "<tr>"
            f"<td>{escape(run.get('question', {}).get('id', ''))}</td>"
            f"<td>{escape(run.get('site', {}).get('name', ''))}</td>"
            f"<td>{run.get('fetch_count', '')}</td>"
            f"<td>{escape(str(run.get('max_fetches_reached', False)))}</td>"
            f"<td>{escape(str(run.get('invalid_no_fetch_answer', False)))}</td>"
            f"<td>{escape(_preview(run.get('final_answer', ''), 240))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Question</th><th>Site</th><th>Fetches</th><th>Max Hit</th>"
        "<th>No-Fetch Answer</th><th>Answer Preview</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_retrieval_probes(probes: list[dict[str, Any]]) -> str:
    if not probes:
        return "<p>No retrieval probes.</p>"
    rows = []
    for probe in probes:
        llms_status = probe.get("llms_fetch", {}).get("status_code")
        hit = probe.get("expected_hit_rank")
        hit_text = f"rank {hit}" if hit else ("no expected URL" if not probe.get("expected_urls") else "miss")
        top_candidate = ""
        candidates = probe.get("candidates", [])
        if candidates:
            first = candidates[0]
            top_candidate = f"{first.get('title', '')} ({first.get('fetch', {}).get('status_code', '')})"
        rows.append(
            "<tr>"
            f"<td>{escape(probe.get('question', {}).get('id', ''))}</td>"
            f"<td>{escape(probe.get('site', {}).get('name', ''))}</td>"
            f"<td>{escape(str(llms_status))}</td>"
            f"<td>{probe.get('llms_entry_count', '')}</td>"
            f"<td>{probe.get('fetch_count', '')}</td>"
            f"<td>{probe.get('total_bytes', '')}</td>"
            f"<td>{escape(hit_text)}</td>"
            f"<td>{escape(_preview(top_candidate, 180))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Question</th><th>Site</th><th>llms.txt</th><th>Index Entries</th>"
        "<th>Fetches</th><th>Bytes</th><th>Expected Hit</th><th>Top Candidate</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_answer_quality(judgments: list[dict[str, Any]]) -> str:
    if not judgments:
        return "<p>No judge results.</p>"
    rows = []
    for judgment in judgments:
        if judgment.get("judge_parse_error"):
            quality = "judge_parse_error"
            notes = judgment.get("raw_judge_text", "")
            winner = "unknown"
        else:
            quality = json.dumps(
                {
                    "correctness": judgment.get("correctness"),
                    "citation_quality": judgment.get("citation_quality"),
                    "provenance_quality": judgment.get("provenance_quality"),
                    "fetch_efficiency": judgment.get("fetch_efficiency"),
                },
                ensure_ascii=True,
            )
            notes = judgment.get("notes", "")
            winner = judgment.get("winner", "")
        rows.append(
            "<tr>"
            f"<td>{escape(judgment.get('question_id', ''))}</td>"
            f"<td>{escape(str(winner))}</td>"
            f"<td><code>{escape(_preview(quality, 500))}</code></td>"
            f"<td>{escape(_preview(str(notes), 300))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Question</th><th>Winner</th><th>Scores</th><th>Notes</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def build_action_lists(results: dict[str, Any]) -> dict[str, list[str]]:
    surface = results.get("surface_audit", {})
    site_names = list(surface.keys())
    primary = site_names[0] if site_names else "primary site"
    comparison = site_names[1] if len(site_names) > 1 else "comparison site"

    keep = [
        "Keep the human-facing visual polish and clementine-derived design quality as a protected strength.",
        "Keep dual human and agent audiences visible in evaluation criteria.",
    ]
    borrow = [
        f"Borrow from {comparison} only when a machine-surface feature is clearly better and can be added without lowering UI polish.",
    ]
    fix = []
    investigate = []
    do_not_regress = [
        DESIGN_GUARD,
        "Do not degrade accessible typography, spacing, navigation clarity, or SU brand alignment while adding crawler affordances.",
    ]

    for site_name, audit in surface.items():
        broken = audit.get("broken_machine_surface_urls", [])
        if broken:
            fix.append(f"{site_name}: repair {len(broken)} broken machine-surface URL(s).")
        if not audit.get("llms_txt_links") and _status_code(audit, "llms.txt") and _status_code(audit, "llms.txt") < 400:
            borrow.append(f"{site_name}: consider linking llms.txt from the homepage or head metadata for easier discovery.")
        if not audit.get("markdown_twin_links"):
            investigate.append(f"{site_name}: confirm whether .md twins are discoverable from HTML pages or only from llms/sitemap.")
        if not audit.get("markdown_frontmatter_source_urls"):
            investigate.append(f"{site_name}: sample Markdown pages did not expose source_url in frontmatter.")

    parse_errors = [item for item in results.get("judgments", []) if item.get("judge_parse_error")]
    if parse_errors:
        investigate.append(f"Judge JSON parsing failed for {len(parse_errors)} question(s); inspect raw judge text.")

    probes = results.get("retrieval_probes", [])
    if probes:
        for probe in probes:
            site_name = probe.get("site", {}).get("name", "unknown")
            question_id = probe.get("question", {}).get("id", "unknown")
            llms_status = probe.get("llms_fetch", {}).get("status_code")
            if llms_status is None or int(llms_status) >= 400:
                fix.append(f"{site_name}: retrieval probe cannot start from llms.txt for {question_id}.")
            elif probe.get("expected_urls") and not probe.get("expected_hit_rank"):
                investigate.append(f"{site_name}: llms ranking missed the expected page for {question_id}.")
            elif probe.get("expected_hit_rank") == 1:
                keep.append(f"{site_name}: llms ranking found the expected page first for {question_id}.")

    if not results.get("agent_runs"):
        investigate.append("Agent fetch-loop did not run; set OPENROUTER_API_KEY and use a tool-calling model for the primary benchmark.")
    else:
        grouped: dict[str, list[int]] = {}
        for run in results["agent_runs"]:
            grouped.setdefault(run.get("site", {}).get("name", "unknown"), []).append(int(run.get("fetch_count", 0)))
        for site_name, counts in grouped.items():
            keep.append(f"{site_name}: average fetch count was {mean(counts):.1f} across completed runs.")

    return {
        "keep": _dedupe(keep),
        "borrow": _dedupe(borrow),
        "fix": _dedupe(fix or [f"{primary}: no automatic fixes identified from available results."]),
        "investigate": _dedupe(investigate),
        "do_not_regress": _dedupe(do_not_regress),
    }


def render_action_panel(title: str, items: list[str]) -> str:
    body = "".join(f"<li>{escape(item)}</li>" for item in items) if items else "<li>No items.</li>"
    return f"<section class=\"panel\"><h3>{escape(title)}</h3><ul>{body}</ul></section>"


def render_errors(errors: list[Any]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{escape(str(error))}</li>" for error in errors)
    return f"<h2>Run Errors</h2><ul>{items}</ul>"


def _status(record: dict[str, Any] | None) -> str:
    if not record:
        return "missing"
    if record.get("error"):
        return f"error: {record['error']}"
    return str(record.get("status_code"))


def _status_code(audit: dict[str, Any], key: str) -> int | None:
    value = audit.get("fetched", {}).get(key, {}).get("status_code")
    return int(value) if value is not None else None


def _preview(text: str, limit: int) -> str:
    compact = " ".join(str(text).split())
    return compact if len(compact) <= limit else compact[: limit - 3] + "..."


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
