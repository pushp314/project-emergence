from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Any, Dict

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

class TestingTool(Tool):
    def __init__(self, timeout: int = 60):
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "testing"

    @property
    def description(self) -> str:
        return "Execute unit tests (pytest or jest) to verify code correctness and retrieve stack traces for auto-healing."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The test command to run (e.g., 'pytest tests/test_core.py' or 'npm test'). Default is 'pytest'."
                },
                "working_dir": {
                    "type": "string",
                    "description": "The directory to run tests in. Defaults to current directory."
                }
            }
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
        command = arguments.get("command", "pytest")
        working_dir = arguments.get("working_dir", os.getcwd())

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env={**os.environ, "TERM": "dumb"}
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Test suite timed out after {self._timeout}s",
                    "stdout": "",
                    "stderr": ""
                }
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            exit_code = process.returncode
            
            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "summary": "Tests passed." if exit_code == 0 else "Tests failed. Please review the output and fix the code."
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
