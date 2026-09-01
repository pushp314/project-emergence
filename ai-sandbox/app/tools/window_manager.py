from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Optional
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool

logger = logging.getLogger(__name__)


class MacWindowManagerTool(Tool):
    """Manage macOS active windows, applications, and system controls (volume, frontmost apps)."""

    @property
    def name(self) -> str:
        return "window_manager"

    @property
    def description(self) -> str:
        return "Control macOS GUI applications, query active open windows/apps, switch focus, adjust system volume, or close apps gracefully."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_apps", "focus_app", "quit_app", "set_volume", "get_volume"],
                    "description": "Action to perform on macOS GUI"
                },
                "app_name": {
                    "type": "string",
                    "description": "Name of the application (e.g. 'Brave Browser', 'Finder', 'Visual Studio Code')"
                },
                "volume_level": {
                    "type": "integer",
                    "description": "Volume percentage from 0 to 100 (for 'set_volume')"
                }
            },
            "required": ["action"]
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

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        action = arguments.get("action", "list_apps")
        app_name = arguments.get("app_name", "")
        volume_level = arguments.get("volume_level")

        try:
            if action == "list_apps":
                script = 'tell application "System Events" to get name of every process whose background only is false'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    return {"success": False, "error": stderr.decode()}
                
                apps = [a.strip() for a in stdout.decode().strip().split(", ")]
                return {"success": True, "active_gui_apps": apps, "count": len(apps)}

            elif action == "focus_app":
                if not app_name:
                    return {"success": False, "error": "app_name is required for focus_app"}
                script = f'tell application "{app_name}" to activate'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    return {"success": False, "error": stderr.decode()}
                return {"success": True, "message": f"Focused application: {app_name}"}

            elif action == "quit_app":
                if not app_name:
                    return {"success": False, "error": "app_name is required for quit_app"}
                script = f'tell application "{app_name}" to quit'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                return {"success": True, "message": f"Requested quit for: {app_name}"}

            elif action == "set_volume":
                if volume_level is None:
                    return {"success": False, "error": "volume_level (0-100) is required"}
                level = max(0, min(100, int(volume_level)))
                script = f'set volume output volume {level}'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return {"success": True, "message": f"macOS output volume set to {level}%"}

            elif action == "get_volume":
                script = 'output volume of (get volume settings)'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                return {"success": True, "output_volume": stdout.decode().strip()}

            return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
