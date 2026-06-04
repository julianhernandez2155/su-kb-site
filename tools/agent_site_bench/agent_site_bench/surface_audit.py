from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urljoin, urlparse

import yaml

from .config import SiteConfig
from .fetcher import FetchResult, Fetcher


MACHINE_PATHS = ("", "robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt")
MARKDOWN_AFFORDANCE_PATTERNS = (
    "copy markdown",
    "copy as markdown",
    "raw markdown",
    "download markdown",
    "view markdown",
    "copy-markdown",
    "data-copy-markdown",
)


@dataclass(frozen=True)
class SurfaceAuditResult:
    site_name: str
    start_url: str
    machine_root_url: str
    fetched: dict[str, dict]
    homepage_links: list[dict]
    llms_txt_links: list[str]
    llms_full_txt_links: list[str]
    markdown_twin_links: list[str]
    markdown_copy_affordances: list[str]
    markdown_frontmatter_source_urls: list[dict]
    json_ld_blocks: list[dict]
    broken_machine_surface_urls: list[dict]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class HomepageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict] = []
        self.json_ld_blocks: list[str] = []
        self._in_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() in {"a", "link"} and attr_map.get("href"):
            self.links.append({"tag": tag.lower(), "href": attr_map["href"], "attrs": attr_map})
        if tag.lower() == "script" and attr_map.get("type", "").lower() == "application/ld+json":
            self._in_json_ld = True
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_json_ld:
            self._in_json_ld = False
            self.json_ld_blocks.append("".join(self._json_ld_parts).strip())
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._json_ld_parts.append(data)


def audit_sites(sites: Iterable[SiteConfig], fetcher: Fetcher, max_discovered_fetches: int = 25) -> dict[str, dict]:
    return {
        site.name: audit_site(site, fetcher, max_discovered_fetches=max_discovered_fetches).to_dict()
        for site in sites
    }


def audit_site(site: SiteConfig, fetcher: Fetcher, max_discovered_fetches: int = 25) -> SurfaceAuditResult:
    fetched: dict[str, FetchResult] = {}
    machine_urls = _root_machine_urls(site)
    for label, url in machine_urls.items():
        fetched[label] = fetcher.fetch(url)

    homepage = fetched["homepage"]
    parser = HomepageParser()
    if homepage.text:
        parser.feed(homepage.text)

    homepage_links = [
        {**link, "absolute_url": urljoin(homepage.final_url or site.start_url, link["href"])}
        for link in parser.links
    ]
    json_ld_blocks = _parse_json_ld_blocks(parser.json_ld_blocks)
    llms_txt_links = _matching_links(homepage_links, "llms.txt")
    llms_full_txt_links = _matching_links(homepage_links, "llms-full.txt")
    markdown_copy_affordances = _detect_markdown_affordances(homepage.text, homepage_links)

    discovered_urls = _discover_machine_urls(site, fetched, homepage_links)
    markdown_twin_links = sorted(
        set(_markdown_links(homepage_links))
        | {url for url in discovered_urls if _looks_like_markdown_url(url)}
    )
    discovered_fetches: dict[str, FetchResult] = {}
    for url in discovered_urls[:max_discovered_fetches]:
        if url not in {result.url for result in fetched.values()}:
            discovered_fetches[url] = fetcher.fetch(url)

    markdown_frontmatter_source_urls = []
    for url, result in discovered_fetches.items():
        if _looks_like_markdown_url(url) and result.text:
            source_url = _frontmatter_source_url(result.text)
            if source_url:
                markdown_frontmatter_source_urls.append({"url": url, "source_url": source_url})

    fetched_records = {label: result.to_record(include_text=False) for label, result in fetched.items()}
    for url, result in discovered_fetches.items():
        fetched_records[url] = result.to_record(include_text=False)

    broken = []
    for label, result in fetched.items():
        if _is_broken(result):
            broken.append({"label": label, "url": result.url, "status_code": result.status_code, "error": result.error})
    for url, result in discovered_fetches.items():
        if _is_broken(result):
            broken.append({"label": "discovered", "url": url, "status_code": result.status_code, "error": result.error})

    notes = []
    if not llms_txt_links and _is_broken(fetched["llms.txt"]):
        notes.append("No homepage llms.txt link found and root llms.txt was not reachable.")
    if not markdown_twin_links:
        notes.append("No homepage links to .md twins detected.")
    if not markdown_copy_affordances:
        notes.append("No obvious markdown/copy affordance detected on the homepage.")
    if not json_ld_blocks:
        notes.append("No JSON-LD block detected in homepage HTML.")

    return SurfaceAuditResult(
        site_name=site.name,
        start_url=site.start_url,
        machine_root_url=site.resolved_machine_root_url,
        fetched=fetched_records,
        homepage_links=homepage_links,
        llms_txt_links=llms_txt_links,
        llms_full_txt_links=llms_full_txt_links,
        markdown_twin_links=markdown_twin_links,
        markdown_copy_affordances=markdown_copy_affordances,
        markdown_frontmatter_source_urls=markdown_frontmatter_source_urls,
        json_ld_blocks=json_ld_blocks,
        broken_machine_surface_urls=broken,
        notes=notes,
    )


