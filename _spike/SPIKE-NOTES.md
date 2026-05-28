# _spike/ — Quartz + clementine integration test

**Status: disposable.** Scratch space to verify that clementine.syr.edu styling integrates cleanly into Quartz v4's component model before committing to the architecture in `../site/`.

## What's here (when work starts)

- A vanilla Quartz v4 install (from `npx quartz create`)
- Clementine assets dropped into `quartz/styles/` and `quartz/static/`:
  - `site.css` from `C:\Users\julia\Documents\Codex\2026-05-28\can-you-go-to-this-website\`
  - Sherman Sans `.woff2` (3 weights) from the same Codex directory
  - SU color tokens (`--su-blue: #000E54`, `--su-orange: #F76900`, etc.)
- 3 hand-written seed markdown pages in `content/data-ai/` to verify Quartz builds + GH Pages publishes
- Adapted layouts using clementine class names (`.site-nav`, `.hero`, `.assistants`, `.asst-card`, `.data-privacy-banner`, `.site-footer`) per Codex's [`design.md`](C:\Users\julia\Documents\Codex\2026-05-28\can-you-go-to-this-website\design.md)

## Decision gate

Per the plan: **if styling integration fights for >2 days, fall back to MkDocs-Material + `mkdocs-roamlinks-plugin`.** Document the call in a new ADR (`docs/decisions/000X-ssg-fallback.md`).

## When to delete

Once the spike's working setup is promoted into `../site/` (Stage 3 of the plan), delete this entire `_spike/` directory. Per [[handoff-ready-workspace]] convention, the underscore prefix signals "temporary support folder — not for long-term residence."
