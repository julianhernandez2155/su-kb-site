from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .agent_loop import run_agent_for_site_question
from .config import BenchConfig, load_config, load_questions
from .fetcher import Fetcher
from .judge import judge_question
from .openrouter_client import OpenRouterClient, load_openrouter_api_key
from .report import new_results, write_report
from .retrieval_probe import run_retrieval_probe_for_site_question
from .surface_audit import audit_sites


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_site_bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the benchmark harness.")
    run_parser.add_argument("--config", required=True, help="Path to config.yaml")
    run_parser.add_argument("--questions", required=True, help="Path to questions.yaml")
    run_parser.add_argument("--out", required=True, help="Output directory, e.g. results/latest")
    run_parser.add_argument("--surface-only", action="store_true", help="Run no-paid surface and retrieval probes; no OpenRouter calls.")
    run_parser.add_argument("--skip-judge", action="store_true", help="Run agent fetch loop but skip judge calls.")

    args = parser.parse_args(argv)
    if args.command == "run":
        return run_command(args)
    parser.error(f"unknown command: {args.command}")
    return 2


def run_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    questions = load_questions(args.questions)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = new_results(
        config_summary=_config_summary(config),
        config_path=str(Path(args.config)),
        questions_path=str(Path(args.questions)),
    )

    fetcher = Fetcher(
        timeout_seconds=config.timeout_seconds,
        user_agent=config.user_agent,
    )
    try:
        surface = audit_sites(config.sites, fetcher)
        results["surface_audit"] = surface
        _write_json(out_dir / "surface_audit.json", surface)

        retrieval_probes = _run_retrieval_probes(config, questions, fetcher, out_dir)
        results["retrieval_probes"] = retrieval_probes

        api_key = load_openrouter_api_key()
        if args.surface_only:
            results["errors"].append("surface_only: OpenRouter agent and judge runs skipped.")
            write_report(out_dir, results)
            print(f"Wrote surface-only report to {out_dir}")
            return 0

        if not api_key:
            results["errors"].append("OPENROUTER_API_KEY missing; agent fetch-loop and judge skipped.")
            write_report(out_dir, results)
            print("OPENROUTER_API_KEY missing; wrote surface audit and skipped paid OpenRouter calls.")
            return 2

        openrouter = OpenRouterClient(
            api_key=api_key,
            base_url=config.openrouter_base_url,
            timeout_seconds=max(60.0, config.timeout_seconds),
        )
        try:
            agent_runs = _run_agent_loops(config, questions, fetcher, openrouter, out_dir)
            results["agent_runs"] = agent_runs
            if args.skip_judge:
                results["errors"].append("skip_judge: judge calls skipped.")
            else:
                judgments = _run_judge(config, questions, agent_runs, openrouter, out_dir)
                results["judgments"] = judgments
        finally:
            openrouter.close()

        write_report(out_dir, results)
        print(f"Wrote benchmark report to {out_dir}")
        return 0
    finally:
        fetcher.close()


def _run_agent_loops(
    config: BenchConfig,
    questions,
    fetcher: Fetcher,
    openrouter: OpenRouterClient,
    out_dir: Path,
) -> list[dict[str, Any]]:
    runs_dir = out_dir / "agent_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    for question in questions:
        for site in config.sites:
            run = run_agent_for_site_question(
                client=openrouter,
                fetcher=fetcher,
                config=config,
                site=site,
                question=question,
            )
            runs.append(run)
            _write_json(runs_dir / f"{question.id}__{site.name}.json", run)
    return runs


def _run_retrieval_probes(
    config: BenchConfig,
    questions,
    fetcher: Fetcher,
    out_dir: Path,
) -> list[dict[str, Any]]:
    probes_dir = out_dir / "retrieval_probes"
    probes_dir.mkdir(parents=True, exist_ok=True)
    probes = []
    for question in questions:
        for site in config.sites:
            probe = run_retrieval_probe_for_site_question(
                fetcher=fetcher,
                site=site,
                question=question,
                top_k=config.retrieval_top_k,
                allow_external_fetches=config.allow_external_fetches,
            )
            probes.append(probe)
            _write_json(probes_dir / f"{question.id}__{site.name}.json", probe)
    _write_json(out_dir / "retrieval_probes.json", probes)
    return probes


def _run_judge(
    config: BenchConfig,
    questions,
    agent_runs: list[dict[str, Any]],
    openrouter: OpenRouterClient,
    out_dir: Path,
) -> list[dict[str, Any]]:
    judge_dir = out_dir / "judge"
    judge_dir.mkdir(parents=True, exist_ok=True)
    judgments = []
    for question in questions:
        site_runs = [run for run in agent_runs if run.get("question", {}).get("id") == question.id]
        judgment = judge_question(
            client=openrouter,
            config=config,
            question=question,
            site_runs=site_runs,
        )
        judgments.append(judgment)
        _write_json(judge_dir / f"{question.id}.json", judgment)
    return judgments


def _config_summary(config: BenchConfig) -> dict[str, Any]:
    return {
        "sites": [
            {
                "name": site.name,
                "start_url": site.start_url,
                "machine_root_url": site.resolved_machine_root_url,
                "protected_design": site.protected_design,
            }
            for site in config.sites
        ],
        "agent_model": config.models.agent,
        "judge_model": config.models.judge,
        "max_fetches": config.max_fetches,
        "retrieval_top_k": config.retrieval_top_k,
        "max_page_chars": config.max_page_chars,
        "allow_external_fetches": config.allow_external_fetches,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
