from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional
import asyncio
import logging

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import AgentConfig, AgentMessage, ToolCall, ToolResult, PermissionRequest
from app.models.base import ModelAdapter, GenerationRequest, GenerationResponse, get_model_registry

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
            messages.append({"role": role, "content": f"[{msg.role.value}] {msg.content}"})
        
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


class ExplorerAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
    
    async def think(self, context: AgentContext) -> str:
        return await self.generate_response(context)


class ChallengerAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
    
    async def think(self, context: AgentContext) -> str:
        return await self.generate_response(context)


class ObserverAgent(BaseAgent):
    def __init__(self, agent_id: str, config: AgentConfig, event_bus: Optional[EventBus] = None, model_adapter: Optional[ModelAdapter] = None):
        super().__init__(agent_id, config, event_bus, model_adapter)
        self._should_intervene = False
        self._intervention_reason = ""
    
    async def think(self, context: AgentContext) -> str:
        return await self.generate_response(context)
    
    def evaluate_intervention(self, context: AgentContext) -> tuple[bool, str]:
        return self._should_intervene, self._intervention_reason
    
    def set_intervention(self, should_intervene: bool, reason: str) -> None:
        self._should_intervene = should_intervene
        self._intervention_reason = reason