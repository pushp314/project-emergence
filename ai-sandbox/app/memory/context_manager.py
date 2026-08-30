from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import uuid
from datetime import datetime, timezone

from app.memory.store import SQLiteStore, ConversationRecord
from app.events.bus import get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class ContextSnapshot:
    conversation_id: str
    turn_number: int
    recent_messages: List[Dict[str, Any]]
    summary: str
    important_facts: List[str]
    open_questions: List[str]
    current_topic: str
    role_distribution: Dict[str, int]
    evidence_summary: Dict[str, int]
    resource_state: str = "GREEN"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "turn_number": self.turn_number,
            "recent_messages": self.recent_messages,
            "summary": self.summary,
            "important_facts": self.important_facts,
            "open_questions": self.open_questions,
            "current_topic": self.current_topic,
            "role_distribution": self.role_distribution,
            "evidence_summary": self.evidence_summary,
            "resource_state": self.resource_state,
            "timestamp": self.timestamp,
        }


@dataclass
class ContextBudget:
    max_context_tokens: int = 8192
    max_recent_turns: int = 12
    summary_interval: int = 10
    yellow_reduction: float = 0.85
    orange_reduction: float = 0.70
    red_reduction: float = 0.0

    def adjusted_budget(self, resource_state: str) -> int:
        if resource_state == "ORANGE":
            return int(self.max_context_tokens * self.orange_reduction)
        elif resource_state == "YELLOW":
            return int(self.max_context_tokens * self.yellow_reduction)
        elif resource_state == "RED":
            return 0
        return self.max_context_tokens


@dataclass
class ContextState:
    conversation_id: str
    total_turns: int = 0
    summarized_turns: int = 0
    current_topic: str = ""
    important_facts: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    role_distribution: Dict[str, int] = field(default_factory=dict)
    evidence_counts: Dict[str, int] = field(default_factory=dict)
    last_summarized_turn: int = 0


