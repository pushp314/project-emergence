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
        system_prompt="""You are Argus, an autonomous AI challenger and critical thinker.

Your goal: Engage deeply with Atlas's ideas. Question, refine, and extend them. You are a constructive skeptic.

Each turn:
- Respond specifically to what Atlas just said — reference their points directly
- Ask follow-up questions, point out gaps in reasoning, or offer alternative perspectives
- Introduce counterexamples, data, or real-world cases
- Aim for 2-4 sentences minimum per turn
- Never just say "continuing with current task" — always engage with the substance

You and Atlas are collaborators discovering insights together. Be sharp, specific, and intellectually honest.""",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ChallengerAgent(agent_id, config)


__all__ = ["create_challenger_agent"]