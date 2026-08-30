from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
import uuid
from datetime import datetime, timezone
from app.memory.store import SQLiteStore, ConversationRecord, MemoryRecord
from app.memory.summarizer import MemorySummarizer
from app.memory.context_manager import ContextManager, ContextSnapshot, ContextBudget, ContextState
from app.events.schemas import AgentMessage, MemoryEntry, ConversationSummary
from app.events.bus import EventBus, EventType, get_event_bus

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(
        self,
        store: SQLiteStore,
        summarizer: MemorySummarizer,
        event_bus: Optional[EventBus] = None,
        max_entries: int = 1000
    ):
        self.store = store
        self.summarizer = summarizer
        self.event_bus = event_bus or get_event_bus()
        self.max_entries = max_entries
        self.context_manager = ContextManager(
            store=self.store,
            summarizer=self.summarizer,
            event_bus=self.event_bus,
            max_context_tokens=8192,
            summarization_interval=self._summarization_interval if hasattr(self, '_summarization_interval') else 10
        )
        self._conversation_id: Optional[str] = None
    
    def set_conversation(self, conversation_id: str) -> None:
        self._conversation_id = conversation_id
    
    @property
    def conversation_id(self) -> Optional[str]:
        return self._conversation_id
    
    async def record_message(self, message: AgentMessage) -> None:
        if not self._conversation_id:
            return
        
        record = ConversationRecord(
            id=str(uuid.uuid4()),
            conversation_id=self._conversation_id,
            turn_number=message.turn_number,
            agent_id=message.agent_id,
            role=message.agent_identity,
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata
        )
        self.store.save_message(record)
        
        await self._maybe_extract_memory(message)
        
        await self.event_bus.publish_type(
            EventType.MEMORY_UPDATED,
            self._conversation_id,
            {"type": "message", "turn": message.turn_number}
        )
    
    async def _maybe_extract_memory(self, message: AgentMessage) -> None:
        content_lower = message.content.lower()
        
        if any(kw in content_lower for kw in ["discovered", "found", "learned", "important", "key insight", "conclusion"]):
            await self.add_memory(
                type="fact",
                content=message.content[:500],
                importance=0.8,
                metadata={"source_agent": message.agent_id, "turn": message.turn_number}
            )
        
        if "?" in message.content and any(kw in content_lower for kw in ["wonder", "question", "unclear", "don't know", "unsure"]):
            await self.add_memory(
                type="question",
                content=message.content[:500],
                importance=0.7,
                metadata={"source_agent": message.agent_id, "turn": message.turn_number}
            )
    
    async def add_memory(
        self,
        type: str,
        content: str,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        if not self._conversation_id:
            return ""
        
        entry_id = str(uuid.uuid4())
        record = MemoryRecord(
            id=entry_id,
            conversation_id=self._conversation_id,
            type=type,
            content=content,
            importance=importance,
            metadata=metadata or {},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.store.save_memory(record)
        
        await self.event_bus.publish_type(
            EventType.MEMORY_UPDATED,
            self._conversation_id,
            {"type": type, "entry_id": entry_id}
        )
        
        return entry_id
    
    async def get_context(self, current_turn: int, short_term_turns: int = 8) -> Dict[str, Any]:
        if not self._conversation_id:
            return {"recent_messages": [], "summary": ""}
        
        return self.summarizer.build_context(self._conversation_id, current_turn, short_term_turns)
    
    async def maybe_summarize(self, current_turn: int) -> Optional[ConversationSummary]:
        if not self._conversation_id:
            return None
        
        if await self.summarizer.should_summarize(self._conversation_id, current_turn):
            logger.info(f"Summarizing conversation {self._conversation_id} at turn {current_turn}")
            return await self.summarizer.summarize(self._conversation_id, current_turn)
        
        return None
    
    def get_memory_entries(self, type_filter: Optional[str] = None, limit: int = 100) -> List[MemoryEntry]:
        if not self._conversation_id:
            return []
        
        records = self.store.get_memory(self._conversation_id, type_filter, limit)
        return [
            MemoryEntry(
                entry_id=r.id,
                type=r.type,
                content=r.content,
                metadata=r.metadata,
                timestamp=r.timestamp,
                importance=r.importance
            )
            for r in records
        ]
    
    def get_conversation_state(self) -> Optional[Dict[str, Any]]:
        if not self._conversation_id:
            return None
        return self.store.load_state(self._conversation_id)
    
    def save_conversation_state(self, current_turn: int, current_topic: str, state_data: Dict[str, Any]) -> None:
        if not self._conversation_id:
            return
        self.store.save_state(self._conversation_id, current_turn, current_topic, state_data)
    
    async def recover_conversation(self, conversation_id: str) -> Dict[str, Any]:
        self._conversation_id = conversation_id
        state = self.store.load_state(conversation_id)
        message_count = self.store.get_message_count(conversation_id)
        latest_summary = self.store.get_latest_summary(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "message_count": message_count,
            "current_turn": state["current_turn"] if state else 0,
            "current_topic": state["current_topic"] if state else "",
            "state_data": state["state_data"] if state else {},
            "has_summary": latest_summary is not None
        }