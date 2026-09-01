from typing import Any, Dict
import asyncio
import base64
import os
import pathlib
import time
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool

class ScreenshotTool(Tool):
    def __init__(self, artifacts_dir: str = "./data/artifacts/screenshots"):
        self.artifacts_dir = pathlib.Path(artifacts_dir)
        try:
            self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    @property
    def name(self) -> str:
        return "screenshot"
    
    @property
    def description(self) -> str:
        return "Take a screenshot of the user's macOS screen to visually inspect open apps, windows, code, UI, or errors."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "display": {
                    "type": "integer",
                    "description": "Display index to capture (default 0 for main screen)"
                }
            }
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.READ
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.LOW
    
    @property
    def enabled(self) -> bool:
        return True
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        display = arguments.get("display", 0)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        screenshot_file = self.artifacts_dir / f"screen_{timestamp}.png"
        
        try:
            # -x prevents sound, -D selects display (macOS specific)
            proc = await asyncio.create_subprocess_exec(
                "screencapture", "-x", "-D", str(display + 1), str(screenshot_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0 or not screenshot_file.exists():
                return {
                    "success": False,
                    "error": f"Screenshot capture failed: {stderr.decode()}"
                }
            
            with open(screenshot_file, "rb") as f:
                image_data = f.read()
                
            base64_img = base64.b64encode(image_data).decode("utf-8")
            file_size_kb = len(image_data) / 1024
            
            return {
                "success": True,
                "text": f"Mac screen captured ({file_size_kb:.1f} KB).",
                "file_path": str(screenshot_file.resolve()),
                "image_base64": base64_img,
                "timestamp": timestamp
            }
        except Exception as e:
            return {"success": False, "error": f"Error taking screenshot: {str(e)}"}
