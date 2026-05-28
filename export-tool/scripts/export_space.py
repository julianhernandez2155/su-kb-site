"""Thin CLI: export one Confluence space to markdown.

Usage:
    python scripts/export_space.py ITSAI

Reads sync_config.yaml from the export-tool root and ATLASSIAN_EMAIL /
ATLASSIAN_TOKEN from a repo-root .env (or the process environment). Streams
per-page progress events to stdout. Does NOT touch the network until invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without `pip install -e .` — put src/ on the path.
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from su_kb_export.config import SyncConfig
from su_kb_export.puller import ConfluencePuller, load_credentials


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python scripts/export_space.py <SPACE_KEY>", file=sys.stderr)
        return 2
    space_key = argv[1]

    cfg = SyncConfig.load(_ROOT / "sync_config.yaml")
    # Look for .env at the export-tool root, then the site repo root.
    env_path = next(
        (p for p in (_ROOT / ".env", _ROOT.parent / ".env") if p.exists()),
        None,
    )
    email, token = load_credentials(env_path)
    if not (email and token):
        print(
            "ATLASSIAN_EMAIL / ATLASSIAN_TOKEN not set — add them to .env or "
            "the environment before exporting.",
            file=sys.stderr,
        )
        return 1

    puller = ConfluencePuller(cfg, email, token)
    for event in puller.pull_space(space_key):
        print(f"[{event.kind}] {event.payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
