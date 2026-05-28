"""Static configuration + display data for the SU KB renderer.

Pure data, no logic — kept out of render.py so the renderer stays under its
300-line maintainability ceiling (ADR-0002). Edit labels / card copy here.
"""

SITE_ORIGIN = "https://julianhernandez2155.github.io"
BASE_URL = "/su-kb-site"
GITHUB_URL = "https://github.com/julianhernandez2155/su-kb-site"
ASSETS = ["tokens.css", "docpage.css", "landing.css", "copy-markdown.js"]

DEPT_LABELS = {"data-ai": "Data & AI"}
LABELS = {
    "data-ai": "Data & AI", "claude": "Claude", "copilot": "Microsoft Copilot",
    "gemini": "Google Gemini", "clementine-platform": "mentorAI / Clementine",
    "ai-general-information": "AI General Information", "guides": "Cross-cutting guides",
    "example-uses": "Example Uses",
}
GROUP_ORDER = ["claude", "copilot", "gemini", "clementine-platform", "ai-general-information"]

# Index-page intro blurbs by directory group slug. Falls back to a generated
# "Browse the N pages…" line when a group isn't listed here.
INDEX_INTROS = {
    "claude": "Anthropic's Claude at Syracuse — policy, setup, connectors, and worked example uses.",
    "copilot": "Microsoft Copilot policy and guidance for university data.",
    "gemini": "Google Gemini at SU — login, posture, and NotebookLM / study workflows.",
    "clementine-platform": "Syracuse's mentorAI / Clementine platform — build mentors, configure tools, use the API.",
    "ai-general-information": "Cross-cutting AI guidance — the approved-tools list and creative AI workflows.",
    "example-uses": "Concrete, reviewed examples of using Claude for real student and staff tasks.",
}
COLLAPSE_GUARD = {"ai-at-syracuse-university", "ai"}
AGENTS = ["Claude-User", "ClaudeBot", "GPTBot", "PerplexityBot", "Google-Extended"]

# Inline SVG icon paths reused from docpage.html (triangle / circle-i).
CALLOUT_ICONS = {
    "warning": ('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 '
                '3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/>'
                '<line x1="12" y1="17" x2="12.01" y2="17"/>'),
    "tip": ('<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>'
            '<line x1="12" y1="16" x2="12.01" y2="16"/>'),
}
CALLOUT_ICONS["note"] = CALLOUT_ICONS["tip"]
CALLOUT_ICONS["info"] = CALLOUT_ICONS["tip"]

# Landing card metadata: (icon, title, tag, featured, desc, kinds).
CARD_META = {
    "claude": ("C", "Claude", "Premium", True,
               "Anthropic's Claude — data classification, retention & training opt-out, "
               "premium seats, Claude Code setup, M365 connector, MCP and Cowork posture.",
               "FAQ · Setup · Policy"),
    "copilot": ("M", "Microsoft Copilot", None, False,
                "Copilot policy for university data — retention, training opt-out, M365 "
                "integration, and the protected vs commercial Copilot distinction at SU.", "FAQ"),
    "gemini": ("G", "Google Gemini", None, False,
               "Gemini at SU — g.syr.edu login, training and retention posture, Drive access "
               "rules, plus NotebookLM and Smart Study Companion workflows.", "FAQ · Workflows"),
    "clementine-platform": ("m", "mentorAI", "Clementine", False,
                            "Syracuse's own private AI platform for course-specific mentors. "
                            "Build a mentor, configure tools, choose an LLM, use the API.",
                            "Setup · API"),
    "ai-general-information": ("★", "AI General Information", None, False,
                "The canonical approved-tools list — which AI tools are approved for which data "
                "classifications — plus creative cross-platform AI workflows.", "Policy · Workflows"),
}