def _root_machine_urls(site: SiteConfig) -> dict[str, str]:
    root = site.resolved_machine_root_url
    return {label or "homepage": urljoin(root, label) for label in MACHINE_PATHS}


def _matching_links(links: list[dict], suffix: str) -> list[str]:
    return sorted(
        {
            link["absolute_url"]
            for link in links
            if urlparse(link["absolute_url"]).path.lower().endswith(f"/{suffix}")
            or urlparse(link["absolute_url"]).path.lower().endswith(suffix)
        }
    )


def _markdown_links(links: list[dict]) -> list[str]:
    return sorted({link["absolute_url"] for link in links if _looks_like_markdown_url(link["absolute_url"])})


def _looks_like_markdown_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".md")


def _detect_markdown_affordances(homepage_text: str, links: list[dict]) -> list[str]:
    found: set[str] = set()
    lowered = homepage_text.lower()
    for pattern in MARKDOWN_AFFORDANCE_PATTERNS:
        if pattern in lowered:
            found.add(pattern)
    for link in links:
        attrs = " ".join(str(value).lower() for value in link.get("attrs", {}).values())
        if ".md" in link["absolute_url"].lower() or "markdown" in attrs or "copy" in attrs:
            found.add(f"link:{link['absolute_url']}")
    return sorted(found)


def _discover_machine_urls(
    site: SiteConfig,
    fetched: dict[str, FetchResult],
    homepage_links: list[dict],
) -> list[str]:
    urls: set[str] = set()
    for link in homepage_links:
        absolute = link["absolute_url"]
        lowered_path = urlparse(absolute).path.lower()
        if lowered_path.endswith((".md", "/llms.txt", "/llms-full.txt")):
            urls.add(absolute)

    for label in ("sitemap.xml", "llms.txt", "llms-full.txt", "robots.txt"):
        result = fetched.get(label)
        if not result or not result.text:
            continue
        for url in _urls_from_text(result.text):
            if _looks_like_machine_url(url):
                urls.add(urljoin(site.resolved_machine_root_url, url))
        for url in _markdown_links_from_text(result.text):
            urls.add(urljoin(result.final_url or site.resolved_machine_root_url, url))
        if label == "sitemap.xml":
            urls.update(url for url in _urls_from_sitemap(result.text) if _looks_like_machine_url(url))

    return sorted(urls)


def _urls_from_text(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>'\")]+|/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", text)


def _markdown_links_from_text(text: str) -> list[str]:
    links = re.findall(r"\]\(([^)]+?\.md)(?:#[^)]+)?\)", text)
    links.extend(re.findall(r"href=[\"']([^\"']+?\.md)(?:#[^\"']+)?[\"']", text, flags=re.IGNORECASE))
    return links


def _urls_from_sitemap(text: str) -> list[str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    urls = []
    for element in root.iter():
        if element.tag.lower().endswith("loc") and element.text:
            urls.append(element.text.strip())
    return urls


def _looks_like_machine_url(url: str) -> bool:
    lowered_path = urlparse(url).path.lower()
    return lowered_path.endswith((".md", "/llms.txt", "/llms-full.txt", "/sitemap.xml", "/robots.txt"))


def _frontmatter_source_url(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    source_url = data.get("source_url")
    return str(source_url) if source_url else None


def _parse_json_ld_blocks(blocks: list[str]) -> list[dict]:
    parsed = []
    for index, block in enumerate(blocks):
        try:
            value = json.loads(block)
            json_type = value.get("@type") if isinstance(value, dict) else None
            parsed.append({"index": index, "valid_json": True, "type": json_type, "raw_preview": block[:500]})
        except json.JSONDecodeError as exc:
            parsed.append({"index": index, "valid_json": False, "error": str(exc), "raw_preview": block[:500]})
    return parsed


def _is_broken(result: FetchResult) -> bool:
    return bool(result.error) or result.status_code is None or result.status_code >= 400
