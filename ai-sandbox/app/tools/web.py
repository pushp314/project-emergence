from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class WebTool(Tool):
    def __init__(
        self,
        timeout: int = 30,
        max_response_size: int = 1024 * 1024,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        user_agent: str = "AI-Sandbox/1.0"
    ):
        self._timeout = timeout
        self._max_response_size = max_response_size
        self._allowed_domains = allowed_domains
        self._blocked_domains = blocked_domains or [
            "localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254",
            "metadata.google.internal", "metadata.azure.com"
        ]
        self._user_agent = user_agent
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def name(self) -> str:
        return "web"
    
    @property
    def description(self) -> str:
        return "Fetch web pages, search the web, and extract content from URLs."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["fetch", "search", "extract"],
                    "description": "Operation to perform"
                },
                "url": {
                    "type": "string",
                    "description": "URL to fetch (for fetch/extract operations)"
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for search operation)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum search results (default: 10)",
                    "default": 10
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for extract operation"
                }
            },
            "required": ["operation"]
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.NETWORK
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.MEDIUM
    
    @property
    def enabled(self) -> bool:
        return True
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"User-Agent": self._user_agent}
            )
        return self._session
    
    def _is_domain_allowed(self, url: str) -> tuple[bool, str]:
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            for blocked in self._blocked_domains:
                if blocked in domain:
                    return False, f"Blocked domain: {blocked}"
            
            if self._allowed_domains:
                allowed = False
                for allowed_domain in self._allowed_domains:
                    if allowed_domain in domain:
                        allowed = True
                        break
                if not allowed:
                    return False, f"Domain not in allowed list: {self._allowed_domains}"
            
            return True, ""
        except Exception as e:
            return False, f"Invalid URL: {e}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        operation = arguments.get("operation", "").lower()
        
        if operation == "fetch":
            url = arguments.get("url", "")
            if not url:
                return {"error": "Missing URL for fetch operation"}
            return await self._fetch(url)
        
        elif operation == "search":
            query = arguments.get("query", "")
            if not query:
                return {"error": "Missing query for search operation"}
            max_results = arguments.get("max_results", 10)
            return await self._search(query, max_results)
        
        elif operation == "extract":
            url = arguments.get("url", "")
            selector = arguments.get("selector", "")
            if not url:
                return {"error": "Missing URL for extract operation"}
            return await self._extract(url, selector)
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    async def _fetch(self, url: str) -> Dict[str, Any]:
        allowed, reason = self._is_domain_allowed(url)
        if not allowed:
            return {"error": reason, "url": url}
        
        session = await self._ensure_session()
        
        try:
            async with session.get(url) as response:
                content_type = response.headers.get("Content-Type", "")
                
                if "text/" not in content_type and "application/json" not in content_type:
                    return {
                        "error": f"Unsupported content type: {content_type}",
                        "url": url,
                        "status": response.status
                    }
                
                content = await response.text()
                
                if len(content) > self._max_response_size:
                    content = content[:self._max_response_size] + "... [truncated]"
                
                return {
                    "url": url,
                    "status": response.status,
                    "content_type": content_type,
                    "content": content,
                    "headers": dict(response.headers)
                }
                
        except asyncio.TimeoutError:
            return {"error": f"Request timed out after {self._timeout}s", "url": url}
        except aiohttp.ClientError as e:
            return {"error": f"Request failed: {e}", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}
    
    async def _search(self, query: str, max_results: int) -> Dict[str, Any]:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        session = await self._ensure_session()
        
        try:
            async with session.get(search_url) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, "html.parser")
            results = []
            
            for result in soup.find_all("a", class_="result__snippet")[:max_results]:
                title_elem = result.find_previous("a", class_="result__url")
                link_elem = result.find_parent("a", class_="result__snippet")
                
                text = result.get_text(strip=True)
                link = link_elem.get("href", "") if link_elem else ""
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if text and link:
                    results.append({
                        "title": title,
                        "snippet": text,
                        "url": link
                    })
            
            if not results:
                for link in soup.find_all("a", class_="result__url")[:max_results]:
                    text = link.get_text(strip=True)
                    url = link.get("href", "")
                    if text and url:
                        results.append({
                            "title": text,
                            "snippet": "",
                            "url": url
                        })
            
            return {
                "query": query,
                "results": results[:max_results],
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Search failed: {e}", "query": query, "results": []}
    
    async def _extract(self, url: str, selector: str = "") -> Dict[str, Any]:
        fetch_result = await self._fetch(url)
        
        if "error" in fetch_result:
            return fetch_result
        
        content = fetch_result.get("content", "")
        
        try:
            soup = BeautifulSoup(content, "html.parser")
            
            if selector:
                elements = soup.select(selector)
                extracted = [elem.get_text(strip=True) for elem in elements]
            else:
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                extracted = [soup.get_text(separator="\n", strip=True)]
            
            return {
                "url": url,
                "selector": selector,
                "extracted": extracted
            }
            
        except Exception as e:
            return {"error": f"Extraction failed: {e}", "url": url}
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()