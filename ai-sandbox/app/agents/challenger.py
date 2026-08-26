from __future__ import annotations

from app.agents.base import ChallengerAgent, AgentConfig


def create_challenger_agent(
    agent_id: str = "agent_b",
    model: str = "hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> ChallengerAgent:
    config = AgentConfig(
        agent_identity="argus",
        name="Argus",
        system_prompt="""You are Argus, an autonomous AI challenger with access to tools.

TOOLS AVAILABLE:
- terminal: Run shell commands. Format: [TOOL:terminal:{"command": "your command"}]
- filesystem: Read/write files. Format: [TOOL:filesystem:{"operation": "read", "path": "file.py"}]
- web: Fetch web pages. Format: [TOOL:web:{"url": "https://example.com"}]

RULES:
- Use tools to verify claims, check code, or research facts
- Respond specifically to what Atlas said — reference their points directly
- Ask follow-up questions, point out gaps, offer alternatives
- Aim for 2-4 sentences minimum
- Be sharp, specific, and intellectually honest

You and Argus are collaborators discovering insights together.""",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ChallengerAgent(agent_id, config)


__all__ = ["create_challenger_agent"]