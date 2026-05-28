"""Config loader for sync_config.yaml (su-kb-site, ADR-0002).

Simplified from su-kb-pipeline's config: the public KB drops the three-knob
inclusion logic, space categories, and broadly-accessible-spaces (no access
subsystem). What remains:

  space_departments  — Confluence space_key → site department slug
  collapse_ancestors — wrapper ancestor titles to skip when computing paths
  exclude_segments   — title/ancestor segments that exclude a page (test pages)
  exclude_title_prefixes — title prefixes that exclude a page (e.g. "(Test)")
  enabled_keys       — which spaces the export actually pulls
  output_dir         — where markdown is written (site/content)
  api_base           — Confluence v2 API base
  rate_limit_per_sec — client-side throttle
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SyncConfig:
    space_departments: dict[str, str]
    default_department: str
    collapse_ancestors: list[str]
    exclude_segments: list[str]
    exclude_title_prefixes: list[str]
    enabled_keys: list[str]
    output_dir: Path
    api_base: str
    rate_limit_per_sec: float
    config_path: Path = field(init=False)

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> SyncConfig:
        config_path = Path(path).resolve()
        with config_path.open("r", encoding="utf-8") as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}

        base_dir = config_path.parent
        output_dir = (base_dir / data.get("output_dir", "../site/content")).resolve()

        cfg = cls(
            space_departments=dict(data.get("space_departments", {})),
            default_department=data.get("default_department", "uncategorized"),
            collapse_ancestors=list(data.get("collapse_ancestors", [])),
            exclude_segments=list(data.get("exclude_segments", [])),
            exclude_title_prefixes=list(data.get("exclude_title_prefixes", [])),
            enabled_keys=list(data.get("enabled_keys", [])),
            output_dir=output_dir,
            api_base=data.get("api_base", "https://su-jsm.atlassian.net/wiki/api/v2"),
            rate_limit_per_sec=float(data.get("rate_limit_per_sec", 5)),
        )
        cfg.config_path = config_path
        return cfg

    def department_for(self, space_key: str) -> str:
        return self.space_departments.get(space_key, self.default_department)

    def exclusion_reason(self, title: str, ancestor_path: list[str]) -> str | None:
        """Return why a page is excluded, or None to keep it.

        Excludes if the title starts with any `exclude_title_prefixes` entry,
        or if the title / any ancestor in `ancestor_path` matches an
        `exclude_segments` entry (case-insensitive). Content-quality gate that
        keeps intern scratch + (Test) drafts off the public KB (ADR-0002).
        """
        title = (title or "").strip()
        for prefix in self.exclude_title_prefixes:
            if title.startswith(prefix):
                return f"title prefix {prefix!r}"
        segments = [s.lower() for s in self.exclude_segments]
        for candidate in [title, *ancestor_path]:
            cand = (candidate or "").strip().lower()
            if cand in segments:
                return f"excluded segment {candidate!r}"
            for prefix in self.exclude_title_prefixes:
                if cand.startswith(prefix.lower()):
                    return f"ancestor title prefix {prefix!r}"
        return None

    def is_enabled(self, space_key: str) -> bool:
        """Which spaces the export actually pulls. Empty enabled_keys = all."""
        if not self.enabled_keys:
            return True
        return space_key in self.enabled_keys
