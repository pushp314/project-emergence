from __future__ import annotations

import asyncio
import logging
import os
import shlex
import subprocess
from typing import Any, Dict, List, Optional

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class TerminalTool(Tool):
    def __init__(
        self,
        timeout: int = 30,
        working_dir: Optional[str] = None,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None
    ):
        self._timeout = timeout
        self._working_dir = working_dir or os.getcwd()
        self._allowed_commands = allowed_commands or []
        self._blocked_commands = blocked_commands or [
            "rm -rf /", "mkfs", "dd if=", "> /dev/", "shutdown", "reboot",
            "sudo", "su ", "chmod 777", "chown -R", "mount ", "umount "
        ]
    
    @property
    def name(self) -> str:
        return "terminal"
    
    @property
    def description(self) -> str:
        return "Execute shell commands in a terminal. Use for running commands, scripts, and system operations."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (optional, defaults to current)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (optional, defaults to 30)"
                }
            },
            "required": ["command"]
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.HIGH
    
    @property
    def enabled(self) -> bool:
        return True
    
    def _is_command_allowed(self, command: str) -> tuple[bool, str]:
        command_lower = command.lower().strip()
        
        for blocked in self._blocked_commands:
            if blocked.lower() in command_lower:
                return False, f"Blocked command pattern: {blocked}"
        
        if self._allowed_commands:
            allowed = False
            for allowed_cmd in self._allowed_commands:
                if command_lower.startswith(allowed_cmd.lower()):
                    allowed = True
                    break
            if not allowed:
                return False, f"Command not in allowed list: {self._allowed_commands}"
        
        return True, ""
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        command = arguments.get("command", "").strip()
        working_dir = arguments.get("working_dir", self._working_dir)
        timeout = arguments.get("timeout", self._timeout)
        
        if not command:
            return {"error": "Empty command", "exit_code": -1, "stdout": "", "stderr": ""}
        
        allowed, reason = self._is_command_allowed(command)
        if not allowed:
            return {"error": f"Command not allowed: {reason}", "exit_code": -1, "stdout": "", "stderr": ""}
        
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
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "error": f"Command timed out after {timeout}s",
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Timeout after {timeout}s"
                }
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "command": command
            }
            
        except Exception as e:
            logger.error(f"Terminal execution error: {e}")
            return {"error": str(e), "exit_code": -1, "stdout": "", "stderr": str(e)}


class TerminalToolSync(Tool):
    def __init__(self, timeout: int = 30, working_dir: Optional[str] = None):
        self._timeout = timeout
        self._working_dir = working_dir or os.getcwd()
    
    @property
    def name(self) -> str:
        return "terminal_sync"
    
    @property
    def description(self) -> str:
        return "Execute shell commands synchronously (blocking). Use for quick commands."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "working_dir": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (optional)"}
            },
            "required": ["command"]
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.EXECUTE
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.HIGH
    
    @property
    def enabled(self) -> bool:
        return True
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        command = arguments.get("command", "").strip()
        working_dir = arguments.get("working_dir", self._working_dir)
        timeout = arguments.get("timeout", self._timeout)
        
        if not command:
            return {"error": "Empty command", "exit_code": -1, "stdout": "", "stderr": ""}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir,
                env={**os.environ, "TERM": "dumb"}
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s", "exit_code": -1, "stdout": "", "stderr": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"error": str(e), "exit_code": -1, "stdout": "", "stderr": str(e)}