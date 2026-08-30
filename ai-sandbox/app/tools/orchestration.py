from typing import Any, Dict
import time
from app.events.schemas import PermissionLevel, RiskLevel, AgentMessage, Role
from app.tools.gateway import Tool
from app.agents.base import ExplorerAgent, AgentConfig, AgentContext
from app.events.bus import get_event_bus

class DelegateTaskTool(Tool):
    @property
    def name(self) -> str:
        return "delegate_task"
    
    @property
    def description(self) -> str:
        return "Spawn a specialized sub-agent to handle a specific task. Use this to delegate work instead of doing it yourself. Pass in a role (e.g., 'Python Developer') and a detailed task description."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "The persona/role for the sub-agent (e.g., 'QA Tester', 'Web Scraper')"
                },
                "task": {
                    "type": "string",
                    "description": "A detailed explanation of what the sub-agent needs to accomplish"
                }
            },
            "required": ["role", "task"]
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
        role = arguments["role"]
        task = arguments["task"]
        
        # Create a temporary agent
        agent_id = f"worker_{int(time.time())}"
        config = AgentConfig(
            agent_identity=role.lower().replace(" ", "_"),
            name=role,
            system_prompt=f"You are a {role}. Your sole objective is to complete the following task: {task}\nYou have full access to tools.",
            model="hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M",
            temperature=0.2,
            max_tokens=2048
        )
        
        # Use existing ExplorerAgent logic for now as a generic worker
        worker = ExplorerAgent(agent_id, config, event_bus=get_event_bus())
        
        # Build a context
        context = AgentContext(
            conversation_id="subtask_" + agent_id,
            turn_number=1,
            recent_messages=[
                AgentMessage(
                    message_id="msg_0",
                    conversation_id="subtask_" + agent_id,
                    turn_number=1,
                    role=Role.USER,
                    content=task,
                    agent_identity="Manager"
                )
            ]
        )
        
        # Let the worker think and act
        try:
            result = await worker.think(context)
            return f"Sub-Agent '{role}' returned:\\n{result}"
        except Exception as e:
            return f"Sub-Agent '{role}' failed with error: {str(e)}"

