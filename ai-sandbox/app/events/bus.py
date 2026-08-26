from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    AGENT_MESSAGE = "agent.message"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_ERROR = "agent.error"
    
    HUMAN_MESSAGE = "human.message"
    HUMAN_INTERRUPT = "human.interrupt"
    
    TOOL_REQUEST = "tool.request"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    
    PERMISSION_REQUEST = "permission.request"
    PERMISSION_APPROVED = "permission.approved"
    PERMISSION_DENIED = "permission.denied"
    
    MEMORY_UPDATED = "memory.updated"
    
    OBSERVER_INTERVENTION = "observer.intervention"
    
    RESOURCE_WARNING = "resource.warning"
    RESOURCE_CRITICAL = "resource.critical"
    
    SYSTEM_PAUSE = "system.pause"
    SYSTEM_RESUME = "system.resume"
    SYSTEM_STOP = "system.stop"
    
    CONVERSATION_TURN_START = "conversation.turn.start"
    CONVERSATION_TURN_END = "conversation.turn.end"
    CONVERSATION_SUMMARIZED = "conversation.summarized"


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.AGENT_MESSAGE
    conversation_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            "event_id": self.event_id,
            "type": self.type.value,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata
        })
    
    @classmethod
    def from_json(cls, data: str) -> Event:
        d = json.loads(data)
        return cls(
            event_id=d.get("event_id", str(uuid.uuid4())),
            type=EventType(d["type"]),
            conversation_id=d.get("conversation_id", ""),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat()),
            payload=d.get("payload", {}),
            metadata=d.get("metadata", {})
        )


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, Set[Callable[[Event], Any]]] = {}
        self._wildcard_subscribers: Set[Callable[[Event], Any]] = set()
        self._event_history: List[Event] = []
        self._max_history = 10000
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], Any]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)
        logger.debug(f"Subscribed {callback.__name__} to {event_type.value}")
    
    def subscribe_all(self, callback: Callable[[Event], Any]) -> None:
        self._wildcard_subscribers.add(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], Any]) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
    
    async def publish(self, event: Event) -> None:
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
        
        tasks = []
        
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(asyncio.create_task(callback(event)))
                else:
                    tasks.append(asyncio.create_task(asyncio.to_thread(callback, event)))
        
        for callback in self._wildcard_subscribers:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback(event)))
            else:
                tasks.append(asyncio.create_task(asyncio.to_thread(callback, event)))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def publish_type(self, event_type: EventType, conversation_id: str, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> None:
        event = Event(
            type=event_type,
            conversation_id=conversation_id,
            payload=payload,
            metadata=metadata or {}
        )
        await self.publish(event)
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        if event_type:
            return [e for e in self._event_history if e.type == event_type][-limit:]
        return self._event_history[-limit:]


_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    global _event_bus
    _event_bus = bus