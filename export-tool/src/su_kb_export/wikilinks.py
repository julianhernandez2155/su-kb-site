"""<ac:link> resolution — converts Confluence page references to GFM links.

ADR-0002: emit standard GFM relative links `[alias](./<slug>.md)` for in-corpus
pages (was Obsidian `[[<page-id> - <title>]]`). Out-of-corpus refs degrade to a
real external link `[title](source_url)` rather than emit a broken link.

Images / attachments emit standard markdown `![alt](./attachments/<id>/<file>)`
(was Obsidian `![[...]]` embeds with a `|<size>` width suffix).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus

from .frontmatter import slugify


# Public host every degraded link points back to.
PUBLIC_HOST = "https://answers.atlassian.syr.edu"


@dataclass
class CorpusIndex:
    """Maps page identifiers we know about to their canonical link target."""

    # page_id -> (title, space_key, source_url)
    pages_by_id: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    # (space_key, title) -> page_id
    pages_by_title: dict[tuple[str, str], str] = field(default_factory=dict)

    def register(self, page_id: str, title: str, space_key: str, source_url: str) -> None:
        self.pages_by_id[page_id] = (title, space_key, source_url)
        self.pages_by_title[(space_key, title)] = page_id
        # Also register under empty-space-key so title-only lookups work
        self.pages_by_title[("", title)] = page_id


class DefaultLinkResolver:
    """LinkResolver impl used by macros + walker."""

    def __init__(
        self,
        corpus: CorpusIndex,
        current_space_key: str,
        current_page_id: str,
        attachments_subpath: str = "attachments",
    ) -> None:
        self.corpus = corpus
        self.current_space_key = current_space_key
        self.current_page_id = current_page_id
        self.attachments_subpath = attachments_subpath

    def _gfm_link(self, page_id: str, alias: str | None = None) -> str:
        """`[alias-or-title](./<slug>.md)` — relative GFM link (ADR-0002)."""
        title, _, _ = self.corpus.pages_by_id[page_id]
        text = alias or title
        return f"[{text}](./{slugify(title)}.md)"

    def resolve_page_link(
        self,
        content_title: str | None,
        space_key: str | None,
        page_id: str | None,
        alias: str | None = None,
    ) -> str:
        # `alias` is the human-facing display text from an <ac:link-body>, when
        # present (e.g. `[See the FAQ](./claude-faq.md)`).
        # 1. If we know the page_id outright, prefer that.
        if page_id and page_id in self.corpus.pages_by_id:
            return self._gfm_link(page_id, alias)

        # 2. Look up by (space_key, title) — prefer current space, then provided, then global.
        if content_title:
            for sk in (self.current_space_key, space_key or "", ""):
                if sk is None:
                    continue
                pid = self.corpus.pages_by_title.get((sk, content_title))
                if pid:
                    return self._gfm_link(pid, alias)

        # 3. Out of corpus — degrade to a real external link, not a placeholder.
        # We don't know the target page_id without an API call (= per-link
        # cost), so the source_url is a Confluence search URL scoped to the
        # originating space + title. This always loads somewhere useful while
        # avoiding an N+1 API round-trip during conversion.
        if content_title:
            target_space = space_key or self.current_space_key
            params = f"text={quote_plus(content_title)}"
            if target_space:
                params += f"&spaceKey={quote_plus(target_space)}"
            return f"[{alias or content_title}]({PUBLIC_HOST}/wiki/search?{params})"
        return f"[link]({PUBLIC_HOST}/wiki)"

    def resolve_attachment(self, page_id: str, filename: str) -> str:
        return f"./{self.attachments_subpath}/{page_id}/{filename}"
