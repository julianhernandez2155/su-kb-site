#!/usr/bin/env python3
"""Stage 4 PoC — render a single page and inspect it before generalizing.

Reuses the shared core from render.py (build_md/read_page/build_toc/Page/
render_html). Renders just claude-faq.md to _design/output/ so the template
surgery + callout plugin can be eyeballed against the Codex-clean bar.
"""
from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as R  # noqa: E402

SEED = R.CONTENT / "data-ai" / "claude" / "claude-faq.md"
OUTDIR = R.DESIGN / "output"


def main() -> None:
    env = Environment(loader=FileSystemLoader(str(R.DESIGN)),
                      autoescape=select_autoescape(["html", "jinja"]))
    md = R.build_md()
    meta, body = R.read_page(SEED)
    parts = ["data-ai", "claude", "claude-faq"]
    pe = {}
    tokens = md.parse(body, pe)
    page = R.Page(
        meta=meta, body_md=body, html=md.renderer.render(tokens, md.options, pe),
        toc=R.build_toc(tokens), dept="data-ai", slug="claude-faq",
        rel_path="claude/claude-faq", ancestors=["claude"], src=SEED,
        out_html=OUTDIR / "claude-faq.html", out_md=OUTDIR / "claude-faq.md",
    )
    OUTDIR.mkdir(parents=True, exist_ok=True)
    R.OUT = OUTDIR  # so md mirror lands beside the html
    R.render_html(page, [page], env)
    R.emit_md_mirror(page)
    print(f"Wrote {page.out_html}")


if __name__ == "__main__":
    main()
