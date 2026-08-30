from __future__ import annotations
from datetime import timezone

import json
from typing import Any, Dict, List, Optional
import logging

from app.memory.store import SQLiteStore, ConversationRecord, SummaryRecord
from app.models.base import ModelAdapter, GenerationRequest, get_model_registry
from app.events.schemas import ConversationSummary

logger = logging.getLogger(__name__)


SUMMARIZATION_PROMPT = """You are a conversation summarizer. Analyze the following conversation segment and extract:

1. Main topic/theme
2. Key points discussed
3. Important facts discovered
4. Unresolved questions

Conversation:
{conversation}

Respond in JSON format:
{{
    "topic": "string",
    "key_points": ["string"],
    "important_facts": ["string"],
    "unresolved_questions": ["string"]
}}"""


class MemorySummarizer:
    def __init__(self, store: SQLiteStore, model_adapter: Optional[ModelAdapter] = None, vector_store: Optional[Any] = None):
        self.store = store
        self.model = model_adapter or get_model_registry().get()
        self.vector_store = vector_store
        self._summarization_interval = 10
    
    def set_interval(self, interval: int) -> None:
        self._summarization_interval = interval
    
    async def should_summarize(self, conversation_id: str, current_turn: int) -> bool:
        if current_turn < self._summarization_interval:
            return False
        
        latest_summary = self.store.get_latest_summary(conversation_id)
        last_summarized_turn = latest_summary.turn_end if latest_summary else 0
        
        return (current_turn - last_summarized_turn) >= self._summarization_interval
    
    async def summarize(self, conversation_id: str, current_turn: int) -> Optional[ConversationSummary]:
        latest_summary = self.store.get_latest_summary(conversation_id)
        start_turn = (latest_summary.turn_end + 1) if latest_summary else 1
        
        if start_turn > current_turn:
            return None
        
        messages = self.store.get_messages(conversation_id, limit=current_turn - start_turn + 1)
        messages = [m for m in messages if m.turn_number >= start_turn and m.turn_number <= current_turn]
        
        if not messages:
            return None
        
        conversation_text = "\n".join([
            f"[{msg.role}] Turn {msg.turn_number}: {msg.content}"
            for msg in messages
        ])
        
        request = GenerationRequest(
            prompt=SUMMARIZATION_PROMPT.format(conversation=conversation_text),
            max_tokens=512,
            temperature=0.3,
            stream=False
        )
        
        try:
            response = await self.model.generate(request)
            result = json.loads(response.text)
            
            summary_record = SummaryRecord(
                id=str(__import__('uuid').uuid4()),
                conversation_id=conversation_id,
                turn_start=start_turn,
                turn_end=current_turn,
                topic=result.get("topic", ""),
                key_points=result.get("key_points", []),
                unresolved_questions=result.get("unresolved_questions", []),
                important_facts=result.get("important_facts", []),
                created_at=__import__('datetime').datetime.now(timezone.utc).isoformat()
            )
            
            self.store.save_summary(summary_record)
            
            # Index the summary in Vector Database (RAG)
            if self.vector_store:
                summary_content = f"Topic: {summary_record.topic}\nKey points: {', '.join(summary_record.key_points)}\nImportant facts: {', '.join(summary_record.important_facts)}"
                metadata = {
                    "type": "conversation_summary",
                    "conversation_id": conversation_id,
                    "turn_start": start_turn,
                    "turn_end": current_turn,
                    "topic": summary_record.topic
                }
                # Support both sync and async add_memory
                if hasattr(self.vector_store, 'add_memory_async'):
                    await self.vector_store.add_memory_async(summary_record.id, summary_content, metadata)
                else:
                    self.vector_store.add_memory(summary_record.id, summary_content, metadata)
            
            return ConversationSummary(
                conversation_id=conversation_id,
                turn_count=current_turn,
                topic=summary_record.topic,
                key_points=summary_record.key_points,
                unresolved_questions=summary_record.unresolved_questions,
                important_facts=summary_record.important_facts
            )
            
        except json.JSONDecodeError:
            logger.error("Failed to parse summarization response")
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
        
        return None
    
    def build_context(self, conversation_id: str, current_turn: int, short_term_turns: int = 8) -> Dict[str, Any]:
        recent_messages = self.store.get_messages(conversation_id, limit=short_term_turns)
        latest_summary = self.store.get_latest_summary(conversation_id)
        all_summaries = self.store.get_all_summaries(conversation_id)
        important_facts = self.store.get_memory(conversation_id, type_filter="fact", limit=20)
        open_questions = self.store.get_memory(conversation_id, type_filter="question", limit=20)
        
        summary_text = ""
        if latest_summary:
            summary_text = f"Previous summary (turns {latest_summary.turn_start}-{latest_summary.turn_end}):\n"
            summary_text += f"Topic: {latest_summary.topic}\n"
            if latest_summary.key_points:
                summary_text += "Key points: " + "; ".join(latest_summary.key_points) + "\n"
            if latest_summary.important_facts:
                summary_text += "Important facts: " + "; ".join(latest_summary.important_facts) + "\n"
            if latest_summary.unresolved_questions:
                summary_text += "Unresolved: " + "; ".join(latest_summary.unresolved_questions) + "\n"
        
        if all_summaries and len(all_summaries) > 1:
            summary_text += "\nEarlier summaries:\n"
            for s in all_summaries[:-1]:
                summary_text += f"- Turns {s.turn_start}-{s.turn_end}: {s.topic}\n"
        
        if important_facts:
            summary_text += "\nImportant facts:\n"
            for f in important_facts:
                summary_text += f"- {f.content}\n"
        
        if open_questions:
            summary_text += "\nOpen questions:\n"
            for q in open_questions:
                summary_text += f"- {q.content}\n"
        
        return {
            "recent_messages": recent_messages,
            "summary": summary_text,
            "latest_summary": latest_summary,
            "important_facts": [f.content for f in important_facts],
            "open_questions": [q.content for q in open_questions]
        }