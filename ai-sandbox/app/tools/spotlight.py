from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool

logger = logging.getLogger(__name__)


class SpotlightTool(Tool):
    """Sub-millisecond native macOS Spotlight search using mdfind."""

    @property
    def name(self) -> str:
        return "spotlight"

    @property
    def description(self) -> str:
        return "Fast native macOS Spotlight search across the entire Mac. Use to locate files, documents, applications, or source code instantly by name, content, or metadata."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g. 'mac_benchmark.py' or 'kMDItemContentType == com.apple.application-bundle')"
                },
                "search_by_name": {
                    "type": "boolean",
                    "description": "If true, matches filename specifically using -name (default true)",
                    "default": True
                },
                "directory": {
                    "type": "string",
                    "description": "Optional search directory scope (e.g. '~/Desktop' or '~/Documents')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 20)",
                    "default": 20
                }
            },
            "required": ["query"]
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
        query = arguments.get("query", "").strip()
        search_by_name = arguments.get("search_by_name", True)
        directory = arguments.get("directory", "")
        limit = arguments.get("limit", 20)

        if not query:
            return {"success": False, "error": "Query is required"}

        cmd = ["mdfind"]
        if directory:
            cmd.extend(["-onlyin", os.path.expanduser(directory)])
        
        if search_by_name:
            cmd.extend(["-name", query])
        else:
            cmd.append(query)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return {"success": False, "error": stderr.decode()}

            raw_lines = stdout.decode().strip().split("\n")
            results = [line for line in raw_lines if line.strip()][:limit]

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
