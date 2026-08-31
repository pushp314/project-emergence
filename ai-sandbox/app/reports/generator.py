from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import EvidenceType, ClaimType
from app.sessions.manager import get_session_manager

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(
        self,
        evidence_manager=None,
        session_manager=None,
        reports_dir: str = "./reports"
    ):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self.session_manager = session_manager or get_session_manager()
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_final_report(self, session_id: str) -> str:
        session_info = self.session_manager.get_session_info(session_id) if self.session_manager else None
        if not session_info:
            session_info = {
                "session_id": session_id,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "session_number": 1,
                "status": "active"
            }
        
        timeline = self._generate_timeline(session_id)
        raw_evidence = self.evidence_manager.get_session_evidence(session_id) if self.evidence_manager else []
        session_evidence = [e for e in raw_evidence if isinstance(e, dict)]
        
        report = self._build_report(session_info, timeline, session_evidence)
        
        report_path = self.reports_dir / f"session_{session_id}_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        json_path = self.reports_dir / f"session_{session_id}_report.json"
        with open(json_path, "w") as f:
            json.dump({
                "session_info": session_info,
                "timeline": timeline,
                "evidence_count": len(session_evidence),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
        
        logger.info(f"Final report generated for session {session_id}: {report_path}")
        return str(report_path)
    
    def _generate_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        raw_evidence = self.evidence_manager.get_session_evidence(session_id) if self.evidence_manager else []
        session_evidence = [e for e in raw_evidence if isinstance(e, dict)]
        
        timeline = []
        for e in sorted(session_evidence, key=lambda x: x.get("timestamp", "")):
            timeline.append({
                "timestamp": e.get("timestamp"),
                "event_type": e.get("evidence_type"),
                "agent": e.get("agent_id"),
                "intent": e.get("intent"),
                "reason": e.get("reason"),
                "evidence_id": e.get("evidence_id")
            })
        
        return timeline
    
    def _build_report(self, session_info: Dict, timeline: List[Dict], evidence: List[Dict]) -> str:
        start_time = session_info.get("start_time", "Unknown")
        end_time = session_info.get("end_time", "Unknown")
        session_number = session_info.get("session_number", "Unknown")
        
        model_cfg = session_info.get("model_configuration", {})
        if isinstance(model_cfg, str):
            try:
                model_cfg = json.loads(model_cfg)
            except Exception:
                model_cfg = {}

        gen_cfg = session_info.get("configuration", {})
        if isinstance(gen_cfg, str):
            try:
                gen_cfg = json.loads(gen_cfg)
            except Exception:
                gen_cfg = {}
        
        evidence_by_type = {}
        for e in evidence:
            etype = e.get("evidence_type", "unknown")
            if etype not in evidence_by_type:
                evidence_by_type[etype] = 0
            evidence_by_type[etype] += 1
        
        research_evidence = [e for e in evidence if e.get("evidence_type") in [
            "research_started", "browser_search", "source_found", "content_extracted", "research_completed"
        ]]
        
        decisions = [e for e in evidence if e.get("evidence_type") == "decision"]
        
        experiments = [e for e in evidence if e.get("evidence_type") in [
            "experiment_started", "experiment_completed", "experiment_failed"
        ]]
        
        permissions = [e for e in evidence if e.get("evidence_type") in [
            "permission_request", "permission_granted", "permission_denied"
        ]]
        
        tool_calls = [e for e in evidence if e.get("evidence_type") in [
            "tool_call", "tool_result"
        ]]
        
        report = f"""# Autonomous AI Session Report

## Session Information

- **Session ID**: {session_info.get('session_id', 'Unknown')}
- **Session Number**: #{session_number}
- **Status**: {session_info.get('status', 'Unknown')}
- **Start Time**: {start_time}
- **End Time**: {end_time}
- **Duration**: {self._calculate_duration(start_time, end_time)}

## Configuration

- **Model**: {model_cfg.get('default', 'Resilient Multi-Tier Router (Gemini -> OpenRouter -> Ollama)')}
- **Max Turns**: {gen_cfg.get('max_turns', 1000)}
- **Scheduler**: {gen_cfg.get('scheduler_policy', 'round_robin')}

## Environment

- **Project Version**: {session_info.get('project_version', '1.0.0')}
- **Git Commit**: {session_info.get('git_commit', 'main')}

## Evidence Summary

Total Evidence Events: {len(evidence)}

### By Type
"""
        for etype, count in sorted(evidence_by_type.items()):
            report += f"- **{etype}**: {count}\n"
        
        report += f"""

## Research Performed

Total Research Events: {len(research_evidence)}

"""
        for e in research_evidence:
            reason = e.get("reason", "")
            report += f"- {e.get('timestamp', '')}: {reason}\n"
        
        report += f"""

## Important Decisions

Total Decisions: {len(decisions)}

"""
        for e in decisions:
            reason = e.get("reason", "")
            report += f"- {e.get('timestamp', '')}: {reason}\n"
        
        report += f"""

## Experiments

Total Experiment Events: {len(experiments)}

"""
        for e in experiments:
            reason = e.get("reason", "")
            report += f"- {e.get('timestamp', '')}: {reason}\n"
        
        report += f"""

## Human Interventions & Permissions

Total Permission Events: {len(permissions)}

"""
        for e in permissions:
            reason = e.get("reason", "")
            report += f"- {e.get('timestamp', '')}: {reason}\n"
        
        report += f"""

## Tool Usage

Total Tool Events: {len(tool_calls)}

"""
        for e in tool_calls:
            reason = e.get("reason", "")
            report += f"- {e.get('timestamp', '')}: {reason}\n"
        
        report += f"""

## Complete Timeline

"""
        for event in timeline:
            timestamp = event.get("timestamp", "")
            event_type = event.get("event_type", "unknown")
            agent = event.get("agent", "unknown")
            intent = event.get("intent", "")
            reason = event.get("reason", "")
            report += f"- **{timestamp}** [{event_type}] {agent}: {intent} - {reason}\n"
        
        report += f"""

## Conclusions

This session completed with status: {session_info.get('status', 'Unknown')}.

The agents conducted research, made decisions, and explored topics through structured conversation.

---

*Report generated at {datetime.now(timezone.utc).isoformat()}*
"""
        return report
    
    def _calculate_duration(self, start: str, end: str) -> str:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            diff = end_dt - start_dt
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            seconds = diff.seconds % 60
            return f"{diff.days}d {hours}h {minutes}m {seconds}s"
        except Exception:
            return "Unknown"
    
    def generate_timeline_json(self, session_id: str) -> List[Dict[str, Any]]:
        return self._generate_timeline(session_id)
    
    def export_session_data(self, session_id: str, format: str = "json") -> str:
        session_info = self.session_manager.get_session_info(session_id)
        timeline = self._generate_timeline(session_id)
        evidence = self.evidence_manager.get_session_evidence(session_id)
        
        data = {
            "session_info": session_info,
            "timeline": timeline,
            "evidence": evidence,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }
        
        if format == "json":
            export_path = self.reports_dir / f"session_{session_id}_export.json"
            with open(export_path, "w") as f:
                json.dump(data, f, indent=2)
            return str(export_path)
        else:
            raise ValueError(f"Unsupported format: {format}")


_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator


def set_report_generator(generator: ReportGenerator) -> None:
    global _report_generator
    _report_generator = generator