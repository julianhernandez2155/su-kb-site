from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_site_bench.config import load_config, load_questions
from agent_site_bench.report import write_report


class AgentSiteBenchSmokeTest(unittest.TestCase):
    def test_config_questions_and_report_generation(self) -> None:
        temp_context = tempfile.TemporaryDirectory()
        self.addCleanup(temp_context.cleanup)
        temp_dir = Path(temp_context.name)

        config_path = temp_dir / "config.yaml"
        questions_path = temp_dir / "questions.yaml"
        config_path.write_text(
            """
sites:
  - name: julia_current
    start_url: "https://example.com/kb/"
    protected_design: true
  - name: comparison
    start_url: "https://example.org/kb/"
models:
  agent: "tool-calling-model"
  judge: "json-judge-model"
max_fetches: 3
retrieval_top_k: 2
""".strip(),
            encoding="utf-8",
        )
        questions_path.write_text(
            """
questions:
  - id: q1
    question: "Where is the Markdown version?"
    expected_urls:
      - "/kb/page.md"
""".strip(),
            encoding="utf-8",
        )

        config = load_config(config_path)
        questions = load_questions(questions_path)
        self.assertEqual(len(config.sites), 2)
        self.assertEqual(config.max_fetches, 3)
        self.assertEqual(config.retrieval_top_k, 2)
        self.assertEqual(questions[0].id, "q1")
        self.assertEqual(questions[0].expected_urls, ("/kb/page.md",))

        results = {
            "meta": {
                "created_at": "2026-06-03T00:00:00+00:00",
                "design_guard": "Do not recommend copying lower-polish UI patterns from the comparison site.",
            },
            "config_summary": {},
            "surface_audit": {
                "julia_current": {
                    "fetched": {"homepage": {"status_code": 200}},
                    "markdown_twin_links": ["https://example.com/kb/page.md"],
                    "markdown_copy_affordances": ["copy markdown"],
                    "markdown_frontmatter_source_urls": [],
                    "json_ld_blocks": [],
                    "broken_machine_surface_urls": [],
                    "llms_txt_links": [],
                }
            },
            "retrieval_probes": [
                {
                    "question": {"id": "q1"},
                    "site": {"name": "julia_current"},
                    "llms_fetch": {"status_code": 200},
                    "llms_entry_count": 1,
                    "fetch_count": 2,
                    "total_bytes": 100,
                    "expected_urls": ["/kb/page.md"],
                    "expected_hit_rank": 1,
                    "candidates": [
                        {
                            "title": "Page",
                            "fetch": {"status_code": 200},
                        }
                    ],
                }
            ],
            "agent_runs": [],
            "judgments": [],
            "errors": [],
        }
        out_dir = temp_dir / "out"
        results_path, report_path = write_report(out_dir, results)
        self.assertTrue(results_path.exists())
        self.assertTrue(report_path.exists())
        loaded = json.loads(results_path.read_text(encoding="utf-8"))
        self.assertIn("surface_audit", loaded)
        self.assertIn("retrieval_probes", loaded)
        self.assertIn("Design guard", report_path.read_text(encoding="utf-8"))
        self.assertIn("Retrieval Probe", report_path.read_text(encoding="utf-8"))
if __name__ == "__main__":
    unittest.main()
