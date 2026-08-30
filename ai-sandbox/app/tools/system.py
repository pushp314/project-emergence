import os
import sys
import asyncio
import logging
from typing import Any, Dict

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)

class SystemTool(Tool):
    @property
    def name(self) -> str:
        return "system"

    @property
    def description(self) -> str:
        return "Manage the Jarvis system lifecycle. Reboot the server, install pip packages, or run low-level system commands."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["reboot", "install_pip_package"],
                    "description": "The system operation to perform."
                },
                "package_name": {
                    "type": "string",
                    "description": "Name of the pip package to install (if operation is install_pip_package)."
                }
            },
            "required": ["operation"]
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
        operation = arguments.get("operation")
        
        if operation == "reboot":
            logger.warning("Agent triggered a self-reboot!")
            # Gracefully flush logs and then exit. The immortal supervisor will restart us.
            
            # We run the exit in an async task so we can return the success response to the agent first
            async def delayed_exit():
                await asyncio.sleep(1)
                os._exit(0)
                
            asyncio.create_task(delayed_exit())
            return {"success": True, "message": "Initiating reboot sequence in 1 second. The supervisor will bring the system back online."}
            
        elif operation == "install_pip_package":
            package_name = arguments.get("package_name")
            if not package_name:
                return {"success": False, "error": "package_name is required for install_pip_package."}
            
            # Ensure we install in the current python environment (venv)
            python_executable = sys.executable
            
            logger.info(f"Agent installing pip package: {package_name}")
            process = await asyncio.create_subprocess_shell(
                f'"{python_executable}" -m pip install {package_name}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {"success": True, "output": stdout.decode()}
            else:
                return {"success": False, "error": stderr.decode()}
                
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
