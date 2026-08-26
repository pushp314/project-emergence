from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.evidence.schemas import (
    Evidence, EvidenceType, Source, Claim, ClaimType,
    ResearchSession, Experiment, Decision, Artifact,
    ModificationRecord, VerificationStatus
)

logger = logging.getLogger(__name__)


class EvidenceManager:
    def __init__(
        self,
        db_path: str = "./data/sandbox.db",
        event_bus: Optional[EventBus] = None,
        artifacts_dir: str = "./data/artifacts"
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.event_bus = event_bus or get_event_bus()
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
        self._subscribers: Dict[EventType, List[Callable[[Event], Awaitable[None]]]] = {}
        
        self._init_db()
        self._subscribe_to_events()
    
    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    intent TEXT,
                    reason TEXT,
                    action_details TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    permission_required INTEGER DEFAULT 0,
                    permission_id TEXT,
                    artifacts TEXT,
                    tags TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence(session_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_agent ON evidence(agent_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
                CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);
                
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    research_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    domain TEXT,
                    publisher TEXT,
                    retrieved_at TEXT NOT NULL,
                    content_reference TEXT,
                    content_hash TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_sources_research ON sources(research_id);
                
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    research_id TEXT NOT NULL,
                    source_id TEXT,
                    agent_id TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    verification_status TEXT DEFAULT 'pending',
                    supporting_evidence TEXT,
                    contradicting_evidence TEXT,
                    created_at TEXT NOT NULL,
                    verified_at TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_claims_research ON claims(research_id);
                CREATE INDEX IF NOT EXISTS idx_claims_agent ON claims(agent_id);
                
                CREATE TABLE IF NOT EXISTS research_sessions (
                    research_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    reason TEXT,
                    status TEXT DEFAULT 'pending',
                    sources TEXT,
                    claims TEXT,
                    conclusion TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_research_session ON research_sessions(session_id);
                CREATE INDEX IF NOT EXISTS idx_research_agent ON research_sessions(agent_id);
                
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    hypothesis TEXT,
                    proposed_procedure TEXT,
                    required_tools TEXT,
                    required_permissions TEXT,
                    status TEXT DEFAULT 'proposed',
                    baseline_reference TEXT,
                    result TEXT,
                    conclusion TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    artifacts TEXT,
                    metrics TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_experiments_session ON experiments(session_id);
                CREATE INDEX IF NOT EXISTS idx_experiments_agent ON experiments(agent_id);
                
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    evidence_considered TEXT,
                    alternatives TEXT,
                    resulting_action TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
                CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent_id);
                
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    created_by_action TEXT,
                    experiment_id TEXT,
                    research_id TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);
                CREATE INDEX IF NOT EXISTS idx_artifacts_experiment ON artifacts(experiment_id);
                
                CREATE TABLE IF NOT EXISTS modifications (
                    modification_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    proposal TEXT NOT NULL,
                    reason TEXT,
                    hypothesis TEXT,
                    expected_benefit TEXT,
                    expected_risk TEXT,
                    files_affected TEXT,
                    branch TEXT,
                    baseline_commit TEXT,
                    status TEXT DEFAULT 'proposed',
                    benchmark_before TEXT,
                    benchmark_after TEXT,
                    test_results TEXT,
                    approval TEXT,
                    applied_commit TEXT,
                    rollback_commit TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    evidence TEXT,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_modifications_session ON modifications(session_id);
                
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    session_number INTEGER,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    configuration TEXT,
                    model_configuration TEXT,
                    project_version TEXT,
                    environment_metadata TEXT,
                    summary TEXT,
                    recovery_state TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ram_used_gb REAL,
                    ram_total_gb REAL,
                    cpu_percent REAL,
                    gpu_percent REAL,
                    inference_latency_ms REAL,
                    tokens_per_second REAL,
                    context_tokens INTEGER,
                    active_agents INTEGER,
                    active_model TEXT,
                    queue_depth INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_session ON resource_metrics(session_id);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON resource_metrics(timestamp);
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
    
    def _subscribe_to_events(self) -> None:
        event_types = [
            EventType.AGENT_MESSAGE,
            EventType.TOOL_REQUEST,
            EventType.TOOL_STARTED,
            EventType.TOOL_COMPLETED,
            EventType.TOOL_FAILED,
            EventType.PERMISSION_REQUEST,
            EventType.PERMISSION_APPROVED,
            EventType.PERMISSION_DENIED,
            EventType.MEMORY_UPDATED,
            EventType.OBSERVER_INTERVENTION,
            EventType.RESOURCE_WARNING,
            EventType.RESOURCE_CRITICAL,
            EventType.SYSTEM_PAUSE,
            EventType.SYSTEM_RESUME,
            EventType.SYSTEM_STOP,
            EventType.HUMAN_INTERRUPT,
            EventType.HUMAN_MESSAGE,
        ]
        
        for event_type in event_types:
            self.event_bus.subscribe(event_type, self._on_event)
    
    async def _on_event(self, event: Event) -> None:
        await self._event_queue.put(event)
    
    async def start(self, session_id: str) -> None:
        if self._running:
            return
        
        self._session_id = session_id
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        
        await self._create_session_record(session_id)
        logger.info(f"Evidence Manager started for session {session_id}")
    
    async def stop(self) -> None:
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self._session_id:
            await self._complete_session_record(self._session_id)
        
        logger.info("Evidence Manager stopped")
    
    async def _process_events(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event) -> None:
        if not self._session_id:
            return
        
        handlers = {
            EventType.AGENT_MESSAGE: self._handle_agent_message,
            EventType.TOOL_REQUEST: self._handle_tool_request,
            EventType.TOOL_STARTED: self._handle_tool_started,
            EventType.TOOL_COMPLETED: self._handle_tool_completed,
            EventType.TOOL_FAILED: self._handle_tool_failed,
            EventType.PERMISSION_REQUEST: self._handle_permission_request,
            EventType.PERMISSION_APPROVED: self._handle_permission_approved,
            EventType.PERMISSION_DENIED: self._handle_permission_denied,
            EventType.OBSERVER_INTERVENTION: self._handle_observer_intervention,
            EventType.RESOURCE_WARNING: self._handle_resource_warning,
            EventType.RESOURCE_CRITICAL: self._handle_resource_critical,
            EventType.HUMAN_INTERRUPT: self._handle_human_interrupt,
            EventType.HUMAN_MESSAGE: self._handle_human_message,
            EventType.SYSTEM_PAUSE: self._handle_system_pause,
            EventType.SYSTEM_RESUME: self._handle_system_resume,
            EventType.SYSTEM_STOP: self._handle_system_stop,
        }
        
        handler = handlers.get(event.type)
        if handler:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error handling {event.type}: {e}")
    
    def _create_evidence(self, event: Event, evidence_type: EvidenceType, 
                        intent: str = "", reason: str = "",
                        action_details: Optional[Dict] = None,
                        input_data: Optional[Dict] = None,
                        output_data: Optional[Dict] = None,
                        permission_required: bool = False,
                        permission_id: Optional[str] = None,
                        artifacts: Optional[List[str]] = None,
                        tags: Optional[List[str]] = None) -> Evidence:
        
        agent_id = event.payload.get("agent_id", "unknown")
        correlation_id = event.payload.get("call_id", event.payload.get("request_id", ""))
        
        return Evidence(
            session_id=self._session_id or "",
            agent_id=agent_id,
            evidence_type=evidence_type,
            timestamp=event.timestamp,
            correlation_id=correlation_id,
            intent=intent,
            reason=reason,
            action_details=action_details or {},
            input_data=input_data or {},
            output_data=output_data or {},
            permission_required=permission_required,
            permission_id=permission_id,
            artifacts=artifacts or [],
            tags=tags or [],
            metadata={"event_type": event.type.value, "event_id": event.event_id}
        )
    
    def _save_evidence(self, evidence: Evidence) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO evidence (evidence_id, session_id, agent_id, evidence_type, timestamp,
                                     correlation_id, intent, reason, action_details, input_data,
                                     output_data, permission_required, permission_id, artifacts,
                                     tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence.evidence_id, evidence.session_id, evidence.agent_id,
                evidence.evidence_type.value, evidence.timestamp,
                evidence.correlation_id, evidence.intent, evidence.reason,
                json.dumps(evidence.action_details), json.dumps(evidence.input_data),
                json.dumps(evidence.output_data), int(evidence.permission_required),
                evidence.permission_id, json.dumps(evidence.artifacts),
                json.dumps(evidence.tags), json.dumps(evidence.metadata)
            ))
            conn.commit()
    
    async def _handle_agent_message(self, event: Event) -> None:
        content = event.payload.get("content", "")
        is_intervention = event.metadata.get("intervention", False)
        
        evidence = self._create_evidence(
            event,
            EvidenceType.OBSERVER_INTERVENTION if is_intervention else EvidenceType.AGENT_ACTION,
            intent="Agent communication",
            reason=f"Agent {event.payload.get('agent_id')} sent message",
            action_details={"content_preview": content[:200], "turn": event.payload.get("turn_number")},
            tags=["communication", "intervention"] if is_intervention else ["communication"]
        )
        self._save_evidence(evidence)
    
    async def _handle_tool_request(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.TOOL_CALL,
            intent="Tool request",
            reason=f"Agent requested tool: {event.payload.get('tool_name')}",
            action_details={"tool": event.payload.get("tool_name")},
            input_data=event.payload.get("arguments", {}),
            permission_required=event.payload.get("permission_required", False)
        )
        self._save_evidence(evidence)
    
    async def _handle_tool_started(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.TOOL_CALL,
            intent="Tool execution started",
            reason=f"Tool {event.payload.get('tool_name')} started",
            action_details={"tool": event.payload.get("tool_name")}
        )
        self._save_evidence(evidence)
    
    async def _handle_tool_completed(self, event: Event) -> None:
        result = event.payload.get("result")
        evidence = self._create_evidence(
            event,
            EvidenceType.TOOL_RESULT,
            intent="Tool completed successfully",
            reason=f"Tool {event.payload.get('tool_name')} completed",
            action_details={"tool": event.payload.get("tool_name")},
            output_data={"success": True, "result": str(result)[:500] if result else None},
            tags=["success"]
        )
        self._save_evidence(evidence)
    
    async def _handle_tool_failed(self, event: Event) -> None:
        error = event.payload.get("error")
        evidence = self._create_evidence(
            event,
            EvidenceType.TOOL_RESULT,
            intent="Tool failed",
            reason=f"Tool {event.payload.get('tool_name')} failed: {error}",
            action_details={"tool": event.payload.get("tool_name")},
            output_data={"success": False, "error": error},
            tags=["failure"]
        )
        self._save_evidence(evidence)
    
    async def _handle_permission_request(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.PERMISSION_REQUEST,
            intent="Permission requested",
            reason=event.payload.get("reason", ""),
            action_details={"action": event.payload.get("action"), "command": event.payload.get("command")},
            permission_required=True,
            permission_id=event.payload.get("request_id"),
            tags=["permission", "pending"]
        )
        self._save_evidence(evidence)
    
    async def _handle_permission_approved(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.PERMISSION_GRANTED,
            intent="Permission granted",
            reason=f"Permission {event.payload.get('request_id')} approved by {event.payload.get('decided_by', 'human')}",
            permission_id=event.payload.get("request_id"),
            tags=["permission", "approved"]
        )
        self._save_evidence(evidence)
    
    async def _handle_permission_denied(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.PERMISSION_DENIED,
            intent="Permission denied",
            reason=f"Permission {event.payload.get('request_id')} denied by {event.payload.get('decided_by', 'human')}: {event.payload.get('reason', '')}",
            permission_id=event.payload.get("request_id"),
            tags=["permission", "denied"]
        )
        self._save_evidence(evidence)
    
    async def _handle_observer_intervention(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.OBSERVER_INTERVENTION,
            intent="Observer intervention",
            reason=event.payload.get("reason", ""),
            action_details={"topic": event.payload.get("topic")},
            tags=["observer", "intervention"]
        )
        self._save_evidence(evidence)
    
    async def _handle_resource_warning(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.RESOURCE_WARNING,
            intent="Resource warning",
            reason=f"Resource warning: {event.payload.get('warnings', [])}",
            action_details=event.payload.get("metrics", {}),
            tags=["resource", "warning"]
        )
        self._save_evidence(evidence)
    
    async def _handle_resource_critical(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.RESOURCE_WARNING,
            intent="Resource critical",
            reason=f"Critical resource usage: {event.payload.get('warnings', [])}",
            action_details=event.payload.get("metrics", {}),
            tags=["resource", "critical"]
        )
        self._save_evidence(evidence)
    
    async def _handle_human_interrupt(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.HUMAN_INTERVENTION,
            intent="Human interrupt",
            reason="Human interrupted the conversation",
            tags=["human", "interrupt"]
        )
        self._save_evidence(evidence)
    
    async def _handle_human_message(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.HUMAN_INTERVENTION,
            intent="Human message",
            reason=f"Human sent message: {event.payload.get('content', '')[:100]}",
            action_details={"content": event.payload.get("content", "")},
            tags=["human", "message"]
        )
        self._save_evidence(evidence)
    
    async def _handle_system_pause(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.SYSTEM_ERROR,
            intent="System paused",
            reason="System paused by user or resource manager",
            tags=["system", "pause"]
        )
        self._save_evidence(evidence)
    
    async def _handle_system_resume(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.SYSTEM_ERROR,
            intent="System resumed",
            reason="System resumed from pause",
            tags=["system", "resume"]
        )
        self._save_evidence(evidence)
    
    async def _handle_system_stop(self, event: Event) -> None:
        evidence = self._create_evidence(
            event,
            EvidenceType.SYSTEM_ERROR,
            intent="System stopped",
            reason="System stopped",
            tags=["system", "stop"]
        )
        self._save_evidence(evidence)
    
    async def _create_session_record(self, session_id: str) -> None:
        import subprocess
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd="/Users/pushp/Desktop/A2A/ai-sandbox",
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            git_commit = "unknown"
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (session_id, session_number, status, start_time,
                                                configuration, model_configuration, project_version,
                                                environment_metadata, recovery_state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, 0, "RUNNING", datetime.utcnow().isoformat(),
                "{}", "{}", git_commit, "{}", "{}"
            ))
            conn.commit()
    
    async def _complete_session_record(self, session_id: str) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE sessions SET status = ?, end_time = ? WHERE session_id = ?
            """, ("COMPLETED", datetime.utcnow().isoformat(), session_id))
            conn.commit()
    
    def record_resource_metrics(self, metrics: Dict[str, Any]) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO resource_metrics (session_id, timestamp, ram_used_gb, ram_total_gb,
                                             cpu_percent, gpu_percent, inference_latency_ms,
                                             tokens_per_second, context_tokens, active_agents,
                                             active_model, queue_depth)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self._session_id, datetime.utcnow().isoformat(),
                metrics.get("ram_used_gb"), metrics.get("ram_total_gb"),
                metrics.get("cpu_percent"), metrics.get("gpu_percent"),
                metrics.get("inference_latency_ms"), metrics.get("tokens_per_second"),
                metrics.get("context_tokens"), metrics.get("active_agents"),
                metrics.get("active_model"), metrics.get("queue_depth")
            ))
            conn.commit()
    
    def record_decision(self, decision: Decision) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO decisions (decision_id, session_id, agent_id, decision, reason,
                                      evidence_considered, alternatives, resulting_action,
                                      timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id, decision.session_id, decision.agent_id,
                decision.decision, decision.reason,
                json.dumps(decision.evidence_considered), json.dumps(decision.alternatives),
                decision.resulting_action, decision.timestamp,
                json.dumps(decision.metadata)
            ))
            conn.commit()
    
    def record_artifact(self, artifact: Artifact) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO artifacts (artifact_id, session_id, agent_id, name, artifact_type,
                                      path, size_bytes, created_by_action, experiment_id,
                                      research_id, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                artifact.artifact_id, artifact.session_id, artifact.agent_id,
                artifact.name, artifact.artifact_type, artifact.path,
                artifact.size_bytes, artifact.created_by_action,
                artifact.experiment_id, artifact.research_id,
                artifact.created_at, json.dumps(artifact.metadata)
            ))
            conn.commit()
    
    def record_research(self, research: ResearchSession) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO research_sessions (research_id, session_id, agent_id, question, reason,
                                              status, sources, claims, conclusion,
                                              started_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                research.research_id, research.session_id, research.agent_id,
                research.question, research.reason, research.status,
                json.dumps(research.sources), json.dumps(research.claims),
                research.conclusion, research.started_at, research.completed_at,
                json.dumps(research.metadata)
            ))
            conn.commit()
    
    def record_experiment(self, experiment: Experiment) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO experiments (experiment_id, session_id, agent_id, objective, hypothesis,
                                        proposed_procedure, required_tools, required_permissions,
                                        status, baseline_reference, result, conclusion,
                                        started_at, completed_at, artifacts, metrics, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.experiment_id, experiment.session_id, experiment.agent_id,
                experiment.objective, experiment.hypothesis, experiment.proposed_procedure,
                json.dumps(experiment.required_tools), json.dumps(experiment.required_permissions),
                experiment.status, experiment.baseline_reference, experiment.result,
                experiment.conclusion, experiment.started_at, experiment.completed_at,
                json.dumps(experiment.artifacts), json.dumps(experiment.metrics),
                json.dumps(experiment.metadata)
            ))
            conn.commit()
    
    def record_modification(self, modification: ModificationRecord) -> None:
        if not self._session_id:
            return
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO modifications (modification_id, session_id, agent_id, proposal, reason,
                                          hypothesis, expected_benefit, expected_risk, files_affected,
                                          branch, baseline_commit, status, benchmark_before,
                                          benchmark_after, test_results, approval, applied_commit,
                                          rollback_commit, created_at, completed_at, evidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                modification.modification_id, modification.session_id, modification.agent_id,
                modification.proposal, modification.reason, modification.hypothesis,
                modification.expected_benefit, modification.expected_risk,
                json.dumps(modification.files_affected), modification.branch,
                modification.baseline_commit, modification.status,
                json.dumps(modification.benchmark_before), json.dumps(modification.benchmark_after),
                json.dumps(modification.test_results), modification.approval,
                modification.applied_commit, modification.rollback_commit,
                modification.created_at, modification.completed_at,
                json.dumps(modification.evidence), json.dumps(modification.metadata)
            ))
            conn.commit()
    
    def record_source(self, source: Source) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO sources (source_id, research_id, url, title, domain, publisher,
                                    retrieved_at, content_reference, content_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source.source_id, source.research_id, source.url, source.title,
                source.domain, source.publisher, source.retrieved_at,
                source.content_reference, source.content_hash, json.dumps(source.metadata)
            ))
            conn.commit()
    
    def record_claim(self, claim: Claim) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO claims (claim_id, research_id, source_id, agent_id, claim, claim_type,
                                   confidence, verification_status, supporting_evidence,
                                   contradicting_evidence, created_at, verified_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim.claim_id, claim.research_id, claim.source_id, claim.agent_id,
                claim.claim, claim.claim_type.value, claim.confidence,
                claim.verification_status.value, json.dumps(claim.supporting_evidence),
                json.dumps(claim.contradicting_evidence), claim.created_at,
                claim.verified_at, json.dumps(claim.metadata)
            ))
            conn.commit()
    
    def get_session_evidence(self, session_id: Optional[str] = None, 
                            evidence_type: Optional[EvidenceType] = None,
                            limit: int = 100) -> List[Dict]:
        sid = session_id or self._session_id
        if not sid:
            return []
        
        with self._get_conn() as conn:
            query = "SELECT * FROM evidence WHERE session_id = ?"
            params = [sid]
            
            if evidence_type:
                query += " AND evidence_type = ?"
                params.append(evidence_type.value)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_timeline(self, session_id: Optional[str] = None) -> List[Dict]:
        sid = session_id or self._session_id
        if not sid:
            return []
        
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT * FROM evidence WHERE session_id = ? ORDER BY timestamp ASC
            """, (sid,)).fetchall()
            return [dict(row) for row in rows]
    
    def get_session_info(self, session_id: Optional[str] = None) -> Optional[Dict]:
        sid = session_id or self._session_id
        if not sid:
            return None
        
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
            return dict(row) if row else None


_evidence_manager: Optional[EvidenceManager] = None


def get_evidence_manager() -> EvidenceManager:
    global _evidence_manager
    if _evidence_manager is None:
        _evidence_manager = EvidenceManager()
    return _evidence_manager


def set_evidence_manager(manager: EvidenceManager) -> None:
    global _evidence_manager
    _evidence_manager = manager