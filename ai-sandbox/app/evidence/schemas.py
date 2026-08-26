from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class EvidenceType(str, Enum):
    AGENT_ACTION = "agent_action"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    BROWSER_SEARCH = "browser_search"
    SOURCE_FOUND = "source_found"
    CONTENT_EXTRACTED = "content_extracted"
    CLAIM = "claim"
    VERIFICATION = "verification"
    EVIDENCE_CREATED = "evidence_created"
    DECISION = "decision"
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"
    EXPERIMENT_FAILED = "experiment_failed"
    MODIFICATION_PROPOSED = "modification_proposed"
    MODIFICATION_APPLIED = "modification_applied"
    MODIFICATION_ROLLBACK = "modification_rollback"
    RESOURCE_WARNING = "resource_warning"
    SYSTEM_ERROR = "system_error"
    HUMAN_INTERVENTION = "human_intervention"
    OBSERVER_INTERVENTION = "observer_intervention"
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    EMERGENCE_OBSERVED = "emergence_observed"
    AGENT_SELF_ASSESSMENT = "agent_self_assessment"
    AGENT_ROLE_CHANGE = "agent_role_change"
    AGENT_DISAGREEMENT = "agent_disagreement"


class IntentActionStage(str, Enum):
    SENSE = "sense"
    CATEGORIZE = "categorize"
    INTEND = "intend"
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    LEARN = "learn"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    FAILED = "failed"
    UNVERIFIABLE = "unverifiable"


class ClaimType(str, Enum):
    FACT = "fact"
    OBSERVATION = "observation"
    AGENT_CLAIM = "agent_claim"
    EXTERNAL_SOURCE = "external_source"
    HYPOTHESIS = "hypothesis"
    EXPERIMENTAL_RESULT = "experimental_result"
    CONCLUSION = "conclusion"


@dataclass
class Evidence:
    evidence_id: str = field(default_factory=lambda: f"E-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    evidence_type: EvidenceType = EvidenceType.AGENT_ACTION
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: str = ""
    intent: str = ""
    reason: str = ""
    action_details: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    permission_required: bool = False
    permission_id: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentActionRecord:
    record_id: str = field(default_factory=lambda: f"IAR-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    correlation_id: str = ""
    stage: IntentActionStage = IntentActionStage.SENSE
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Source:
    source_id: str = field(default_factory=lambda: f"SRC-{uuid.uuid4().hex[:8]}")
    research_id: str = ""
    url: str = ""
    title: str = ""
    domain: str = ""
    publisher: str = ""
    retrieved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    content_reference: str = ""
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    claim_id: str = field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:8]}")
    research_id: str = ""
    source_id: str = ""
    agent_id: str = ""
    claim: str = ""
    claim_type: ClaimType = ClaimType.AGENT_CLAIM
    confidence: float = 0.5
    verification_status: VerificationStatus = VerificationStatus.PENDING
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    verified_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchSession:
    research_id: str = field(default_factory=lambda: f"R-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    question: str = ""
    reason: str = ""
    status: str = "pending"
    sources: List[str] = field(default_factory=list)
    claims: List[str] = field(default_factory=list)
    conclusion: str = ""
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    experiment_id: str = field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    objective: str = ""
    hypothesis: str = ""
    proposed_procedure: str = ""
    required_tools: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    status: str = "proposed"
    baseline_reference: Optional[str] = None
    result: Optional[str] = None
    conclusion: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    decision_id: str = field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    decision: str = ""
    reason: str = ""
    evidence_considered: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    resulting_action: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Artifact:
    artifact_id: str = field(default_factory=lambda: f"ART-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    name: str = ""
    artifact_type: str = ""
    path: str = ""
    size_bytes: int = 0
    created_by_action: str = ""
    experiment_id: Optional[str] = None
    research_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModificationRecord:
    modification_id: str = field(default_factory=lambda: f"SM-{uuid.uuid4().hex[:8]}")
    session_id: str = ""
    agent_id: str = ""
    proposal: str = ""
    reason: str = ""
    hypothesis: str = ""
    expected_benefit: str = ""
    expected_risk: str = ""
    files_affected: List[str] = field(default_factory=list)
    branch: str = ""
    baseline_commit: str = ""
    status: str = "proposed"
    benchmark_before: Dict[str, Any] = field(default_factory=dict)
    benchmark_after: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    approval: Optional[str] = None
    applied_commit: Optional[str] = None
    rollback_commit: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)