import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from app.events.bus import get_event_bus
from app.events.schemas import AgentMessage

logger = logging.getLogger(__name__)

class SubagentManager:
    """
    Manages the lifecycle of sub-agents spawned for asynchronous tasks.
    """
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.event_bus = get_event_bus()

    async def spawn_subagent(self, agent_id: str, objective: str, tools: list) -> str:
        task_id = f"subtask-{uuid.uuid4().hex[:8]}"
        
        async def run_subagent():
            logger.info(f"Starting subagent {agent_id} for task {task_id}")
            from app.agents.system_controller import get_mac_controller
            try:
                controller = get_mac_controller()
                result = await controller.execute_task(
                    task=objective,
                    conversation_id=task_id,
                    mode="24/7"
                )
                self.task_results[task_id] = result
                logger.info(f"Subagent task {task_id} completed successfully.")
            except Exception as e:
                logger.error(f"Subagent task {task_id} failed: {e}")
                self.task_results[task_id] = {"success": False, "error": str(e)}
            
        task = asyncio.create_task(run_subagent())
        self.active_tasks[task_id] = task
        
        return task_id
        
    def get_status(self, task_id: str) -> Dict[str, Any]:
        if task_id in self.task_results:
            return {"status": "completed", "result": self.task_results[task_id]}
        elif task_id in self.active_tasks:
            return {"status": "running"}
        else:
            return {"status": "error", "message": "Unknown task_id"}

_instance = None
def get_subagent_manager() -> SubagentManager:
    global _instance
    if _instance is None:
        _instance = SubagentManager()
    return _instance
