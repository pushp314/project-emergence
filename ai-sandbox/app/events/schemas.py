from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    INSTALL = "install"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    EXPLORER = "explorer"
    CHALLENGER = "challenger"
    OBSERVER = "observer"


class ConversationState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    GENERATING = "generating"
    SPEAKING = "speaking"
    OBSERVING = "observing"
    NEXT_TURN = "next_turn"
    PAUSED = "paused"
    PROCESS_HUMAN_INPUT = "process_human_input"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"


class ToolPermission(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_PERMISSION = "requires_permission"
    DENIED = "denied"


@dataclass
class AgentConfig:
    role: AgentRole
    name: str
    system_prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024


@dataclass
class AgentMessage:
    agent_id: str
    role: AgentRole
    content: str
    turn_number: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    permission: PermissionLevel
    risk: RiskLevel
    enabled: bool = True


@dataclass
class ToolCall:
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ToolResult:
    call_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PermissionRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    action: str = ""
    command: str = ""
    reason: str = ""
    risk: RiskLevel = RiskLevel.MEDIUM
    scope: PermissionLevel = PermissionLevel.READ
    duration: str = "once"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"


@dataclass
class PermissionDecision:
    request_id: str
    approved: bool
    decided_by: str = "human"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class MemoryEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    importance: float = 1.0


@dataclass
class ConversationSummary:
    conversation_id: str
    turn_count: int
    topic: str
    key_points: List[str]
    unresolved_questions: List[str]
    important_facts: List[str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResourceMetrics:
    ram_used_gb: float
    ram_total_gb: float
    cpu_percent: float
    gpu_percent: float = 0.0
    generation_latency_ms: float = 0.0
    active_model: str = ""
    queue_length: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResourceThresholds:
    memory_warning_gb: float = 12.0
    memory_critical_gb: float = 14.0
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    latency_warning_ms: float = 5000.0


@dataclass
class ObserverState:
    current_topic: str = ""
    important_discoveries: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    repetition_score: float = 0.0
    conversation_health: float = 1.0
    last_intervention_turn: int = 0