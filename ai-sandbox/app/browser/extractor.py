from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Link:
    text: str
    href: str


@dataclass
class CodeBlock:
    language: str
    text: str


@dataclass
class ContentResult:
    text: str
    title: str = ""
    headings: List[Heading] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    tables: List[List[Dict[str, str]]] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)


class ContentExtractor:
    """Extract structured content from HTML using BeautifulSoup."""

    def __init__(self, strip_tags: Optional[List[str]] = None):
        self._strip_tags = strip_tags or [
            "script", "style", "nav", "footer", "header",
            "noscript", "iframe", "svg",
        ]

    def extract(self, html: str) -> ContentResult:
        soup = BeautifulSoup(html, "html.parser")
        result = ContentResult(text="")
        result.title = self._extract_title(soup)
        result.meta = self._extract_meta(soup)
        result.headings = self._extract_headings(soup)
        result.links = self._extract_links(soup)
        result.code_blocks = self._extract_code_blocks(soup)
        result.tables = self._extract_tables(soup)
        result.text = self._extract_text(soup)
        return result

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return self._extract_text(soup)

    def _strip_noise(self, soup: BeautifulSoup) -> None:
        for tag_name in self._strip_tags:
            for el in soup.find_all(tag_name):
                el.decompose()

    def _extract_text(self, soup: BeautifulSoup) -> str:
        working = BeautifulSoup(str(soup), "html.parser")
        self._strip_noise(working)
        raw = working.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return "\n".join(lines)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def _extract_meta(self, soup: BeautifulSoup) -> Dict[str, str]:
        meta: Dict[str, str] = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property") or ""
            content = tag.get("content") or ""
            if name and content:
                meta[name] = content
        return meta

    def _extract_headings(self, soup: BeautifulSoup) -> List[Heading]:
        headings: List[Heading] = []
        for tag in soup.find_all(re.compile(r"^h[1-6]$")):
            level = int(tag.name[1])
            text = tag.get_text(strip=True)
            if text:
                headings.append(Heading(level=level, text=text))
        return headings

    def _extract_links(self, soup: BeautifulSoup) -> List[Link]:
        links: List[Link] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            if href and href not in seen:
                seen.add(href)
                links.append(Link(text=text, href=href))
        return links

    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[CodeBlock]:
        blocks: List[CodeBlock] = []
        for pre in soup.find_all("pre"):
            code_tag = pre.find("code")
            el = code_tag if code_tag else pre
            language = ""
            classes = el.get("class", [])
            for cls in classes:
                if cls.startswith("language-") or cls.startswith("lang-"):
                    language = cls.split("-", 1)[1]
                    break
            text = el.get_text()
            if text.strip():
                blocks.append(CodeBlock(language=language, text=text))
        return blocks

    def _extract_tables(self, soup: BeautifulSoup) -> List[List[Dict[str, str]]]:
        tables: List[List[Dict[str, str]]] = []
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            headers: List[str] = []
            for th in rows[0].find_all(["th", "td"]):
                headers.append(th.get_text(strip=True))
            data_rows: List[Dict[str, str]] = []
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                row_data: Dict[str, str] = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    row_data[key] = cell.get_text(strip=True)
                if row_data:
                    data_rows.append(row_data)
            tables.append(data_rows)
        return tables