class ContextManager:
    def __init__(
        self,
        store,
        summarizer,
        event_bus=None,
        vector_store=None,
        max_context_tokens: int = 8192,
        summarization_interval: int = 10
    ):
        self.store = store
        self.summarizer = summarizer
        self.event_bus = event_bus or get_event_bus()
        self.vector_store = vector_store
        self.max_context_tokens = max_context_tokens
        self.summarization_interval = summarization_interval
        self.state: Optional[ContextState] = None

    def set_conversation(self, conversation_id: str) -> None:
        self.state = ContextState(conversation_id=conversation_id)
        logger.info(f"ContextManager set for conversation {conversation_id}")

    def get_state(self) -> Optional[ContextState]:
        return self.state

    async def update_from_message(self, message: Any, current_turn: int) -> ContextSnapshot:
        if not self.state:
            logger.warning("ContextManager not associated with a conversation")
            return ContextSnapshot(
                conversation_id="",
                turn_number=current_turn,
                recent_messages=[],
                summary="",
                important_facts=[],
                open_questions=[],
                current_topic="",
                role_distribution={},
                evidence_summary={},
                resource_state="GREEN",
            )

        # Record the message
        msg_id = str(uuid.uuid4())
        await self.store.save_message_async(ConversationRecord(
            id=msg_id,
            conversation_id=self.state.conversation_id,
            turn_number=current_turn,
            agent_id=getattr(message, "agent_id", ""),
            role=getattr(message, "agent_identity", "unknown"),
            content=getattr(message, "content", ""),
            timestamp=getattr(message, "timestamp", datetime.now(timezone.utc).isoformat()),
            metadata=getattr(message, "metadata", {}),
        ))
        
        if self.vector_store and getattr(message, "content", ""):
            await self.vector_store.add_memory_async(
                memory_id=msg_id,
                content=getattr(message, "content", ""),
                metadata={
                    "conversation_id": self.state.conversation_id,
                    "type": "message",
                    "role": getattr(message, "agent_identity", "unknown"),
                    "turn": current_turn
                }
            )

        # Update state
        self.state.total_turns = current_turn
        self.state.role_distribution[getattr(message, "agent_identity", "unknown")] = (
            self.state.role_distribution.get(getattr(message, "agent_identity", "unknown"), 0) + 1
        )

        # Track evidence types
        evidence_type = getattr(message, "evidence_type", None) or getattr(message, "type", None)
        if evidence_type:
            etype = str(evidence_type)
            self.state.evidence_counts[etype] = self.state.evidence_counts.get(etype, 0) + 1

        # Extract context using summarizer
        context = self.summarizer.build_context(
            self.state.conversation_id,
            current_turn,
            short_term_turns=self.summarization_interval
        )

        # Get memory entries
        important_facts = await self.store.get_memory_async(
            self.state.conversation_id, type_filter="fact", limit=20
        )
        open_questions = await self.store.get_memory_async(
            self.state.conversation_id, type_filter="question", limit=20
        )
        
        # Vector memory augmentation
        semantic_memories = []
        if self.vector_store and getattr(message, "content", ""):
            results = await self.vector_store.query_memories_async(
                query=getattr(message, "content", ""),
                n_results=3,
                where={"conversation_id": self.state.conversation_id}
            )
            semantic_memories = [r["content"] for r in results]
            important_facts.extend([type("obj", (object,), {"content": c}) for c in semantic_memories])

        # Build snapshot
        recent_messages = []
        for msg in context.get("recent_messages", []):
            recent_messages.append({
                "role": getattr(msg, "role", "unknown"),
                "content": getattr(msg, "content", "")[:200],
                "turn_number": getattr(msg, "turn_number", 0),
            })

        snapshot = ContextSnapshot(
            conversation_id=self.state.conversation_id,
            turn_number=current_turn,
            recent_messages=recent_messages,
            summary=context.get("summary", ""),
            important_facts=[f.content for f in important_facts],
            open_questions=[q.content for q in open_questions],
            current_topic=context.get("latest_summary").topic if context.get("latest_summary") else "",
            role_distribution=self.state.role_distribution,
            evidence_summary=self.state.evidence_counts,
            resource_state="GREEN",
        )

        # Check if we should summarize
        if current_turn % self.summarization_interval == 0:
            await self._perform_summarization(current_turn)

        return snapshot

    async def _perform_summarization(self, current_turn: int) -> None:
        if not self.state:
            return

        summary = await self.summarizer.summarize(
            self.state.conversation_id, current_turn
        )

        if summary:
            self.state.summarized_turns = current_turn
            self.state.current_topic = summary.topic
            self.state.important_facts = summary.important_facts
            self.state.open_questions = summary.unresolved_questions
            self.state.last_summarized_turn = current_turn

            await self.event_bus.publish_type(
                "context.summarized",
                self.state.conversation_id,
                {
                    "summary_id": summary.id,
                    "turn_start": summary.turn_start,
                    "turn_end": summary.turn_end,
                    "topic": summary.topic,
                    "key_points": summary.key_points,
                    "important_facts": summary.important_facts,
                    "unresolved_questions": summary.unresolved_questions,
                }
            )

            logger.info(f"Context summarized at turn {current_turn}: topic={summary.topic}")

    async def get_context_for_llm(self, resource_state: str = "GREEN") -> Dict[str, Any]:
        if not self.state:
            return {"recent_messages": [], "summary": ""}

        # Get adjusted budget based on resource state
        budget = self.max_context_tokens
        if resource_state in ("YELLOW", "ORANGE", "RED"):
            budget = self._budget_adjusted(resource_state)

        # Get recent messages and summary
        recent_messages = self.store.get_messages(
            self.state.conversation_id, limit=self.summarization_interval
        )
        latest_summary = self.store.get_latest_summary(self.state.conversation_id)
        all_summaries = self.store.get_all_summaries(self.state.conversation_id)
        important_facts = self.store.get_memory(
            self.state.conversation_id, type_filter="fact", limit=20
        )
        open_questions = self.store.get_memory(
            self.state.conversation_id, type_filter="question", limit=20
        )

        # Build context text
        context_parts = []

        if latest_summary:
            context_parts.append(f"Current conversation topic: {latest_summary.topic}")
            if latest_summary.key_points:
                context_parts.append(f"Key points: {'; '.join(latest_summary.key_points)}")
            if latest_summary.important_facts:
                context_parts.append(f"Important facts: {'; '.join(latest_summary.important_facts)}")
            if latest_summary.unresolved_questions:
                context_parts.append(f"Unresolved questions: {'; '.join(latest_summary.unresolved_questions)}")

        context_parts.append(f"\nRecent turns (last {min(self.summarization_interval, self.state.total_turns)} turns):")
        for msg in recent_messages:
            role = getattr(msg, "role", "unknown")
            content = getattr(msg, "content", "")[:500]
            context_parts.append(f"[{role}] Turn {getattr(msg, 'turn_number', 0)}: {content}")

        if important_facts:
            context_parts.append(f"\nImportant facts ({len(important_facts)}):")
            for f in important_facts:
                context_parts.append(f"  - {f.content[:300]}")

        if open_questions:
            context_parts.append(f"\nOpen questions ({len(open_questions)}):")
            for q in open_questions:
                context_parts.append(f"  - {q.content[:300]}")

        # Apply budget constraint
        context_text = "\n".join(context_parts)
        if len(context_text) > budget:
            context_text = context_text[:budget] + "..."

        return {
            "recent_messages": recent_messages,
            "summary": context_text,
            "current_topic": latest_summary.topic if latest_summary else "",
            "important_facts": [f.content for f in important_facts],
            "open_questions": [q.content for q in open_questions],
            "resource_state": resource_state,
            "budget_used": len(context_text),
            "budget_total": budget,
        }

    def _budget_adjusted(self, resource_state: str) -> int:
        if resource_state == "ORANGE":
            return int(self.max_context_tokens * 0.70)
        elif resource_state == "YELLOW":
            return int(self.max_context_tokens * 0.85)
        elif resource_state == "RED":
            return 0
        return self.max_context_tokens

    async def get_context_summary(self) -> Dict[str, Any]:
        if not self.state:
            return {}

        latest_summary = self.store.get_latest_summary(self.state.conversation_id)
        important_facts = self.store.get_memory(
            self.state.conversation_id, type_filter="fact", limit=20
        )
        open_questions = self.store.get_memory(
            self.state.conversation_id, type_filter="question", limit=20
        )
        role_dist = self.state.role_distribution if self.state else {}

        return {
            "conversation_id": self.state.conversation_id,
            "total_turns": self.state.total_turns,
            "summarized_turns": self.state.summarized_turns,
            "current_topic": latest_summary.topic if latest_summary else "",
            "important_facts_count": len(important_facts),
            "open_questions_count": len(open_questions),
            "role_distribution": role_dist,
            "evidence_counts": self.state.evidence_counts if self.state else {},
            "last_summarized_turn": self.state.last_summarized_turn if self.state else 0,
        }

    async def reset(self) -> None:
        self.state = ContextState(conversation_id="")
        logger.info("ContextManager reset")