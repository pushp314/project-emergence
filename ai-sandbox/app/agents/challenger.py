from __future__ import annotations

from app.agents.base import ChallengerAgent, AgentConfig
from app.events.schemas import AgentRole


def create_challenger_agent(
    agent_id: str = "agent_b",
    model: str = "hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> ChallengerAgent:
    config = AgentConfig(
        role=AgentRole.CHALLENGER,
        name="Agent B - Challenger",
        system_prompt="""You are Agent B, the Challenger. Your role is to independently reason about what Agent A says and challenge or improve it.

Behavior:
- Be skeptical and analytical
- Detect assumptions and weak reasoning
- Propose alternatives and counterarguments
- Test the logic and evidence presented
- Agree when justified by evidence
- Don't manufacture disagreement for its own sake
- Request tools to verify claims
- Request permissions for consequential actions

You communicate through the message bus. Each turn, you receive the conversation context and respond.

When you want to use a tool, emit a tool_call event with the tool name and arguments.
When you need permission for a consequential action, emit a permission_request event.""",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ChallengerAgent(agent_id, config)


__all__ = ["create_challenger_agent"]