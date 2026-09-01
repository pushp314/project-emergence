from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool

logger = logging.getLogger(__name__)


class MacNotifyTool(Tool):
    """Native macOS Notifications, Text-To-Speech, and Finder App launcher."""

    @property
    def name(self) -> str:
        return "mac_notify"

    @property
    def description(self) -> str:
        return "Interact with native macOS system alerts: send notification banners to macOS Notification Center, speak audio confirmations using 'say', or open files/apps in Finder."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["notify", "speak", "open"],
                    "description": "The action: 'notify' (banner), 'speak' (audio TTS), 'open' (open in Finder/App)"
                },
                "title": {
                    "type": "string",
                    "description": "Title for notification banner (optional, default 'AI Sandbox')"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to display or speak"
                },
                "target": {
                    "type": "string",
                    "description": "Path or application name for 'open' action (e.g. '~/Desktop/Research_Reports' or 'Calculator')"
                }
            },
            "required": ["action"]
        }

    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE

    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def enabled(self) -> bool:
        return True

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        action = arguments.get("action", "notify")
        message = arguments.get("message", "")
        title = arguments.get("title", "AI Sandbox Mission Control")
        target = arguments.get("target", "")

        try:
            if action == "notify":
                # Escape double quotes
                safe_msg = message.replace('"', '\\"')
                safe_title = title.replace('"', '\\"')
                script = f'display notification "{safe_msg}" with title "{safe_title}"'
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return {"success": True, "message": f"macOS notification sent: {title} - {message}"}

            elif action == "speak":
                safe_msg = message.replace('"', '')
                proc = await asyncio.create_subprocess_exec(
                    "say", safe_msg,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return {"success": True, "message": f"Spoken aloud: '{safe_msg}'"}

            elif action == "open":
                if not target:
                    return {"success": False, "error": "target path or app required for open action"}
                
                import os
                expanded = os.path.expanduser(target)
                proc = await asyncio.create_subprocess_exec(
                    "open", expanded,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    return {"success": False, "error": stderr.decode()}
                return {"success": True, "message": f"Opened in macOS: {expanded}"}

            return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
