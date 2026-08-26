from __future__ import annotations

import asyncio
import logging
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

from app.browser.extractor import ContentExtractor, ContentResult, Link

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    url: str
    method: str
    status: int
    timestamp: str
    title: str = ""


class BrowserSession:
    """Manages aiohttp sessions for web browsing with content extraction."""

    def __init__(
        self,
        timeout: int = 30,
        max_response_size: int = 1024 * 1024,
        user_agent: str = "AI-Sandbox/1.0",
        blocked_domains: Optional[List[str]] = None,
    ):
        self._timeout = timeout
        self._max_response_size = max_response_size
        self._user_agent = user_agent
        self._blocked_domains = blocked_domains or [
            "localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254",
            "metadata.google.internal", "metadata.azure.com",
        ]
        self._session: Optional[aiohttp.ClientSession] = None
        self._cookies: Optional[aiohttp.CookieJar] = aiohttp.CookieJar()
        self._extractor = ContentExtractor()
        self._history: List[HistoryEntry] = []

    @property
    def history(self) -> List[HistoryEntry]:
        return list(self._history)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self._user_agent},
                cookie_jar=self._cookies,
            )
        return self._session

    def _check_domain(self, url: str) -> Optional[str]:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            for blocked in self._blocked_domains:
                if blocked in domain:
                    return f"Blocked domain: {blocked}"
        except Exception as e:
            return f"Invalid URL: {e}"
        return None

    def _record(self, url: str, method: str, status: int, title: str = "") -> None:
        entry = HistoryEntry(
            url=url,
            method=method,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            title=title,
        )
        self._history.append(entry)

    async def get(self, url: str) -> Dict[str, Any]:
        error = self._check_domain(url)
        if error:
            return {"error": error, "url": url}

        session = await self._ensure_session()
        try:
            async with session.get(url) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "text/" not in content_type and "application/json" not in content_type:
                    self._record(url, "GET", resp.status)
                    return {
                        "error": f"Unsupported content type: {content_type}",
                        "url": url,
                        "status": resp.status,
                    }
                text = await resp.text()
                if len(text) > self._max_response_size:
                    text = text[: self._max_response_size] + "... [truncated]"
                result = self._extractor.extract(text)
                self._record(url, "GET", resp.status, title=result.title)
                return {
                    "url": url,
                    "status": resp.status,
                    "content_type": content_type,
                    "text": text,
                    "title": result.title,
                }
        except asyncio.TimeoutError:
            return {"error": f"Request timed out after {self._timeout}s", "url": url}
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {e}", "url": url}

    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error = self._check_domain(url)
        if error:
            return {"error": error, "url": url}

        session = await self._ensure_session()
        try:
            async with session.post(url, data=data) as resp:
                content_type = resp.headers.get("Content-Type", "")
                text = await resp.text()
                if len(text) > self._max_response_size:
                    text = text[: self._max_response_size] + "... [truncated]"
                self._record(url, "POST", resp.status)
                return {
                    "url": url,
                    "status": resp.status,
                    "content_type": content_type,
                    "text": text,
                }
        except asyncio.TimeoutError:
            return {"error": f"Request timed out after {self._timeout}s", "url": url}
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {e}", "url": url}

    def extract_content(self, html: str) -> ContentResult:
        return self._extractor.extract(html)

    async def get_links(self, url: str) -> List[Link]:
        error = self._check_domain(url)
        if error:
            return []

        session = await self._ensure_session()
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                result = self._extractor.extract(html)
                self._record(url, "GET", resp.status, title=result.title)
                return result.links
        except Exception as e:
            logger.warning("get_links failed for %s: %s", url, e)
            return []

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded}"

        session = await self._ensure_session()
        try:
            async with session.get(search_url) as resp:
                html = await resp.text()
            self._record(search_url, "GET", resp.status)

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            results: List[Dict[str, str]] = []

            for snippet in soup.find_all("a", class_="result__snippet")[:max_results]:
                parent = snippet.find_parent("a", class_="result__snippet")
                title_el = snippet.find_previous("a", class_="result__url")
                text = snippet.get_text(strip=True)
                link = parent.get("href", "") if parent else ""
                title = title_el.get_text(strip=True) if title_el else ""
                if text and link:
                    results.append({"title": title, "snippet": text, "url": link})

            if not results:
                for link in soup.find_all("a", class_="result__url")[:max_results]:
                    text = link.get_text(strip=True)
                    href = link.get("href", "")
                    if text and href:
                        results.append({"title": text, "snippet": "", "url": href})

            return results[:max_results]
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query, e)
            return []

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
