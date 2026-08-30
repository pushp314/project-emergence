import asyncio
import logging
import base64
from typing import Any, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)

class PlaywrightBrowserTool(Tool):
    def __init__(self, headless: bool = True):
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Interact with the web using a real browser. Supports navigation, clicking, typing, extracting DOM, and capturing screenshots."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["navigate", "click", "type", "screenshot", "get_dom", "evaluate_js", "close"],
                    "description": "The browser operation to perform"
                },
                "url": {"type": "string", "description": "URL to navigate to (for 'navigate' operation)"},
                "selector": {"type": "string", "description": "CSS selector (for 'click', 'type' operations)"},
                "text": {"type": "string", "description": "Text to type (for 'type' operation)"},
                "script": {"type": "string", "description": "JavaScript to evaluate (for 'evaluate_js' operation)"},
            },
            "required": ["operation"]
        }

    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE

    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.MEDIUM

    @property
    def enabled(self) -> bool:
        return True

    async def _ensure_browser(self):
        if self._page is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
            self._context = await self._browser.new_context(viewport={"width": 1280, "height": 720})
            self._page = await self._context.new_page()

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        operation = arguments.get("operation")
        
        async with self._lock:
            try:
                if operation != "close":
                    await self._ensure_browser()
                
                if operation == "navigate":
                    url = arguments.get("url")
                    if not url:
                        return {"error": "Missing 'url' argument for navigate operation."}
                    await self._page.goto(url, wait_until="networkidle")
                    return {"success": True, "title": await self._page.title(), "url": self._page.url}
                
                elif operation == "click":
                    selector = arguments.get("selector")
                    if not selector:
                        return {"error": "Missing 'selector' argument for click operation."}
                    await self._page.click(selector)
                    await self._page.wait_for_load_state("networkidle")
                    return {"success": True, "url": self._page.url}
                
                elif operation == "type":
                    selector = arguments.get("selector")
                    text = arguments.get("text", "")
                    if not selector:
                        return {"error": "Missing 'selector' argument for type operation."}
                    await self._page.fill(selector, text)
                    return {"success": True}
                
                elif operation == "screenshot":
                    screenshot_bytes = await self._page.screenshot()
                    b64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                    return {"success": True, "image_base64": b64_image}
                
                elif operation == "get_dom":
                    html = await self._page.content()
                    return {"success": True, "dom": html}
                    
                elif operation == "evaluate_js":
                    script = arguments.get("script")
                    if not script:
                        return {"error": "Missing 'script' argument for evaluate_js operation."}
                    result = await self._page.evaluate(script)
                    return {"success": True, "result": result}
                    
                elif operation == "close":
                    if self._browser:
                        await self._browser.close()
                    if self._playwright:
                        await self._playwright.stop()
                    self._page = None
                    self._context = None
                    self._browser = None
                    self._playwright = None
                    return {"success": True}
                else:
                    return {"error": f"Unknown operation: {operation}"}
            except Exception as e:
                logger.error(f"Browser operation failed: {e}")
                return {"error": str(e)}
