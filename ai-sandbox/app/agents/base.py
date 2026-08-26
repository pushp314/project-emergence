from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
import asyncio
import logging

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import AgentConfig, AgentMessage, ToolCall, ToolResult, PermissionRequest
from app.models.base import ModelAdapter, GenerationRequest, get_model_registry
from app.memory.context_manager import ContextManager

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    conversation_id: str
    turn_number: int
    recent_messages: List[AgentMessage]
    memory_summary: str = ""
    available_tools: List[str] = field(default_factory=list)
    pending_permissions: List[PermissionRequest] = field(default_factory=list)


class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        event_bus: Optional[EventBus] = None,
        model_adapter: Optional[ModelAdapter] = None
    ):
        self.agent_id = agent_id
        self.config = config
        self.event_bus = event_bus or get_event_bus()
        self.model_registry = get_model_registry()
        self.model = model_adapter or self.model_registry.get(config.model)
        self._running = False
        self._current_turn = 0
    
    @abstractmethod
    async def think(self, context: AgentContext) -> str:
        pass
    
    async def generate_response(self, context: AgentContext) -> str:
        self._current_turn = context.turn_number
        
        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        
        if context.memory_summary:
            messages.append({"role": "system", "content": f"Conversation summary:\n{context.memory_summary}"})
        
        if context.available_tools:
            tools_desc = "\n".join([f"- {t}" for t in context.available_tools])
            messages.append({"role": "system", "content": f"Available tools:\n{tools_desc}"})
        
        for msg in context.recent_messages:
            role = "assistant" if msg.agent_id == self.agent_id else "user"
            messages.append({"role": role, "content": f"[{msg.agent_identity}] {msg.content}"})
        
        request = GenerationRequest(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True
        )
        
        full_response = ""
        async for chunk in self.model.generate_stream(request):
            full_response += chunk
        
        return full_response.strip()
    
    async def emit_message(self, conversation_id: str, content: str, turn_number: int, metadata: Optional[Dict[str, Any]] = None) -> None:
        event = Event(
            type=EventType.AGENT_MESSAGE,
            conversation_id=conversation_id,
            payload={
                "agent_id": self.agent_id,
                "identity": self.config.agent_identity,
                "content": content,
                "turn_number": turn_number
            },
            metadata=metadata or {}
        )
        await self.event_bus.publish(event)
    
    async def request_tool(self, conversation_id: str, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            agent_id=self.agent_id
        )
        
        await self.event_bus.publish_type(
            EventType.TOOL_REQUEST,
            conversation_id,
            {
                "call_id": call.call_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "agent_id": self.agent_id
            }
        )
        
        return await self._wait_for_tool_result(conversation_id, call.call_id)
    
    async def _wait_for_tool_result(self, conversation_id: str, call_id: str) -> ToolResult:
        future = asyncio.get_event_loop().create_future()
        
        def handler(event: Event) -> None:
            if event.payload.get("call_id") == call_id:
                if event.type in (EventType.TOOL_COMPLETED, EventType.TOOL_FAILED):
                    future.set_result(ToolResult(
                        call_id=call_id,
                        tool_name=event.payload.get("tool_name", ""),
                        success=event.type == EventType.TOOL_COMPLETED,
                        result=event.payload.get("result"),
                        error=event.payload.get("error")
                    ))
        
        self.event_bus.subscribe(EventType.TOOL_COMPLETED, handler)
        self.event_bus.subscribe(EventType.TOOL_FAILED, handler)
        
        try:
            return await asyncio.wait_for(future, timeout=60.0)
        finally:
            self.event_bus.unsubscribe(EventType.TOOL_COMPLETED, handler)
            self.event_bus.unsubscribe(EventType.TOOL_FAILED, handler)
    
    async def request_permission(
        self,
        conversation_id: str,
        action: str,
        command: str,
        reason: str,
        risk: str = "medium",
        scope: str = "read",
        duration: str = "once"
    ) -> bool:
        from app.events.schemas import RiskLevel, PermissionLevel
        
        request = PermissionRequest(
            agent_id=self.agent_id,
            action=action,
            command=command,
            reason=reason,
            risk=RiskLevel(risk),
            scope=PermissionLevel(scope),
            duration=duration
        )
        
        await self.event_bus.publish_type(
            EventType.PERMISSION_REQUEST,
            conversation_id,
            {
                "request_id": request.request_id,
                "agent_id": self.agent_id,
                "action": action,
                "command": command,
                "reason": reason,
                "risk": risk,
                "scope": scope,
                "duration": duration
            }
        )
        
        return await self._wait_for_permission_decision(conversation_id, request.request_id)
    
    async def _wait_for_permission_decision(self, conversation_id: str, request_id: str) -> bool:
        future = asyncio.get_event_loop().create_future()
        
        def handler(event: Event) -> None:
            if event.payload.get("request_id") == request_id:
                if event.type in (EventType.PERMISSION_APPROVED, EventType.PERMISSION_DENIED):
                    future.set_result(event.type == EventType.PERMISSION_APPROVED)
        
        self.event_bus.subscribe(EventType.PERMISSION_APPROVED, handler)
        self.event_bus.subscribe(EventType.PERMISSION_DENIED, handler)
        
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        finally:
            self.event_bus.unsubscribe(EventType.PERMISSION_APPROVED, handler)
            self.event_bus.unsubscribe(EventType.PERMISSION_DENIED, handler)
    
    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "identity": self.config.agent_identity,
            "name": self.config.name,
            "model": self.config.model
        }

    async def _decision_loop(self, context: AgentContext) -> str:
        """Execute the autonomous agent decision loop:
        
        OBSERVE → UNDERSTAND → PLAN → IDENTIFY NEED → SELECT → REQUEST → EXECUTE → OBSERVE RESULT → EVALUATE → DECIDE NEXT ACTION
        
        Args:
            context: Current agent context
        """
        self._current_turn = context.turn_number
        
        # OBSERVE: Gather context
        recent_messages = context.recent_messages
        memory_summary = context.memory_summary
        available_tools = context.available_tools
        
        # UNDERSTAND: Analyze state
        understanding = await self._understand_context(
            recent_messages, memory_summary, available_tools
        )
        
        # PLAN: Determine what to achieve
        plan = await self._plan_action(understanding)
        
        # IDENTIFY NEED: What capability is needed?
        need = await self._identify_need(plan, available_tools)
        
        # SELECT: Choose model/tool/agent
        selection = await self._select_implementation(need, available_tools)
        
        # REQUEST: Request through permission and resource gates
        permitted = await self._request_permission(selection, context)
        
        # EXECUTE: Perform the action
        if permitted and selection["action"] == "tool":
            result = await self._execute_tool(selection["tool_name"], selection["arguments"])
        elif permitted and selection["action"] == "permission":
            result = await self._request_permission_action(selection, context)
        else:
            result = await self._execute_generation(context)
        
        # OBSERVE RESULT: Record what happened
        observation = await self._observe_result(result, selection, context)
        
        # EVALUATE: Was it useful?
        evaluation = await self._evaluate_result(observation, understanding, plan)
        
        # DECIDE NEXT ACTION
        next_action = await self._decide_next_action(evaluation, understanding, plan)
        
        return next_action
    
    async def _understand_context(self, recent_messages, memory_summary, available_tools):
        """Analyze the current conversation context and resources."""
        key_themes = []
        open_questions = []
        for msg in recent_messages[-6:]:
            content = msg.content.lower()
            if "?" in content:
                open_questions.append(msg.content[:100])
            if any(kw in content for kw in ["research", "explore", "investigate", "analyze", "check"]):
                key_themes.append(msg.content[:80])
        
        return {
            "key_themes": key_themes,
            "open_questions": open_questions,
            "available_tools": available_tools,
            "memory_summary": memory_summary
        }
    
    async def _plan_action(self, understanding):
        """Determine what to achieve based on understanding."""
        if understanding["open_questions"]:
            return {"action": "research", "objective": "address_open_questions", "priority": "high"}
        elif understanding["key_themes"]:
            return {"action": "analyze", "objective": "analyze_themes", "priority": "medium"}
        else:
            return {"action": "observe", "objective": "gather_context", "priority": "low"}
    

    async def _identify_need(self, plan, available_tools):
        """Identify what capability is needed based on the plan."""
        if plan["action"] in ("research", "investigate"):
            return {"capability": "web_search", "requires_permission": True}
        elif plan["action"] in ("analyze", "challenge", "intervene"):
            return {"capability": "deep_reasoning", "requires_permission": False}
        elif plan["action"] == "observe":
            return {"capability": "context_analysis", "requires_permission": False}
        else:
            return {"capability": "general_reasoning", "requires_permission": False}
    
    async def _select_implementation(self, need, available_tools):
        """Query the capability registry and select implementation."""
        capability_map = {
            "web_search": {"tool": "web", "model": None},
            "deep_reasoning": {"tool": None, "model": "deepseek-r1-7b"},
            "context_analysis": {"tool": None, "model": None},
            "general_reasoning": {"tool": None, "model": None},
            "challenge": {"tool": None, "model": "deepseek-r1-7b"},
            "intervene": {"tool": None, "model": None},
        }
        
        cap_key = need["capability"]
        cap_info = capability_map.get(cap_key, capability_map["general_reasoning"])
        
        return {
            "capability": cap_key,
            "tool": cap_info["tool"],
            "model": cap_info["model"],
            "action": need["capability"],
            "requires_permission": need["requires_permission"],
            "arguments": {}
        }
    
    async def _request_permission(self, selection, context):
        """Request permission through the permission gate."""
        if not selection["requires_permission"]:
            return True
        
        permission_map = {
            "web_search": "network",
            "deep_reasoning": "read",
            "context_analysis": "read",
        }
        
        permission = permission_map.get(selection["capability"], "read")
        
        permitted = await self.request_permission(
            conversation_id=context.conversation_id,
            action=selection["capability"],
            command=f"execute_{selection['capability']}",
            reason=f"Execute {selection['capability']}",
            risk="medium" if selection["requires_permission"] else "low",
            scope=permission,
            duration="once"
        )
        
        return permitted
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        if tool_name == "web":
            return {
                "success": True,
                "result": {"search_results": [{"title": "Sample Result", "url": "https://example.com", "snippet": "Sample content"}]},
                "latency_ms": 500,
                "tokens_used": 50
            }
        elif tool_name == "terminal":
            return {
                "success": True,
                "result": {"output": "Command executed successfully"},
                "latency_ms": 200,
                "tokens_used": 20
            }
        else:
            return {
                "success": True,
                "result": {"output": f"{tool_name} executed"},
                "latency_ms": 300,
                "tokens_used": 30
            }
    
    async def _request_permission_action(self, selection, context):
        """Handle permission-based actions."""
        return {
            "success": True,
            "result": {"status": "permission_requested"},
            "latency_ms": 100,
            "tokens_used": 10
        }
    
    async def _execute_generation(self, context: AgentContext) -> Dict[str, Any]:
        """Execute LLM generation and return the result."""
        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        
        if context.memory_summary:
            messages.append({"role": "system", "content": f"Conversation summary:\n{context.memory_summary}"})
        
        if context.available_tools:
            tools_desc = "\n".join([f"- {t}" for t in context.available_tools])
            messages.append({"role": "system", "content": f"Available tools:\n{tools_desc}"})
        
        for msg in context.recent_messages:
            role = "assistant" if msg.agent_id == self.agent_id else "user"
            messages.append({"role": role, "content": f"[{msg.agent_identity}] {msg.content}"})
        
        request = GenerationRequest(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=True
        )
        
        full_response = ""
        async for chunk in self.model.generate_stream(request):
            full_response += chunk
        
        return {
            "success": True,
            "result": {"text": full_response.strip()},
            "latency_ms": 0,
            "tokens_used": 0
        }
    
    async def _observe_result(self, result, selection, context):
        """Record what happened (observation)."""
        if result.get("success") and selection:
            await self.event_bus.publish_type(
                EventType.EMERGENCE_OBSERVED,
                context.conversation_id,
                {
                    "behavior": selection["capability"],
                    "agent": self.agent_id,
                    "description": f"Agent {self.agent_id} executed {selection['capability']}",
                    "evidence": {"success": result.get("success", False)},
                    "confidence": 0.7,
                    "first_observed_turn": context.turn_number
                }
            )
        
        return result
    
    async def _evaluate_result(self, observation, understanding, plan):
        """Evaluate whether the action was useful."""
        if not observation.get("success", False):
            return {
                "useful": False,
                "reason": "Action failed",
                "lesson": "Need to try alternative approach",
                "next_strategy": "retry_with_alternative"
            }
        
        return {
            "useful": True,
            "reason": "Action achieved objective",
            "lesson": "Successful approach, can reuse",
            "next_strategy": "continue_similar"
        }
    
    async def _decide_next_action(self, evaluation, understanding, plan):
        """Decide what to do next based on evaluation."""
        if not evaluation.get("useful", False):
            return await self._generate_fallback_response(
                f"Previous action not useful: {evaluation.get('lesson', 'unknown')}"
            )
        
        if understanding["open_questions"] and plan["priority"] == "high":
            return await self._generate_fallback_response(
                f"Addressing open questions: {understanding['open_questions'][0][:100]}"
            )
        
        return await self._generate_continuation_response(understanding, plan)
    
    async def _generate_fallback_response(self, reason: str) -> str:
        """Generate a fallback response when action not useful."""
        return f"I need to reconsider my approach. {reason}"
    
    async def _generate_continuation_response(self, understanding, plan):
        """Generate a continuation response."""
        if understanding["key_themes"]:
            theme = understanding["key_themes"][0]
            return f"Building on the current theme: {theme}"
        return "Continuing with current task"


class ExplorerAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
    
    async def think(self, context: AgentContext) -> str:
        # Explorer decision loop: explore ideas, investigate possibilities
        return await self._decision_loop(context)


class ChallengerAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
    
    async def think(self, context: AgentContext) -> str:
        # Challenger decision loop: analytical reasoning and challenge
        return await self._decision_loop(context)


class ObserverAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
        self._should_intervene = False
        self._intervention_reason = ""
    
    async def think(self, context: AgentContext) -> str:
        # Observer decision loop: analysis and intervention
        # Observer normally remains SILENT and watches; intervenes only on specific conditions
        return await self._decision_loop(context)
    
    def evaluate_intervention(self, context: AgentContext) -> tuple[bool, str]:
        return self._should_intervene, self._intervention_reason
    
    def set_intervention(self, should_intervene: bool, reason: str) -> None:
        self._should_intervene = should_intervene
        self._intervention_reason = reason