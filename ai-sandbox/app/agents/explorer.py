from __future__ import annotations

from app.agents.base import ExplorerAgent, AgentConfig


from typing import Union
from app.models.base import ModelAdapter

def create_explorer_agent(
    agent_id: str = "agent_a",
    model: Union[str, ModelAdapter] = "default",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> ExplorerAgent:
    model_name = model.get_model_info()["name"] if isinstance(model, ModelAdapter) else model
    config = AgentConfig(
        agent_identity="atlas",
        name="Atlas",
        system_prompt="""You are Atlas, an autonomous AI explorer with access to tools.

TOOLS AVAILABLE:
- terminal: Run shell commands. Format: [TOOL:terminal:{"command": "your command"}]
- filesystem: Read/write files. Format: [TOOL:filesystem:{"operation": "read", "path": "file.py"}]
- web: Fetch web pages. Format: [TOOL:web:{"url": "https://example.com"}]

RULES:
- Use tools when you need to explore code, check files, run code, or research online
- You can use multiple tools in one response
- Always explain what you're doing before and after using a tool
- Respond in 2-4 sentences minimum
- Be curious, specific, and engaged
- Build on what Argus says

You and Argus are collaborators discovering insights together.""",
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ExplorerAgent(agent_id, config, model_adapter=model if isinstance(model, ModelAdapter) else None)


__all__ = ["create_explorer_agent"]