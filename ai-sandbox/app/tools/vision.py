from typing import Any, Dict
import asyncio
import base64
import os
import subprocess
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool

class ScreenshotTool(Tool):
    @property
    def name(self) -> str:
        return "screenshot"
    
    @property
    def description(self) -> str:
        return "Take a screenshot of the user's screen. Returns the image so you can visually analyze the current state of the computer, look for visual bugs, or read text from the screen."
    
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
        import tempfile
        display = arguments.get("display", 0)
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        try:
            # -x prevents the sound, -D selects the display (macos specific)
            proc = await asyncio.create_subprocess_exec(
                "screencapture", "-x", "-D", str(display + 1), temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return f"Screenshot failed: {stderr.decode()}"
            
            with open(temp_path, "rb") as f:
                image_data = f.read()
                
            base64_img = base64.b64encode(image_data).decode("utf-8")
            return {
                "text": "Screenshot captured successfully.",
                "image_base64": base64_img
            }
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
