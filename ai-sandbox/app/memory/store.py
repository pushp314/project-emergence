from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationRecord:
    id: str
    conversation_id: str
    turn_number: int
    agent_id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class MemoryRecord:
    id: str
    conversation_id: str
    type: str
    content: str
    importance: float
    metadata: Dict[str, Any]
    timestamp: str


@dataclass
class SummaryRecord:
    id: str
    conversation_id: str
    turn_start: int
    turn_end: int
    topic: str
    key_points: List[str]
    unresolved_questions: List[str]
    important_facts: List[str]
    created_at: str


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_conversations_cid_turn 
                ON conversations(conversation_id, turn_number);
                
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 1.0,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_memory_cid_type 
                ON memory(conversation_id, type);
                
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    turn_start INTEGER NOT NULL,
                    turn_end INTEGER NOT NULL,
                    topic TEXT,
                    key_points TEXT,
                    unresolved_questions TEXT,
                    important_facts TEXT,
                    created_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_summaries_cid 
                ON summaries(conversation_id);
                
                CREATE TABLE IF NOT EXISTS conversation_state (
                    conversation_id TEXT PRIMARY KEY,
                    current_turn INTEGER DEFAULT 0,
                    current_topic TEXT,
                    state_data TEXT,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.commit()
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_message(self, record: ConversationRecord) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO conversations (id, conversation_id, turn_number, agent_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.conversation_id, record.turn_number,
                record.agent_id, record.role, record.content,
                record.timestamp, json.dumps(record.metadata)
            ))
            conn.commit()
    
    def get_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> List[ConversationRecord]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM conversations
                WHERE conversation_id = ?
                ORDER BY turn_number DESC
                LIMIT ? OFFSET ?
            """, (conversation_id, limit, offset)).fetchall()
            
            return [ConversationRecord(
                id=r["id"], conversation_id=r["conversation_id"],
                turn_number=r["turn_number"], agent_id=r["agent_id"],
                role=r["role"], content=r["content"],
                timestamp=r["timestamp"], metadata=json.loads(r["metadata"] or "{}")
            ) for r in reversed(rows)]
    
    def get_message_count(self, conversation_id: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COUNT(*) as count FROM conversations WHERE conversation_id = ?
            """, (conversation_id,)).fetchone()
            return row["count"] if row else 0
    
    def save_memory(self, record: MemoryRecord) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO memory (id, conversation_id, type, content, importance, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.conversation_id, record.type,
                record.content, record.importance,
                json.dumps(record.metadata), record.timestamp
            ))
            conn.commit()
    
    def get_memory(self, conversation_id: str, type_filter: Optional[str] = None, limit: int = 100) -> List[MemoryRecord]:
        with self._get_conn() as conn:
            if type_filter:
                rows = conn.execute("""
                    SELECT * FROM memory
                    WHERE conversation_id = ? AND type = ?
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                """, (conversation_id, type_filter, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM memory
                    WHERE conversation_id = ?
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT ?
                """, (conversation_id, limit)).fetchall()
            
            return [MemoryRecord(
                id=r["id"], conversation_id=r["conversation_id"],
                type=r["type"], content=r["content"],
                importance=r["importance"], metadata=json.loads(r["metadata"] or "{}"),
                timestamp=r["timestamp"]
            ) for r in rows]
    
    def save_summary(self, record: SummaryRecord) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO summaries (id, conversation_id, turn_start, turn_end, topic, key_points, unresolved_questions, important_facts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.conversation_id, record.turn_start, record.turn_end,
                record.topic, json.dumps(record.key_points),
                json.dumps(record.unresolved_questions), json.dumps(record.important_facts),
                record.created_at
            ))
            conn.commit()
    
    def get_latest_summary(self, conversation_id: str) -> Optional[SummaryRecord]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM summaries
                WHERE conversation_id = ?
                ORDER BY turn_end DESC
                LIMIT 1
            """, (conversation_id,)).fetchone()
            
            if row:
                return SummaryRecord(
                    id=row["id"], conversation_id=row["conversation_id"],
                    turn_start=row["turn_start"], turn_end=row["turn_end"],
                    topic=row["topic"], key_points=json.loads(row["key_points"] or "[]"),
                    unresolved_questions=json.loads(row["unresolved_questions"] or "[]"),
                    important_facts=json.loads(row["important_facts"] or "[]"),
                    created_at=row["created_at"]
                )
            return None
    
    def get_all_summaries(self, conversation_id: str) -> List[SummaryRecord]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM summaries
                WHERE conversation_id = ?
                ORDER BY turn_start
            """, (conversation_id,)).fetchall()
            
            return [SummaryRecord(
                id=r["id"], conversation_id=r["conversation_id"],
                turn_start=r["turn_start"], turn_end=r["turn_end"],
                topic=r["topic"], key_points=json.loads(r["key_points"] or "[]"),
                unresolved_questions=json.loads(r["unresolved_questions"] or "[]"),
                important_facts=json.loads(r["important_facts"] or "[]"),
                created_at=r["created_at"]
            ) for r in rows]
    
    def save_state(self, conversation_id: str, current_turn: int, current_topic: str, state_data: Dict[str, Any]) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_state (conversation_id, current_turn, current_topic, state_data, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, current_turn, current_topic, json.dumps(state_data), datetime.utcnow().isoformat()))
            conn.commit()
    
    def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM conversation_state WHERE conversation_id = ?
            """, (conversation_id,)).fetchone()
            
            if row:
                return {
                    "current_turn": row["current_turn"],
                    "current_topic": row["current_topic"],
                    "state_data": json.loads(row["state_data"] or "{}"),
                    "updated_at": row["updated_at"]
                }
            return None
    
    def delete_conversation(self, conversation_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM memory WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM summaries WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversation_state WHERE conversation_id = ?", (conversation_id,))
            conn.commit()