from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import Decision, Evidence, EvidenceType

logger = logging.getLogger(__name__)


class DecisionManager:
    def __init__(self, evidence_manager=None):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self._decision_cache: Dict[str, Decision] = {}
    
    def record_decision(
        self,
        agent_id: str,
        decision: str,
        reason: str = "",
        evidence_considered: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None,
        resulting_action: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Decision:
        session_id = self.evidence_manager._session_id if self.evidence_manager else ""
        
        decision_obj = Decision(
            session_id=session_id,
            agent_id=agent_id,
            decision=decision,
            reason=reason,
            evidence_considered=evidence_considered or [],
            alternatives=alternatives or [],
            resulting_action=resulting_action,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        self.evidence_manager.record_decision(decision_obj)
        self._decision_cache[decision_obj.decision_id] = decision_obj
        
        evidence = Evidence(
            session_id=session_id,
            agent_id=agent_id,
            evidence_type=EvidenceType.DECISION,
            intent="Decision recorded",
            reason=reason,
            action_details={
                "decision": decision,
                "decision_id": decision_obj.decision_id,
                "alternatives": alternatives or []
            },
            tags=["decision", "recorded"]
        )
        self.evidence_manager._save_evidence(evidence)
        
        logger.info(f"Decision recorded: {decision_obj.decision_id} by {agent_id}")
        
        return decision_obj
    
    def get_decision(self, decision_id: str) -> Optional[Decision]:
        return self._decision_cache.get(decision_id)
    
    def get_decisions_by_agent(self, agent_id: str) -> List[Decision]:
        return [d for d in self._decision_cache.values() if d.agent_id == agent_id]
    
    def get_decisions_by_session(self, session_id: str) -> List[Decision]:
        return [d for d in self._decision_cache.values() if d.session_id == session_id]


_decision_manager: Optional[DecisionManager] = None


def get_decision_manager() -> DecisionManager:
    global _decision_manager
    if _decision_manager is None:
        _decision_manager = DecisionManager()
    return _decision_manager


def set_decision_manager(manager: DecisionManager) -> None:
    global _decision_manager
    _decision_manager = manager