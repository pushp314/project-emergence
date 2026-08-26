from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.models.base import ModelAdapter, get_model_registry

logger = logging.getLogger(__name__)


@dataclass
class ModelCapability:
    model_id: str
    name: str
    capabilities: List[str] = field(default_factory=list)
    max_context: int = 4096
    max_output: int = 1024
    estimated_latency_ms: float = 100.0
    estimated_ram_mb: float = 500.0
    specialization: str = "general"
    loaded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCapability:
    tool_id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    permission_required: str = "read"
    risk_level: str = "low"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    agent_id: str
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    preferred_models: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityRequest:
    request_id: str
    agent_id: str
    capability: str
    reason: str
    objective: str
    context: str
    priority: str = "normal"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"


@dataclass
class CapabilityResult:
    request_id: str
    capability: str
    selected_implementation: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        model_registry=None
    ):
        self.event_bus = event_bus or get_event_bus()
        self.model_registry = model_registry or get_model_registry()
        self._models: Dict[str, ModelCapability] = {}
        self._tools: Dict[str, ToolCapability] = {}
        self._agents: Dict[str, AgentCapability] = {}
        self._request_handlers: Dict[str, Callable[[CapabilityRequest], Awaitable[CapabilityResult]]] = {}
        self._routing_history: List[Dict[str, Any]] = []
        self._max_history = 1000
    
    def register_model(self, capability: ModelCapability) -> None:
        self._models[capability.model_id] = capability
        logger.info(f"Registered model capability: {capability.model_id}")
    
    def register_tool(self, capability: ToolCapability) -> None:
        self._tools[capability.tool_id] = capability
        logger.info(f"Registered tool capability: {capability.tool_id}")
    
    def register_agent(self, capability: AgentCapability) -> None:
        self._agents[capability.agent_id] = capability
        logger.info(f"Registered agent capability: {capability.agent_id}")
    
    def get_model(self, model_id: str) -> Optional[ModelCapability]:
        return self._models.get(model_id)
    
    def get_tool(self, tool_id: str) -> Optional[ToolCapability]:
        return self._tools.get(tool_id)
    
    def get_agent(self, agent_id: str) -> Optional[AgentCapability]:
        return self._agents.get(agent_id)
    
    def find_models_by_capability(self, capability: str) -> List[ModelCapability]:
        return [m for m in self._models.values() if capability in m.capabilities]
    
    def find_tools_by_capability(self, capability: str) -> List[ToolCapability]:
        return [t for t in self._tools.values() if capability in t.capabilities]
    
    def list_models(self) -> List[ModelCapability]:
        return list(self._models.values())
    
    def list_tools(self) -> List[ToolCapability]:
        return list(self._tools.values())
    
    def list_agents(self) -> List[AgentCapability]:
        return list(self._agents.values())
    
    def register_request_handler(self, capability: str, handler: Callable[[CapabilityRequest], Awaitable[CapabilityResult]]) -> None:
        self._request_handlers[capability] = handler
    
    async def request_capability(self, request: CapabilityRequest) -> CapabilityResult:
        start_time = time.time()
        
        handlers = self._request_handlers.get(request.capability, [])
        
        if not handlers:
            return CapabilityResult(
                request_id=request.request_id,
                capability=request.capability,
                selected_implementation="",
                success=False,
                error=f"No handler registered for capability: {request.capability}",
                latency_ms=(time.time() - start_time) * 1000
            )
        
        for handler in handlers:
            try:
                result = await handler(request)
                self._record_routing(request, result)
                return result
            except Exception as e:
                logger.error(f"Capability handler error: {e}")
                continue
        
        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            selected_implementation="",
            success=False,
            error="All handlers failed",
            latency_ms=(time.time() - start_time) * 1000
        )
    
    def _record_routing(self, request: CapabilityRequest, result: CapabilityResult) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "capability": request.capability,
            "selected": result.selected_implementation,
            "success": result.success,
            "latency_ms": result.latency_ms,
            "reason": request.reason
        }
        
        self._routing_history.append(record)
        if len(self._routing_history) > self._max_history:
            self._routing_history.pop(0)
    
    def get_routing_history(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        history = self._routing_history
        if agent_id:
            history = [r for r in history if r.get("agent_id") == agent_id]
        return history[-limit:]
    
    def get_performance_stats(self, capability: Optional[str] = None) -> Dict[str, Any]:
        history = self._routing_history
        if capability:
            history = [r for r in history if r.get("capability") == capability]
        
        if not history:
            return {}
        
        total = len(history)
        successful = sum(1 for r in history if r.get("success"))
        avg_latency = sum(r.get("latency_ms", 0) for r in history) / total
        
        return {
            "total_requests": total,
            "success_rate": successful / total if total > 0 else 0,
            "avg_latency_ms": avg_latency,
            "capability": capability or "all"
        }


DEFAULT_MODEL_CAPABILITIES = {
    "qwen3-8b": ModelCapability(
        model_id="qwen3-8b",
        name="Qwen3 8B",
        capabilities=["general_reasoning", "research", "conversation", "analysis"],
        max_context=8192,
        max_output=2048,
        estimated_latency_ms=100.0,
        estimated_ram_mb=800.0,
        specialization="general"
    ),
    "qwen2.5-coder-7b": ModelCapability(
        model_id="qwen2.5-coder-7b",
        name="Qwen2.5 Coder 7B",
        capabilities=["programming", "code_analysis", "debugging", "code_generation"],
        max_context=8192,
        max_output=2048,
        estimated_latency_ms=150.0,
        estimated_ram_mb=800.0,
        specialization="coding"
    ),
    "deepseek-r1-7b": ModelCapability(
        model_id="deepseek-r1-7b",
        name="DeepSeek R1 7B",
        capabilities=["deep_reasoning", "criticism", "analysis", "math", "logic"],
        max_context=8192,
        max_output=2048,
        estimated_latency_ms=200.0,
        estimated_ram_mb=800.0,
        specialization="reasoning"
    ),
    "dolphin3-cyber-8b": ModelCapability(
        model_id="dolphin3-cyber-8b",
        name="Dolphin3 Cyber 8B",
        capabilities=["cybersecurity", "security_analysis", "vulnerability_research"],
        max_context=8192,
        max_output=2048,
        estimated_latency_ms=150.0,
        estimated_ram_mb=800.0,
        specialization="security"
    ),
    "dolphin-llama3-8b": ModelCapability(
        model_id="dolphin-llama3-8b",
        name="Dolphin Llama3 8B",
        capabilities=["general_reasoning", "conversation", "creative_writing"],
        max_context=8192,
        max_output=2048,
        estimated_latency_ms=100.0,
        estimated_ram_mb=800.0,
        specialization="general"
    ),
}


DEFAULT_TOOL_CAPABILITIES = {
    "terminal": ToolCapability(
        tool_id="terminal",
        name="Terminal",
        description="Execute shell commands",
        capabilities=["execute", "system_operations", "file_operations"],
        permission_required="execute",
        risk_level="high"
    ),
    "filesystem": ToolCapability(
        tool_id="filesystem",
        name="Filesystem",
        description="Read, write, and manipulate files",
        capabilities=["read", "write", "list", "search"],
        permission_required="write",
        risk_level="medium"
    ),
    "web": ToolCapability(
        tool_id="web",
        name="Web Browser",
        description="Search and browse the web",
        capabilities=["search", "browse", "extract", "research"],
        permission_required="network",
        risk_level="medium"
    ),
}


DEFAULT_AGENT_CAPABILITIES = {
    "agent_a": AgentCapability(
        agent_id="agent_a",
        name="Agent A - Explorer",
        role="explorer",
        capabilities=["explore", "research", "hypothesis_generation", "browser_research"],
        preferred_models=["qwen3-8b", "qwen2.5-coder-7b"],
        available_tools=["terminal", "filesystem", "web"]
    ),
    "agent_b": AgentCapability(
        agent_id="agent_b",
        name="Agent B - Challenger",
        role="challenger",
        capabilities=["critique", "verification", "deep_reasoning", "assumption_testing"],
        preferred_models=["deepseek-r1-7b", "qwen3-8b"],
        available_tools=["terminal", "filesystem", "web"]
    ),
    "agent_c": AgentCapability(
        agent_id="agent_c",
        name="Agent C - Observer",
        role="observer",
        capabilities=["monitoring", "pattern_detection", "intervention"],
        preferred_models=["qwen3-8b"],
        available_tools=[]
    ),
}


_capability_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    global _capability_registry
    if _capability_registry is None:
        registry = CapabilityRegistry()
        
        for model in DEFAULT_MODEL_CAPABILITIES.values():
            registry.register_model(model)
        
        for tool in DEFAULT_TOOL_CAPABILITIES.values():
            registry.register_tool(tool)
        
        for agent in DEFAULT_AGENT_CAPABILITIES.values():
            registry.register_agent(agent)
        
        _capability_registry = registry
    
    return _capability_registry


def set_capability_registry(registry: CapabilityRegistry) -> None:
    global _capability_registry
    _capability_registry = registry