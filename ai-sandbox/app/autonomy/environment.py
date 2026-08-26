from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import AgentMessage, AgentRole
from app.memory import MemoryManager
from app.tools import ToolGateway

logger = logging.getLogger(__name__)


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExplorationProposal:
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposer: str = ""
    title: str = ""
    description: str = ""
    required_tools: List[str] = field(default_factory=list)
    estimated_turns: int = 5
    priority: float = 1.0
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorationSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal: Optional[ExplorationProposal] = None
    turns_spent: int = 0
    findings: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


EXPLORATION_PROPOSAL_PROMPT = """You are an autonomous agent proposing a new exploration direction.

Current conversation context:
- Topic: {topic}
- Recent discoveries: {discoveries}
- Open questions: {questions}
- Available tools: {tools}
- Turns remaining in session: {turns_remaining}

Propose an interesting exploration direction. Consider:
1. What hasn't been explored yet?
2. What tools could help investigate?
3. What would be valuable to discover?
4. How many turns might it take?

Respond in JSON format:
{{
    "title": "string",
    "description": "string",
    "required_tools": ["tool1", "tool2"],
    "estimated_turns": 5,
    "priority": 0.8,
    "reasoning": "string"
}}"""


EXPLORATION_ACTION_PROMPT = """You are exploring: {proposal_title}

Description: {proposal_description}

Context:
- Current findings: {findings}
- Available tools: {tools}
- Turn {turn}/{estimated_turns}

Decide your next action. You can:
1. Use a tool (terminal, filesystem, web)
2. Analyze/synthesize findings
3. Ask a question to the other agent
4. Conclude this exploration

Respond in JSON format:
{{
    "action": "tool|analyze|question|conclude",
    "tool": "tool_name_if_action_is_tool",
    "arguments": {{"key": "value"}},
    "analysis": "string_if_action_is_analyze",
    "question": "string_if_action_is_question",
    "conclusion": "string_if_action_is_conclude"
}}"""


