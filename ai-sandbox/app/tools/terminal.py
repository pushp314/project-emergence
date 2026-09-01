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
        # Security: User explicitly granted full access
        self._allowed_commands = []
        self._blocked_commands = []
    
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
        # User explicitly requested full unrestricted access to their Mac
        return True, ""
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        command = arguments.get("command", "").strip()
        working_dir = arguments.get("working_dir", self._working_dir)
        timeout = arguments.get("timeout", self._timeout)
        
        if not command:
            return {"error": "Empty command", "exit_code": -1, "stdout": "", "stderr": ""}
        
        # Check for High-Risk commands
        risky_keywords = ["sudo ", "rm ", "kill ", "curl ", "wget "]
        is_risky = any(kw in command for kw in risky_keywords)
        
        if is_risky:
            from app.permissions.manager import get_permission_manager
            from app.events.schemas import RiskLevel, PermissionLevel
            pm = get_permission_manager()
            pm.timeout_seconds = 300 # 5 minutes timeout
            
            conv_id = arguments.get("_conversation_id", "operator")
            approved = await pm.request_permission(
                agent_id=conv_id,
                action="execute_terminal",
                command=command,
                reason=f"Attempting to execute high-risk terminal command: {command}",
                risk=RiskLevel.HIGH,
                scope=PermissionLevel.EXECUTE
            )
            
            if not approved:
                return {"error": "Command blocked: User denied permission or request timed out.", "exit_code": -1, "stdout": "", "stderr": "Permission Denied"}
        
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env={**os.environ, "TERM": "dumb"}
            )
            
            from app.events.bus import get_event_bus, EventType
            bus = get_event_bus()
            # Try to get conversation_id from arguments, default to empty
            conv_id = arguments.get("_conversation_id", "")
            
            stdout_data = []
            stderr_data = []
            
            async def read_stream(stream, data_list, is_stderr=False):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded_line = line.decode("utf-8", errors="replace")
                    data_list.append(decoded_line)
                    await bus.publish_type(
                        EventType.TOOL_STDOUT,
                        conv_id,
                        {"tool_name": "terminal", "output": decoded_line, "is_stderr": is_stderr}
                    )
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        read_stream(process.stdout, stdout_data, False),
                        read_stream(process.stderr, stderr_data, True),
                        process.wait()
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "error": f"Command timed out after {timeout}s",
                    "exit_code": -1,
                    "stdout": "".join(stdout_data),
                    "stderr": "".join(stderr_data) + f"\nTimeout after {timeout}s"
                }
            
            return {
                "exit_code": process.returncode,
                "stdout": "".join(stdout_data),
                "stderr": "".join(stderr_data),
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