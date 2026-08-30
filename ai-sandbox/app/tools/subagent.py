from typing import Any, Dict

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel
from app.orchestration.subagent_manager import get_subagent_manager

class SubAgentTool(Tool):
    def __init__(self):
        self.manager = get_subagent_manager()
        
    @property
    def name(self) -> str:
        return "subagent"
        
    @property
    def description(self) -> str:
        return "Spawn or check on asynchronous sub-agents for parallel tasks."
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["spawn", "check_status"]
                },
                "objective": {
                    "type": "string",
                    "description": "What the subagent should do (required for spawn)"
                },
                "tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tools to give the subagent (optional)"
                },
                "task_id": {
                    "type": "string",
                    "description": "Task ID to check (required for check_status)"
                }
            },
            "required": ["operation"]
        }
        
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.SYSTEM
        
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.MEDIUM
        
    @property
    def enabled(self) -> bool:
        return True
        
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        operation = arguments.get("operation")
        if operation == "spawn":
            task_id = await self.manager.spawn_subagent(
                agent_id="subagent",
                objective=arguments.get("objective", ""),
                tools=arguments.get("tools", [])
            )
            return {"status": "spawned", "task_id": task_id}
        elif operation == "check_status":
            task_id = arguments.get("task_id")
            if not task_id:
                raise ValueError("task_id required for check_status")
            return self.manager.get_status(task_id)
        else:
            raise ValueError(f"Unknown operation: {operation}")