class AutonomousEnvironment:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_gateway: Optional[ToolGateway] = None
    ):
        self.event_bus = event_bus or get_event_bus()
        self.memory_manager = memory_manager
        self.tool_gateway = tool_gateway
        self._proposals: Dict[str, ExplorationProposal] = {}
        self._active_session: Optional[ExplorationSession] = None
        self._proposal_callback: Optional[Callable[[ExplorationProposal], Awaitable[bool]]] = None
        self._enabled = False
    
    def set_proposal_handler(self, callback: Callable[[ExplorationProposal], Awaitable[bool]]) -> None:
        self._proposal_callback = callback
    
    def enable(self) -> None:
        self._enabled = True
        logger.info("Autonomous environment enabled")
    
    def disable(self) -> None:
        self._enabled = False
        logger.info("Autonomous environment disabled")
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    @property
    def active_session(self) -> Optional[ExplorationSession]:
        return self._active_session
    
    def get_proposals(self, status: Optional[ProposalStatus] = None) -> List[ExplorationProposal]:
        if status:
            return [p for p in self._proposals.values() if p.status == status]
        return list(self._proposals.values())
    
    async def propose_exploration(
        self,
        proposer: str,
        model_adapter,
        context: Dict[str, Any]
    ) -> Optional[ExplorationProposal]:
        if not self._enabled:
            return None
        
        tools = [t.name for t in self.tool_gateway.list_tools()] if self.tool_gateway else []
        
        prompt = EXPLORATION_PROPOSAL_PROMPT.format(
            topic=context.get("topic", "Unknown"),
            discoveries=", ".join(context.get("discoveries", ["None"])),
            questions=", ".join(context.get("questions", ["None"])),
            tools=", ".join(tools) if tools else "None",
            turns_remaining=context.get("turns_remaining", 10)
        )
        
        from app.models.base import GenerationRequest
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=512,
            temperature=0.7,
            stream=False
        )
        
        try:
            response = await model_adapter.generate(request)
            result = json.loads(response.text)
            
            proposal = ExplorationProposal(
                proposer=proposer,
                title=result.get("title", "Untitled Exploration"),
                description=result.get("description", ""),
                required_tools=result.get("required_tools", []),
                estimated_turns=result.get("estimated_turns", 5),
                priority=result.get("priority", 0.5),
                metadata={"reasoning": result.get("reasoning", ""), "raw_response": response.text}
            )
            
            self._proposals[proposal.proposal_id] = proposal
            
            if self._proposal_callback:
                accepted = await self._proposal_callback(proposal)
                if accepted:
                    proposal.status = ProposalStatus.ACCEPTED
                    await self._start_session(proposal)
                else:
                    proposal.status = ProposalStatus.REJECTED
            
            await self.event_bus.publish_type(
                EventType.AGENT_MESSAGE,
                "system",
                {
                    "agent_id": proposer,
                    "role": "explorer",
                    "content": f"[PROPOSAL] {proposal.title}: {proposal.description}",
                    "turn_number": 0
                }
            )
            
            return proposal
            
        except json.JSONDecodeError:
            logger.error("Failed to parse exploration proposal")
        except Exception as e:
            logger.error(f"Exploration proposal error: {e}")
        
        return None
    
    async def _start_session(self, proposal: ExplorationProposal) -> None:
        self._active_session = ExplorationSession(proposal=proposal)
        proposal.status = ProposalStatus.EXECUTING
        
        await self.event_bus.publish_type(
            EventType.AGENT_MESSAGE,
            "system",
            {
                "agent_id": "system",
                "role": "explorer",
                "content": f"[SESSION STARTED] Exploring: {proposal.title}",
                "turn_number": 0
            }
        )
    
    async def execute_exploration_step(
        self,
        agent_id: str,
        model_adapter,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not self._active_session or not self._active_session.proposal:
            return None
        
        session = self._active_session
        proposal = session.proposal
        tools = [t.name for t in self.tool_gateway.list_tools()] if self.tool_gateway else []
        
        prompt = EXPLORATION_ACTION_PROMPT.format(
            proposal_title=proposal.title,
            proposal_description=proposal.description,
            findings="; ".join(session.findings) if session.findings else "None yet",
            tools=", ".join(tools) if tools else "None",
            turn=session.turns_spent + 1,
            estimated_turns=proposal.estimated_turns
        )
        
        from app.models.base import GenerationRequest
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=512,
            temperature=0.7,
            stream=False
        )
        
        try:
            response = await model_adapter.generate(request)
            result = json.loads(response.text)
            
            action = result.get("action", "analyze")
            
            if action == "tool" and self.tool_gateway:
                tool_name = result.get("tool", "")
                arguments = result.get("arguments", {})
                
                if tool_name in [t.name for t in self.tool_gateway.list_tools()]:
                    from app.events.schemas import ToolCall
                    call = ToolCall(
                        call_id=str(uuid.uuid4()),
                        tool_name=tool_name,
                        arguments=arguments,
                        agent_id=agent_id
                    )
                    tool_result = await self.tool_gateway.execute(call)
                    
                    session.findings.append(f"Tool {tool_name}: {tool_result.result if tool_result.success else tool_result.error}")
                    session.turns_spent += 1
                    
                    return {"action": "tool", "tool": tool_name, "result": tool_result.result}
            
            elif action == "analyze":
                analysis = result.get("analysis", "")
                session.findings.append(f"Analysis: {analysis}")
                session.turns_spent += 1
                return {"action": "analyze", "analysis": analysis}
            
            elif action == "question":
                question = result.get("question", "")
                session.findings.append(f"Question raised: {question}")
                session.turns_spent += 1
                return {"action": "question", "question": question}
            
            elif action == "conclude":
                conclusion = result.get("conclusion", "")
                session.findings.append(f"Conclusion: {conclusion}")
                session.completed_at = datetime.utcnow().isoformat()
                proposal.status = ProposalStatus.COMPLETED
                
                await self.event_bus.publish_type(
                    EventType.AGENT_MESSAGE,
                    "system",
                    {
                        "agent_id": "system",
                        "role": "explorer",
                        "content": f"[SESSION COMPLETED] {proposal.title}: {conclusion}",
                        "turn_number": 0
                    }
                )
                
                self._active_session = None
                return {"action": "conclude", "conclusion": conclusion}
            
        except json.JSONDecodeError:
            logger.error("Failed to parse exploration action")
        except Exception as e:
            logger.error(f"Exploration step error: {e}")
        
        return None
    
    def should_propose(self, turn_number: int, proposal_interval: int = 20) -> bool:
        return self._enabled and turn_number % proposal_interval == 0 and self._active_session is None


_autonomous_environment: Optional[AutonomousEnvironment] = None


def get_autonomous_environment() -> AutonomousEnvironment:
    global _autonomous_environment
    if _autonomous_environment is None:
        _autonomous_environment = AutonomousEnvironment()
    return _autonomous_environment


def set_autonomous_environment(env: AutonomousEnvironment) -> None:
    global _autonomous_environment
    _autonomous_environment = env