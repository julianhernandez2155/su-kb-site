#!/usr/bin/env python3
"""SU ITS Data & AI KB — thin renderer (ADR-0002). Renders site/content to
site/_site/: HTML + verbatim .md mirror + llms.txt + llms-full.txt + sitemap.xml + robots.txt
+ landing. Static config/data lives in kb_config.py (off the 300-line ceiling).
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from kb_config import (ASSETS, BASE_URL, CALLOUT_ICONS, CARD_META, COLLAPSE_GUARD,
                       DEPT_LABELS, AGENTS, GITHUB_URL, GROUP_ORDER, INDEX_INTROS,
                       LABELS, SITE_ORIGIN)

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "site" / "content"
DESIGN = ROOT / "_design"
OUT = ROOT / "site" / "_site"
ASSET_V = ""  # content hash appended to asset URLs (?v=) for cache-busting; set in main()
RELATED_RE = re.compile(r"^##\s+Related\s*$", re.MULTILINE)
_MD_LINK_RE = re.compile(r'(href=")([^"]+?)\.md(")')
_ATTACH_RE = re.compile(r'((?:href|src)=")(?:\.\./|\./)*(attachments/[^"]+)(")')
_ALERT_RE = re.compile(r"^\[!(\w+)\]\s*([^\n]*)")
_PYG = HtmlFormatter(nowrap=True, style="native")  # light tokens, legible on navy #0b1442

def _slug(text: str) -> str:
    return re.sub(r"[\s_]+", "-", re.sub(r"[^\w\s-]", "", str(text).lower()).strip())

def _highlight(code: str, lang: str, _attrs) -> str:
    try:  # nowrap -> token spans only; markdown-it's <pre><code> keeps the navy block
        lexer = get_lexer_by_name(lang or "text")
    except ClassNotFound:
        lexer = get_lexer_by_name("text")
    return f'<pre><code class="highlight">{pyg_highlight(code, lexer, _PYG)}</code></pre>'

def callout_plugin(md: MarkdownIt) -> None:
    """GitHub-alert blockquotes (> [!warning] Title) -> docpage.css .callout markup.

    Core rule flags matching quotes + strips the marker line (re-parsing the
    remainder so no stray empty <p>). Open/close rules emit the div pair.
    """
    def core_rule(state):
        toks = state.tokens
        for i, t in enumerate(toks):
            if t.type != "blockquote_open":
                continue
            inl = next((toks[j] for j in range(i + 1, len(toks)) if toks[j].type == "inline"), None)
            m = _ALERT_RE.match(inl.content) if inl else None
            if not m:
                continue
            kind = m.group(1).lower()
            title = m.group(2).strip()
            rest = inl.content[m.end():].lstrip("\n")
            inl.content = rest
            inl.children = md.parseInline(rest, state.env)[0].children if rest else []
            t.meta["callout"] = (kind if kind in ("warning", "tip") else "note", title)

    def open_rule(self, tokens, idx, options, env):
        info = tokens[idx].meta.get("callout")
        if not info:
            return "<blockquote>\n"
        cls, title = info
        icon = CALLOUT_ICONS.get(cls, CALLOUT_ICONS["note"])
        title_html = f'<p class="callout-title">{html.escape(title)}</p>' if title else ""
        return (f'<div class="callout callout--{cls}">'
                f'<svg class="callout-icon" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                f'stroke-linejoin="round" aria-hidden="true">{icon}</svg>'
                f'<div>{title_html}\n')

    def close_rule(self, tokens, idx, options, env):
        # Match the open token (scan back, tracking nesting depth).
        depth = 0
        for j in range(idx - 1, -1, -1):
            if tokens[j].type == "blockquote_close":
                depth += 1
            elif tokens[j].type == "blockquote_open":
                if depth == 0:
                    return "</div></div>\n" if tokens[j].meta.get("callout") else "</blockquote>\n"
                depth -= 1
        return "</blockquote>\n"

    md.core.ruler.push("su_callout", core_rule)
    md.add_render_rule("blockquote_open", open_rule)
    md.add_render_rule("blockquote_close", close_rule)

def build_md() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"html": False, "linkify": False, "typographer": True})
    md.enable("table")
    md.options["highlight"] = _highlight
    md.use(footnote_plugin).use(tasklists_plugin, enabled=True).use(callout_plugin)
    md.use(anchors_plugin, max_level=3, permalink=False, slug_func=_slug)
    return md

def read_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return yaml.safe_load(fm) or {}, body.lstrip("\n")
    return {}, text

def build_toc(tokens) -> str:
    items = [(t.attrGet("id") or "", tokens[i + 1].content)
             for i, t in enumerate(tokens)
             if t.type == "heading_open" and t.tag in ("h2", "h3") and i + 1 < len(tokens)]
    if not items:
        return ""
    lis = "".join(f'<li><a href="#{html.escape(i)}">{html.escape(x)}</a></li>' for i, x in items)
    return f'<ul class="toc-list">{lis}</ul>'

@dataclass
class Page:
    meta: dict; body_md: str; html: str; toc: str  # noqa: E702
    dept: str; slug: str; rel_path: str; ancestors: list  # noqa: E702
    out_html: Path; out_md: Path; src: Path  # noqa: E702

def load_corpus(md: MarkdownIt) -> list[Page]:
    pages = []
    for src in sorted(CONTENT.rglob("*.md")):
        meta, body = read_page(src)
        rel = src.relative_to(CONTENT)
        parts = list(rel.with_suffix("").parts)
        leaked = [s for s in parts if s in COLLAPSE_GUARD]
        if leaked:
            raise SystemExit(f"collapse-guard: '{leaked[0]}' segment leaked into {rel}")
        dept = meta.get("department") or parts[0]
        env = {}
        tokens = md.parse(body, env)
        out_html = OUT.joinpath(dept, *parts[1:]).with_suffix(".html")
        pages.append(Page(meta, body, md.renderer.render(tokens, md.options, env),
                          build_toc(tokens), dept, parts[-1], "/".join(parts[1:]),
                          parts[1:-1], out_html, out_html.with_suffix(".md"), src))
    return pages

def build_sidebar(pages: list[Page], dept: str,
                  current_group: str | None = None, current_slug: str | None = None) -> str:
    """Collapsible grouped nav: dept home + root pages, then one <details> per
    tool group (with page count). example-uses etc. nest as a labelled sublist.
    The group holding the current page is open; the rest stay collapsed so a
    29-page corpus reads as ~5 sections, not one long wall."""
    roots, groups = [], {}
    for p in pages:
        if p.dept != dept:
            continue
        if not p.ancestors:
            roots.append(p)
            continue
        node = groups.setdefault(p.ancestors[0], {"direct": [], "subs": {}})
        if len(p.ancestors) == 1:
            node["direct"].append(p)
        else:
            node["subs"].setdefault(p.ancestors[1], []).append(p)

    def link(p: Page) -> str:
        cur = ' aria-current="page"' if (p.slug == current_slug and p.dept == dept) else ""
        return (f'<li><a href="{BASE_URL}/{dept}/{p.rel_path}.html"{cur}>'
                f'{html.escape(p.meta.get("title", p.slug))}</a></li>')

    by_title = lambda x: x.meta.get("title", x.slug)
    home_cur = ' aria-current="page"' if current_group is None and current_slug is None else ""
    out = ['<nav class="doc-nav" aria-label="Section pages">',
           f'<a class="nav-home" href="{BASE_URL}/{dept}/"{home_cur}>'
           f'All {html.escape(DEPT_LABELS.get(dept, dept))}</a>']
    for p in sorted(roots, key=by_title):
        cur = ' aria-current="page"' if p.slug == current_slug else ""
        out.append(f'<a class="nav-home nav-home--sub" '
                   f'href="{BASE_URL}/{dept}/{p.rel_path}.html"{cur}>'
                   f'{html.escape(p.meta.get("title", p.slug))}</a>')
    for g in _order(groups):
        node = groups[g]
        count = len(node["direct"]) + sum(len(v) for v in node["subs"].values())
        opn = " open" if g == current_group else ""
        out.append(f'<details class="nav-group"{opn}>')
        out.append(f'<summary class="nav-summary"><span class="nav-label">'
                   f'{html.escape(_label(g))}</span>'
                   f'<span class="nav-count">{count}</span></summary>')
        out.append('<ul class="nav-list">')
        for p in sorted(node["direct"], key=by_title):
            out.append(link(p))
        for sub in sorted(node["subs"]):
            out.append(f'<li class="nav-sub"><span class="nav-sub-title">'
                       f'{html.escape(_label(sub))}</span><ul class="nav-sublist">')
            for p in sorted(node["subs"][sub], key=by_title):
                out.append(link(p))
            out.append('</ul></li>')
        out.append('</ul></details>')
    out.append('</nav>')
    return "\n".join(out)

def related_for(page: Page, pages: list[Page]) -> list[Page]:
    tags = set(page.meta.get("tags") or [])
    scored = [(len(tags & set(o.meta.get("tags") or [])), o.meta.get("last_modified", ""), o)
              for o in pages if o is not page]
    scored = [s for s in scored if s[0]]
    # Coerce the last_modified tiebreaker to str: PyYAML parses unquoted
    # `YYYY-MM-DD` as datetime.date but quoted ones stay str, and mixing the
    # two breaks the tuple comparison. ISO strings still sort chronologically.
    scored.sort(key=lambda t: (t[0], str(t[1])), reverse=True)
    return [o for _, _, o in scored[:5]]

def breadcrumbs_for(page: Page) -> list[dict]:
    crumbs = [{"label": "Home", "href": f"{BASE_URL}/"},
              {"label": DEPT_LABELS.get(page.dept, page.dept), "href": f"{BASE_URL}/{page.dept}/"}]
    acc = f"{BASE_URL}/{page.dept}"
    for seg in page.ancestors:
        acc += f"/{seg}"
        crumbs.append({"label": LABELS.get(seg, seg.replace("-", " ").title()), "href": acc + "/"})
    crumbs.append({"label": page.meta.get("title", page.slug), "href": ""})
    return crumbs

def _as_list(value) -> list:
    if not value:
        return []
    return value if isinstance(value, list) else [value]

def _json_ready(data):
    if isinstance(data, dict):
        return {k: _json_ready(v) for k, v in data.items() if v not in (None, "", [], {})}
    if isinstance(data, list):
        return [_json_ready(v) for v in data if v not in (None, "", [], {})]
    return str(data) if hasattr(data, "isoformat") else data

def _json_ld(data: dict) -> str:
    return json.dumps(_json_ready(data), ensure_ascii=True, separators=(",", ":"))

def _site_graph(canonical_url: str) -> dict:
    return {"@type": "WebSite", "name": "SU ITS Data & AI Knowledge Base",
            "url": f"{SITE_ORIGIN}{BASE_URL}/", "@id": f"{SITE_ORIGIN}{BASE_URL}/#website",
            "isPartOf": {"@type": "Organization", "name": "Syracuse University"},
            "potentialAction": {"@type": "ReadAction", "target": canonical_url}}

def _doc_json_ld(page: Page, ctx: dict) -> str:
    source_url = ctx.get("source_url")
    data = {"@context": "https://schema.org", "@type": "TechArticle",
            "headline": ctx.get("title"), "description": ctx.get("description"),
            "url": ctx.get("canonical_url"), "dateModified": ctx.get("last_modified"),
            "inLanguage": "en", "isPartOf": _site_graph(ctx.get("canonical_url")),
            "publisher": {"@type": "Organization", "name": "Syracuse University"},
            "about": _as_list(ctx.get("tags")),
            "audience": [{"@type": "Audience", "audienceType": a}
                         for a in _as_list(ctx.get("audience"))],
            "encoding": {"@type": "MediaObject", "encodingFormat": "text/markdown",
                         "contentUrl": f"{SITE_ORIGIN}{BASE_URL}/{page.dept}/{page.rel_path}.md"}}
    if source_url and source_url != "#":
        data["citation"] = source_url
    return _json_ld(data)

def _collection_json_ld(name: str, description: str, canonical_url: str, item_urls: list[str]) -> str:
    return _json_ld({"@context": "https://schema.org", "@type": "CollectionPage",
                     "name": name, "description": description, "url": canonical_url,
                     "inLanguage": "en", "isPartOf": _site_graph(canonical_url),
                     "publisher": {"@type": "Organization", "name": "Syracuse University"},
                     "mainEntity": {"@type": "ItemList",
                                    "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                                         "url": url}
                                                        for i, url in enumerate(item_urls)]}})

def render_html(page: Page, pages: list[Page], env: Environment, slug_index: dict) -> None:
    # In-corpus body links are authored relative (`./slug.md`) for a flat corpus;
    # wrapper-collapse nested the tree, so resolve by slug to the true emitted
    # location (root-absolute `.html`), and pin attachment refs to the dept tree.
    def md_link(m: re.Match) -> str:
        hit = slug_index.get(m.group(2).rstrip("/").rsplit("/", 1)[-1])
        tgt = f"{BASE_URL}/{hit[0]}/{hit[1]}" if hit else m.group(2)
        return f'{m.group(1)}{tgt}.html{m.group(3)}'
    body = _MD_LINK_RE.sub(md_link, page.html)
    body = _ATTACH_RE.sub(
        lambda m: f'{m.group(1)}{BASE_URL}/{page.dept}/{m.group(2)}{m.group(3)}', body)
    if not RELATED_RE.search(page.body_md):
        rel = related_for(page, pages)
        if rel:
            items = "".join(
                f'<li><a href="{BASE_URL}/{r.dept}/{r.rel_path}.html" class="wikilink">'
                f'{html.escape(r.meta.get("title", r.slug))}</a></li>' for r in rel)
            body += f'\n<h2 id="related">Related</h2>\n<ul>{items}</ul>'
            if page.toc:
                page.toc = page.toc.replace(
                    "</ul>", '<li><a href="#related">Related</a></li></ul>')
    ctx = {"title": page.slug, "description": "", "page_id": "", "last_modified": None,
           "tags": [], "source_url": "#", **page.meta}
    ctx.update(dept=page.dept, slug=page.slug, rel_md_path=page.rel_path + ".md", body=body,
               toc=page.toc, asset_v=ASSET_V, base_url=BASE_URL, github_url=GITHUB_URL,
               department_label=DEPT_LABELS.get(page.dept, page.dept),
               canonical_url=f"{SITE_ORIGIN}{BASE_URL}/{page.dept}/{page.rel_path}.html",
               source_path=f"raw/knowledge-bases/ITSAI/{page.meta.get('page_id', '')}",
               breadcrumbs=breadcrumbs_for(page),
               sidebar=build_sidebar(pages, page.dept,
                                     page.ancestors[0] if page.ancestors else None, page.slug))
    ctx["json_ld"] = _doc_json_ld(page, ctx)
    page.out_html.parent.mkdir(parents=True, exist_ok=True)
    page.out_html.write_text(env.get_template("docpage.html.jinja").render(**ctx),
                             encoding="utf-8")

def emit_md_mirror(page: Page) -> None:
    shutil.copyfile(page.src, page.out_md)

def _label(seg: str) -> str:
    return LABELS.get(seg, seg.replace("-", " ").title())

# First matching tag becomes a page's type chip on hub listings.
_TYPE_CHIPS = [("faq", "FAQ"), ("setup", "Setup"), ("how-to", "How-to"),
               ("example-use", "Example"), ("security", "Security"),
               ("policy", "Policy"), ("api", "API"), ("overview", "Overview")]

def _type_chip(tags: list | None) -> str:
    tset = set(tags or [])
    return next((label for t, label in _TYPE_CHIPS if t in tset), "")

def index_pages(pages: list[Page]) -> dict[tuple, dict]:
    """Map every directory containing pages → {pages, subdirs}.

    Key is (dept, segs-tuple); segs is the path below the dept (() = dept root).
    A directory is listed if it directly holds a page OR is an ancestor of one,
    so landing-card and breadcrumb targets all resolve to an emitted index.
    """
    dirs: dict[tuple, dict] = {}
    for p in pages:
        for depth in range(len(p.ancestors) + 1):
            node = dirs.setdefault((p.dept, tuple(p.ancestors[:depth])),
                                   {"pages": [], "subdirs": set()})
            if depth == len(p.ancestors):
                node["pages"].append(p)
            else:
                node["subdirs"].add(p.ancestors[depth])
    return dirs

def render_index(dept: str, segs: list[str], node: dict, pages: list[Page],
                 env: Environment) -> None:
    """Emit index.html (+ index.md siblings) for one directory, reusing the
    docpage template so breadcrumbs / sidebar / copy-button all keep working."""
    label = DEPT_LABELS.get(dept, dept) if not segs else _label(segs[-1])
    rel = "/".join(segs)
    key = segs[-1] if segs else dept
    intro = INDEX_INTROS.get(key, f"Browse the pages in {label}.")
    # Hub body: subsections as a compact card grid, pages as a rich list
    # (title + type chip + description + audience) — built from enriched meta.
    subs = sorted(node["subdirs"], key=lambda s: GROUP_ORDER.index(s)
                  if s in GROUP_ORDER else 99)
    ps = sorted(node["pages"], key=lambda x: x.meta.get("title", x.slug))

    def under(sub: str) -> int:
        pre = list(segs) + [sub]
        return sum(1 for p in pages if p.dept == dept and list(p.ancestors[:len(pre)]) == pre)

    body = []
    if subs:
        cards = []
        for s in subs:
            n = under(s)
            sdesc = INDEX_INTROS.get(s, "")
            cards.append(
                f'<a class="hub-card" href="./{s}/"><span class="hub-card-title">'
                f'{html.escape(_label(s))}</span>'
                + (f'<span class="hub-card-desc">{html.escape(sdesc)}</span>' if sdesc else "")
                + f'<span class="hub-card-foot"><span class="badge badge--accent">{n} '
                f'page{"s" if n != 1 else ""}</span>'
                f'<span class="hub-card-arrow" aria-hidden="true">&rarr;</span></span></a>')
        head = '<h2 class="hub-h">Browse by section</h2>' if ps else ""
        body.append(f'{head}<div class="hub-grid">{"".join(cards)}</div>')
    if ps:
        items = []
        for p in ps:
            chip = _type_chip(p.meta.get("tags"))
            desc = (p.meta.get("description") or "").strip()
            aud = p.meta.get("audience") or []
            items.append(
                f'<a class="hub-item" href="./{p.slug}.html"><span class="hub-item-head">'
                f'<span class="hub-item-title">{html.escape(p.meta.get("title", p.slug))}</span>'
                + (f'<span class="badge">{html.escape(chip)}</span>' if chip else "")
                + "</span>"
                + (f'<span class="hub-item-desc">{html.escape(desc)}</span>' if desc else "")
                + ('<span class="hub-item-aud">'
                   + "".join(f'<span class="hub-aud">{html.escape(a)}</span>' for a in aud)
                   + "</span>" if aud else "")
                + "</a>")
        head = '<h2 class="hub-h">Pages</h2>' if subs else ""
        body.append(f'{head}<div class="hub-list">{"".join(items)}</div>')
    total = sum(1 for p in pages if p.dept == dept and list(p.ancestors[:len(segs)]) == list(segs))
    hub_meta = (f'{total} page{"s" if total != 1 else ""}'
                + (f' · {len(subs)} section{"s" if len(subs) != 1 else ""}' if subs else ""))
    # Breadcrumbs: Home › Dept › …segs (last is current, empty href).
    crumbs = [{"label": "Home", "href": f"{BASE_URL}/"}]
    acc = f"{BASE_URL}/{dept}"
    crumbs.append({"label": DEPT_LABELS.get(dept, dept), "href": "" if not segs else acc + "/"})
    for i, seg in enumerate(segs):
        acc += f"/{seg}"
        crumbs.append({"label": _label(seg), "href": "" if i == len(segs) - 1 else acc + "/"})
    ctx = {"title": label, "description": intro, "page_id": "index", "last_modified": None,
           "tags": [], "source_url": "#", "dept": dept, "slug": "index",
           "rel_md_path": (rel + "/" if rel else "") + "index.md", "body": "\n".join(body),
           "toc": "", "is_hub": True, "hub_meta": hub_meta, "asset_v": ASSET_V,
           "base_url": BASE_URL, "github_url": GITHUB_URL,
           "department_label": DEPT_LABELS.get(dept, dept),
           "canonical_url": f"{SITE_ORIGIN}{BASE_URL}/{dept}/{rel + '/' if rel else ''}index.html",
           "source_path": f"knowledge-bases/ITSAI/{dept}/{rel}".rstrip("/"), "breadcrumbs": crumbs,
           "sidebar": build_sidebar(pages, dept, segs[0] if segs else None, None)}
    ctx["json_ld"] = _collection_json_ld(
        label, intro, ctx["canonical_url"],
        [f"{SITE_ORIGIN}{BASE_URL}/{p.dept}/{p.rel_path}.html" for p in ps],
    )
    out_dir = OUT.joinpath(dept, *segs)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        env.get_template("docpage.html.jinja").render(**ctx), encoding="utf-8")
    # .md mirror (for the copy/raw links). Also at `<dir>.md` so copy-markdown.js
    # — which maps the trailing-slash URL to `<dir>.md` — fetches a real file.
    md = "\n".join([f"# {label}", "", intro, ""]
                   + [f"- [{_label(s)}](./{s}/)" for s in sorted(node["subdirs"])]
                   + [f"- [{p.meta.get('title', p.slug)}](./{p.slug}.md)" for p in ps]) + "\n"
    (out_dir / "index.md").write_text(md, encoding="utf-8")
    if segs:
        OUT.joinpath(dept, *segs).with_suffix(".md").write_text(md, encoding="utf-8")

def _grouped(pages: list[Page]) -> dict:
    by_dept = {}
    for p in pages:
        grp = p.ancestors[0] if p.ancestors else "_root"
        by_dept.setdefault(p.dept, {}).setdefault(grp, []).append(p)
    return by_dept

def _order(groups) -> list[str]:
    return [g for g in GROUP_ORDER if g in groups] + [g for g in groups if g not in GROUP_ORDER]

_LLMS_EXTRA_KEYWORDS = {
    "understanding-claude-products-chat-code-and-api":
        "Claude Chat vs Claude Code vs Claude API, request access, premium seats, Anthropic Console.",
    "purchase-claude-code-and-claude-api-access":
        "buy or request Claude Code, Claude API credits, premium Claude seats, funding options.",
    "how-to-use-google-notebooklm":
        "NotebookLM study support, research assistant, source-grounded notebooks, audio overviews, "
        "flashcards, quizzes, course readings.",
    "mentorai-using-the-api":
        "mentorAI API, Clementine API, API key request, PowerShell examples, datasets, chat sessions, "
        "programmatic access.",
    "approved-tools-for-use-with-university-data":
        "approved AI tools, university data classification, FERPA, HIPAA, protected information.",
}

def _page_md_url(page: Page) -> str:
    return f"{SITE_ORIGIN}{BASE_URL}/{page.dept}/{page.rel_path}.md"

def _page_html_url(page: Page) -> str:
    return f"{SITE_ORIGIN}{BASE_URL}/{page.dept}/{page.rel_path}.html"

def _llms_desc(page: Page) -> str:
    parts = []
    desc = (page.meta.get("description") or "").strip()
    if desc:
        parts.append(desc)
    tags = _as_list(page.meta.get("tags"))
    if tags:
        parts.append("Topics: " + ", ".join(str(t) for t in tags))
    audience = _as_list(page.meta.get("audience"))
    if audience:
        parts.append("Audience: " + ", ".join(str(a) for a in audience))
    extra = _LLMS_EXTRA_KEYWORDS.get(page.slug)
    if extra:
        parts.append("Retrieval aliases: " + extra)
    return " ".join(parts) or f"{page.meta.get('title', page.slug)} overview"

def emit_llms_txt(pages: list[Page]) -> None:
    lines = ["# SU ITS Data & AI Knowledge Base", "",
             "> Public knowledge base for the ITS Data & AI department at Syracuse University,",
             "> sourced from Confluence. Start here for fast retrieval: choose the most relevant",
             "> Markdown URL below, fetch that `.md` page, and cite its `source_url` frontmatter.",
             "> Use `/llms-full.txt` only when a single full-corpus context file is needed.",
             "> This site is independent of the official Clementine product.", ""]
    for dept, groups in _grouped(pages).items():
        lines += [f"## {DEPT_LABELS.get(dept, dept)}", ""]
        for grp in _order(groups):
            if grp != "_root":
                lines.append(f"### {LABELS.get(grp, grp.title())}")
            for p in sorted(groups[grp], key=lambda x: x.slug):
                desc = _llms_desc(p)
                lines.append(f"- [{p.meta.get('title', p.slug)}](./{dept}/{p.rel_path}.md): {desc}")
            lines.append("")
    (OUT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")

def emit_llms_full_txt(pages: list[Page]) -> None:
    lines = ["# SU ITS Data & AI Knowledge Base - Full Markdown Corpus", "",
             "This file concatenates the public Markdown pages for agents that need a",
             "single context source. For normal question answering, fetch `/llms.txt`",
             "first and then fetch the one or two most relevant `.md` page URLs.", ""]
    for p in sorted(pages, key=lambda x: (x.dept, x.rel_path)):
        meta = {"title": p.meta.get("title", p.slug), "url": _page_html_url(p),
                "markdown_url": _page_md_url(p), "source_url": p.meta.get("source_url"),
                "page_id": p.meta.get("page_id"), "tags": _as_list(p.meta.get("tags")),
                "audience": _as_list(p.meta.get("audience")),
                "last_modified": p.meta.get("last_modified")}
        lines += ["---"]
        lines += [f"{k}: {json.dumps(_json_ready(v), ensure_ascii=True)}"
                  for k, v in _json_ready(meta).items()]
        lines += ["---", "", p.body_md.strip(), ""]
    (OUT / "llms-full.txt").write_text("\n".join(lines), encoding="utf-8")

def emit_ai_discovery_files() -> None:
    well_known = OUT / ".well-known"
    well_known.mkdir(parents=True, exist_ok=True)
    for name in ("llms.txt", "llms-full.txt"):
        src = OUT / name
        if src.exists():
            shutil.copyfile(src, well_known / name)

def emit_sitemap(pages: list[Page]) -> None:
    rows = [f"  <url><loc>{SITE_ORIGIN}{BASE_URL}/</loc></url>"]
    for p in pages:
        loc = html.escape(f"{SITE_ORIGIN}{BASE_URL}/{p.dept}/{p.rel_path}.html")
        lm = p.meta.get("last_modified")
        rows.append(f"  <url><loc>{loc}</loc>{f'<lastmod>{lm}</lastmod>' if lm else ''}</url>")
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    (OUT / "sitemap.xml").write_text(head + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8")

def emit_robots() -> None:
    lines = ["# SU ITS Data & AI Knowledge Base — agent access policy",
             "# This KB is intentionally open to AI retrieval agents.", ""]
    lines += [f"User-agent: {a}" for a in AGENTS]
    lines += ["Allow: /", "", "User-agent: *", "Allow: /", "",
              f"Sitemap: {SITE_ORIGIN}{BASE_URL}/sitemap.xml", ""]
    (OUT / "robots.txt").write_text("\n".join(lines), encoding="utf-8")

def emit_landing(pages: list[Page], env: Environment) -> None:
    groups = _grouped(pages).get("data-ai", {})
    cards = []
    for grp in GROUP_ORDER:
        if grp not in CARD_META:
            continue
        icon, title, tag, feat, desc, kinds = CARD_META[grp]
        n = len(groups.get(grp, []))
        cards.append({"slug": grp, "icon": icon, "title": title, "tag": tag, "featured": feat,
                      "desc": desc, "kinds": kinds, "count": f"{n} page{'s' if n != 1 else ''}"})
    canonical_url = f"{SITE_ORIGIN}{BASE_URL}/"
    section_urls = [f"{SITE_ORIGIN}{BASE_URL}/data-ai/{card['slug']}/" for card in cards]
    out = env.get_template("landing.html.jinja").render(
        base_url=BASE_URL, github_url=GITHUB_URL, dept="data-ai", cards=cards,
        asset_v=ASSET_V, canonical_url=canonical_url,
        json_ld=_collection_json_ld(
            "SU ITS Data & AI Knowledge Base",
            "Public knowledge base for Syracuse University's ITS Data & AI department.",
            canonical_url, section_urls))
    (OUT / "index.html").write_text(out, encoding="utf-8")
    lines = ["# SU ITS Data & AI Knowledge Base", "",
             "Public knowledge base for Syracuse University's ITS Data & AI department.",
             "Use this homepage mirror when an agent starts from the site root.",
             "",
             "## Retrieval entry points", "",
             "- [Fast retrieval index](./llms.txt)",
             "- [Full Markdown corpus](./llms-full.txt)",
             "- [Sitemap](./sitemap.xml)", "",
             "## Sections", ""]
    lines += [f"- [{card['title']}](./data-ai/{card['slug']}/): {card['desc']}"
              for card in cards]
    (OUT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def copy_assets() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        if (DESIGN / name).exists():
            shutil.copyfile(DESIGN / name, OUT / name)
    # Token colors only, scoped under .article-body; drop the bare `pre{}` and
    # `.highlight{bg}` base rules so they don't leak onto the navy block.
    defs = (ln for ln in _PYG.get_style_defs(".article-body .highlight").splitlines()
            if not ln.lstrip().startswith(("pre ", ".article-body .highlight {")))
    (OUT / "pygments.css").write_text("\n".join(defs), encoding="utf-8")
    if (DESIGN / "assets").exists():
        shutil.copytree(DESIGN / "assets", OUT / "assets", dirs_exist_ok=True)

_HREF_RE = re.compile(r'href="([^"#?]+)"')

def check_links() -> list[str]:
    """Verify every internal href under _site resolves to an emitted file.

    Resolves BASE_URL-prefixed and relative hrefs against the emitting file's
    directory; directory URLs (trailing slash) map to their index.html. Returns
    a sorted list of (source -> broken target) strings; empty means clean.
    """
    broken: list[str] = []
    for hf in sorted(OUT.rglob("*.html")):
        for href in _HREF_RE.findall(hf.read_text(encoding="utf-8")):
            if "://" in href or href.startswith("mailto:"):
                continue
            if href.startswith(BASE_URL + "/"):
                rel = href[len(BASE_URL) + 1:]
                target = OUT.joinpath(*rel.split("/"))
            elif href.startswith("/"):
                continue  # absolute non-BASE_URL (none expected); skip
            else:
                target = hf.parent.joinpath(*href.split("/"))
            if href.endswith("/") or target.is_dir():
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{hf.relative_to(OUT)} -> {href}")
    return sorted(broken)

def leak_guard(pages: list[Page]) -> None:
    """Fail the build if a page the exporter classified restricted is present.

    Defense in depth for the public-only invariant (ADR-0003). The authoritative
    gate is in the export tool (it alone knows Confluence read restrictions);
    this is a cheap second check keyed on the export's `.last-exclusions.jsonl`.
    That report is local-only (gitignored), so in CI — which renders committed
    content and never runs the export — the file is absent and this no-ops.
    """
    report = ROOT / "export-tool" / ".last-exclusions.jsonl"
    if not report.exists():
        return
    restricted: set[str] = set()
    for line in report.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("reason") in ("read-restricted", "access-check-failed"):
            pid = str(entry.get("page_id") or "")
            if pid:
                restricted.add(pid)
    leaked = sorted({str(p.meta.get("page_id") or "") for p in pages} & restricted)
    if leaked:
        raise SystemExit(
            f"leak-guard: {len(leaked)} restricted page(s) in site/content - "
            f"page_id(s) {leaked} (ADR-0003 public-only). Build aborted."
        )


def main() -> None:
    env = Environment(loader=FileSystemLoader(str(DESIGN)),
                      autoescape=select_autoescape(["html", "jinja"]))
    md = build_md()
    pages = load_corpus(md)
    leak_guard(pages)
    # Clean rebuild: drop stale rendered output so renamed/excluded pages don't
    # linger as orphans. Leave assets/ (OneDrive holds font handles); refreshed
    # in place by copy_assets().
    depts = {p.dept for p in pages}
    for dept in depts:
        if (OUT / dept).exists():
            shutil.rmtree(OUT / dept, onexc=lambda f, p, e: None)
    if (OUT / ".well-known").exists():
        shutil.rmtree(OUT / ".well-known", onexc=lambda f, p, e: None)
    for stale in ("llms.txt", "llms-full.txt", "sitemap.xml", "robots.txt", "index.html", "index.md"):
        (OUT / stale).unlink(missing_ok=True)
    copy_assets()
    # Cache-bust: hash the emitted assets so each change yields a new ?v=, which
    # bypasses GitHub Pages' 10-minute (max-age=600) browser cache on redeploy.
    global ASSET_V
    h = hashlib.sha1()
    for a in [*ASSETS, "pygments.css"]:
        if (OUT / a).exists():
            h.update((OUT / a).read_bytes())
    ASSET_V = h.hexdigest()[:8]
    # slug → (dept, rel_path) resolves in-corpus body links to their true nested
    # location regardless of the source link's authored relative path.
    slug_index = {p.slug: (p.dept, p.rel_path) for p in pages}
    for p in pages:
        render_html(p, pages, env, slug_index)
        emit_md_mirror(p)
    for dept in depts:  # copy attachments/ so body images + file links resolve
        if (CONTENT / dept / "attachments").is_dir():
            shutil.copytree(CONTENT / dept / "attachments", OUT / dept / "attachments",
                            dirs_exist_ok=True)
    dirs = index_pages(pages)
    for (dept, segs), node in dirs.items():
        render_index(dept, list(segs), node, pages, env)
    emit_llms_txt(pages)
    emit_llms_full_txt(pages)
    emit_ai_discovery_files()
    emit_sitemap(pages)
    emit_robots()
    emit_landing(pages, env)
    broken = check_links()
    print(f"Rendered {len(pages)} pages + {len(dirs)} index pages to {OUT}")
    if broken:
        print(f"WARNING: {len(broken)} broken internal link(s):")
        for b in broken:
            print(f"  {b}")

if __name__ == "__main__":
    main()
