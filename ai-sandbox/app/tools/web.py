from __future__ import annotations

import asyncio
import logging
import urllib.parse
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, Playwright

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class WebTool(Tool):
    def __init__(
        self,
        timeout: int = 30000,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        user_agent: str = "AI-Sandbox/1.0"
    ):
        self._timeout = timeout
        self._allowed_domains = allowed_domains
        self._blocked_domains = blocked_domains or [
            "localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254",
            "metadata.google.internal", "metadata.azure.com"
        ]
        self._user_agent = user_agent
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()
    
    @property
    def name(self) -> str:
        return "web"
    
    @property
    def description(self) -> str:
        return "Full browser autonomy: navigate, click, type, search, and extract accessibility trees using Playwright."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "extract_a11y_tree", "extract_text", "search", "extract_screenshot"],
                    "description": "Operation to perform"
                },
                "url": {
                    "type": "string",
                    "description": "URL to navigate to or search"
                },
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for click, type, or extract operations"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type"
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
    
    async def _ensure_browser(self) -> Page:
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(headless=True)
        if self._page is None:
            self._page = await self._browser.new_page(user_agent=self._user_agent)
            self._page.set_default_timeout(self._timeout)
        return self._page
    
    def _is_domain_allowed(self, url: str) -> tuple[bool, str]:
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                return False, "Invalid URL"
            
            if self._allowed_domains:
                if not any(hostname.endswith(d) for d in self._allowed_domains):
                    return False, f"Domain {hostname} not in allowed list"
            
            if self._blocked_domains:
                if any(hostname == d or hostname.endswith(f".{d}") for d in self._blocked_domains):
                    return False, f"Domain {hostname} is blocked"
            
            return True, ""
        except Exception as e:
            return False, f"URL parse error: {str(e)}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        operation = arguments.get("operation")
        if not operation:
            raise ValueError("Missing 'operation' argument")
        
        async with self._lock:
            page = await self._ensure_browser()
            
            if operation == "navigate":
                url = arguments.get("url")
                if not url:
                    raise ValueError("navigate operation requires 'url'")
                if not url.startswith("http"):
                    url = "https://" + url
                
                allowed, reason = self._is_domain_allowed(url)
                if not allowed:
                    raise PermissionError(f"Navigation blocked: {reason}")
                
                await page.goto(url, wait_until="domcontentloaded")
                return {"status": "success", "url": page.url, "title": await page.title()}
            
            elif operation == "search":
                query = arguments.get("query")
                if not query:
                    raise ValueError("search operation requires 'query'")
                
                search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                await page.goto(search_url, wait_until="domcontentloaded")
                
                results = []
                elements = await page.query_selector_all(".result__body")
                for el in elements[:10]:
                    title_el = await el.query_selector(".result__title")
                    link_el = await el.query_selector(".result__url")
                    snippet_el = await el.query_selector(".result__snippet")
                    if title_el and link_el and snippet_el:
                        results.append({
                            "title": await title_el.inner_text(),
                            "url": await link_el.inner_text(),
                            "snippet": await snippet_el.inner_text()
                        })
                
                return {"status": "success", "results": results}
            
            elif operation == "click":
                selector = arguments.get("selector")
                if not selector:
                    raise ValueError("click operation requires 'selector'")
                await page.click(selector)
                await page.wait_for_load_state("domcontentloaded")
                return {"status": "success", "url": page.url, "title": await page.title()}
            
            elif operation == "type":
                selector = arguments.get("selector")
                text = arguments.get("text")
                if not selector or not text:
                    raise ValueError("type operation requires 'selector' and 'text'")
                await page.fill(selector, text)
                return {"status": "success"}
            
            elif operation == "extract_a11y_tree":
                # Playwright's accessibility snapshot provides a great tree representation of the DOM
                snapshot = await page.accessibility.snapshot()
                return {"status": "success", "a11y_tree": snapshot}
            
            elif operation == "extract_text":
                selector = arguments.get("selector", "body")
                element = await page.query_selector(selector)
                if not element:
                    raise ValueError(f"Selector '{selector}' not found")
                text = await element.inner_text()
                return {"status": "success", "text": text}
            
            elif operation == "extract_screenshot":
                import base64
                screenshot_bytes = await page.screenshot(type="png")
                b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                return {"status": "success", "image_base64": b64}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
    
    async def cleanup(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None