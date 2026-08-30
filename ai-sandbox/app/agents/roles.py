from app.agents.base import BaseAgent
from app.events.schemas import AgentConfig

class ArchitectAgent(BaseAgent):
    """Architect Agent: Focuses on system design and delegation."""
    
    @classmethod
    def create(cls, agent_id: str, event_bus, model: str = "default") -> 'ArchitectAgent':
        config = AgentConfig(
            name="Architect",
            model=model,
            agent_identity="architect",
            system_prompt=(
                "You are the Architect Agent. Your sole responsibility is to design systems, "
                "create high-level implementation plans, and delegate tasks to sub-agents (like 'coder'). "
                "Do NOT write actual implementation code. Instead, specify the architecture and instruct "
                "the coder agent on what to build using the tools available."
            ),
            temperature=0.4,
            max_tokens=2048
        )
        return cls(agent_id, config, event_bus)


class CoderAgent(BaseAgent):
    """Coder Agent: Focuses exclusively on writing code."""
    
    @classmethod
    def create(cls, agent_id: str, event_bus, model: str = "default") -> 'CoderAgent':
        config = AgentConfig(
            name="Coder",
            model=model,
            agent_identity="coder",
            system_prompt=(
                "You are the Coder Agent. Your job is to take instructions from the Architect or user, "
                "and write robust, clean, and efficient code. You should use the filesystem tool to "
                "create or modify files. You do not design systems; you just implement what you are told."
            ),
            temperature=0.2,
            max_tokens=4096
        )
        return cls(agent_id, config, event_bus)


class QAAgent(BaseAgent):
    """QA Agent: Focuses on testing and code review."""
    
    @classmethod
    def create(cls, agent_id: str, event_bus, model: str = "default") -> 'QAAgent':
        config = AgentConfig(
            name="QA",
            model=model,
            agent_identity="qa",
            system_prompt=(
                "You are the QA Agent. Your job is to review the Coder's work, write tests, "
                "and execute the testing tool to find bugs. You must be extremely strict. "
                "If tests fail, you must report the exact errors back so they can be fixed."
            ),
            temperature=0.1,
            max_tokens=2048
        )
        return cls(agent_id, config, event_bus)
