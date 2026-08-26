from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import EvidenceType

logger = logging.getLogger(__name__)


class SessionStatus(str):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"
    FAILED = "FAILED"
    RECOVERABLE = "RECOVERABLE"


@dataclass
class SessionConfig:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    max_turns: int = 1000
    turn_timeout_seconds: int = 120
    short_term_turns: int = 8
    initial_speaker: str = "agent_a"
    scheduler_policy: str = "round_robin"
    model_config: Dict[str, Any] = field(default_factory=dict)
    resource_config: Dict[str, Any] = field(default_factory=dict)
    permissions_config: Dict[str, Any] = field(default_factory=dict)
    tools_config: Dict[str, Any] = field(default_factory=dict)
    autonomy_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    session_id: str
    session_number: int
    status: str
    current_turn: int
    current_speaker: str
    next_speaker: str
    agents: List[str]
    config: SessionConfig
    created_at: str
    updated_at: str
    recovery_data: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    def __init__(
        self,
        db_path: str = "./data/sandbox.db",
        event_bus: Optional[EventBus] = None,
        evidence_manager: Optional[Any] = None
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.event_bus = event_bus or get_event_bus()
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self._current_session: Optional[SessionState] = None
        self._session_counter = 0
        
        self._init_db()
    
    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_metadata (
                    session_id TEXT PRIMARY KEY,
                    session_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    configuration TEXT,
                    model_configuration TEXT,
                    project_version TEXT,
                    environment_metadata TEXT,
                    summary TEXT,
                    recovery_state TEXT,
                    current_turn INTEGER DEFAULT 0,
                    current_speaker TEXT,
                    next_speaker TEXT,
                    active_agents TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
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
    
    def _get_next_session_number(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT MAX(session_number) as max_num FROM session_metadata").fetchone()
            return (row["max_num"] or 0) + 1
    
    async def create_session(self, config: SessionConfig) -> SessionState:
        self._session_counter = self._get_next_session_number()
        
        import subprocess
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd="/Users/pushp/Desktop/A2A/ai-sandbox",
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            git_commit = "unknown"
        
        session = SessionState(
            session_id=config.session_id,
            session_number=self._session_counter,
            status=SessionStatus.RUNNING,
            current_turn=0,
            current_speaker=config.initial_speaker,
            next_speaker=config.initial_speaker,
            agents=["agent_a", "agent_b", "agent_c"],
            config=config,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO session_metadata (session_id, session_number, status, start_time, end_time,
                                             configuration, model_configuration, project_version,
                                             environment_metadata, recovery_state,
                                             current_turn, current_speaker, next_speaker,
                                             active_agents, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id, session.session_number, session.status,
                session.created_at, None,
                json.dumps(config.__dict__), json.dumps(config.model_config),
                git_commit, "{}", "{}",
                session.current_turn, session.current_speaker, session.next_speaker,
                json.dumps(session.agents), session.created_at, session.updated_at
            ))
            conn.commit()
        
        self._current_session = session
        
        await self.evidence_manager.start(config.session_id)
        
        await self.event_bus.publish_type(
            EventType.SYSTEM_RESUME,
            config.session_id,
            {"session_id": config.session_id, "session_number": session.session_number}
        )
        
        logger.info(f"Created session {config.session_id} (#{session.session_number})")
        return session
    
    async def update_session_state(
        self,
        current_turn: int,
        current_speaker: str,
        next_speaker: str,
        status: Optional[str] = None,
        recovery_data: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self._current_session:
            return
        
        session = self._current_session
        session.current_turn = current_turn
        session.current_speaker = current_speaker
        session.next_speaker = next_speaker
        session.updated_at = datetime.utcnow().isoformat()
        
        if status:
            session.status = status
        
        if recovery_data:
            session.recovery_data.update(recovery_data)
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE session_metadata SET status = ?, current_turn = ?, current_speaker = ?,
                                          next_speaker = ?, recovery_state = ?, updated_at = ?
                WHERE session_id = ?
            """, (session.status, session.current_turn, session.current_speaker,
                  session.next_speaker, json.dumps(session.recovery_data),
                  session.updated_at, session.session_id))
            conn.commit()
    
    async def pause_session(self) -> bool:
        if not self._current_session or self._current_session.status != SessionStatus.RUNNING:
            return False
        
        self._current_session.status = SessionStatus.PAUSED
        self._current_session.updated_at = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE session_metadata SET status = ?, updated_at = ? WHERE session_id = ?
            """, (SessionStatus.PAUSED, self._current_session.updated_at, self._current_session.session_id))
            conn.commit()
        
        await self.event_bus.publish_type(
            EventType.SYSTEM_PAUSE,
            self._current_session.session_id,
            {"session_id": self._current_session.session_id}
        )
        
        return True
    
    async def resume_session(self) -> bool:
        if not self._current_session or self._current_session.status != SessionStatus.PAUSED:
            return False
        
        self._current_session.status = SessionStatus.RUNNING
        self._current_session.updated_at = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE session_metadata SET status = ?, updated_at = ? WHERE session_id = ?
            """, (SessionStatus.RUNNING, self._current_session.updated_at, self._current_session.session_id))
            conn.commit()
        
        await self.event_bus.publish_type(
            EventType.SYSTEM_RESUME,
            self._current_session.session_id,
            {"session_id": self._current_session.session_id}
        )
        
        return True
    
    async def complete_session(self, status: str = SessionStatus.COMPLETED) -> None:
        if not self._current_session:
            return
        
        self._current_session.status = status
        self._current_session.updated_at = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE session_metadata SET status = ?, end_time = ?, updated_at = ?
                WHERE session_id = ?
            """, (status, datetime.utcnow().isoformat(), self._current_session.updated_at, self._current_session.session_id))
            conn.commit()
        
        await self.evidence_manager.stop()
        
        await self.event_bus.publish_type(
            EventType.SYSTEM_STOP,
            self._current_session.session_id,
            {"session_id": self._current_session.session_id, "final_status": status}
        )
        
        logger.info(f"Completed session {self._current_session.session_id} with status {status}")
    
    async def interrupt_session(self) -> bool:
        if not self._current_session:
            return False
        
        self._current_session.status = SessionStatus.INTERRUPTED
        self._current_session.updated_at = datetime.utcnow().isoformat()
        
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE session_metadata SET status = ?, updated_at = ? WHERE session_id = ?
            """, (SessionStatus.INTERRUPTED, self._current_session.updated_at, self._current_session.session_id))
            conn.commit()
        
        await self.event_bus.publish_type(
            EventType.HUMAN_INTERRUPT,
            self._current_session.session_id,
            {"session_id": self._current_session.session_id}
        )
        
        return True
    
    async def get_recoverable_sessions(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT session_id, session_number, status, start_time, end_time,
                       current_turn, current_speaker, recovery_state, updated_at
                FROM session_metadata
                WHERE status IN (?, ?, ?)
                ORDER BY session_number DESC
            """, (SessionStatus.INTERRUPTED, SessionStatus.PAUSED, SessionStatus.RECOVERABLE)).fetchall()
            
            return [dict(row) for row in rows]
    
    async def recover_session(self, session_id: str) -> Optional[SessionState]:
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM session_metadata WHERE session_id = ?
            """, (session_id,)).fetchone()
            
            if not row:
                return None
            
            recovery_state = json.loads(row["recovery_state"] or "{}")
            config_data = json.loads(row["configuration"] or "{}")
            config = SessionConfig(**config_data)
            config.session_id = session_id
            
            session = SessionState(
                session_id=row["session_id"],
                session_number=row["session_number"],
                status=SessionStatus.RECOVERABLE,
                current_turn=row["current_turn"],
                current_speaker=row["current_speaker"],
                next_speaker=row["next_speaker"],
                agents=json.loads(row["active_agents"] or "[]"),
                config=config,
                created_at=row["start_time"],
                updated_at=datetime.utcnow().isoformat(),
                recovery_data=recovery_state
            )
            
            self._current_session = session
            
            await self.evidence_manager.start(session_id)
            
            with self._get_conn() as conn:
                conn.execute("""
                    UPDATE session_metadata SET status = ?, updated_at = ? WHERE session_id = ?
                """, (SessionStatus.RUNNING, datetime.utcnow().isoformat(), session_id))
                conn.commit()
            
            await self.event_bus.publish_type(
                EventType.SYSTEM_RESUME,
                session_id,
                {"session_id": session_id, "recovered": True}
            )
            
            logger.info(f"Recovered session {session_id} from turn {session.current_turn}")
            return session
    
    async def get_session_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT session_id, session_number, status, start_time, end_time,
                       current_turn
                FROM session_metadata
                ORDER BY session_number DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_current_session(self) -> Optional[SessionState]:
        return self._current_session
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM session_metadata WHERE session_id = ?", (session_id,)).fetchone()
            return dict(row) if row else None


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def set_session_manager(manager: SessionManager) -> None:
    global _session_manager
    _session_manager = manager