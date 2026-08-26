from __future__ import annotations

import hashlib
import logging
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, BinaryIO

from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import Artifact, Evidence, EvidenceType

logger = logging.getLogger(__name__)


class ArtifactManager:
    def __init__(
        self,
        evidence_manager=None,
        artifacts_base_dir: str = "./data/artifacts"
    ):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self.artifacts_base_dir = Path(artifacts_base_dir)
        self.artifacts_base_dir.mkdir(parents=True, exist_ok=True)
        self._artifact_cache: Dict[str, Artifact] = {}
    
    def _get_session_dir(self, session_id: str) -> Path:
        session_dir = self.artifacts_base_dir / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def _get_experiment_dir(self, session_id: str, experiment_id: str) -> Path:
        exp_dir = self._get_session_dir(session_id) / "experiments" / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir
    
    def _get_research_dir(self, session_id: str, research_id: str) -> Path:
        research_dir = self._get_session_dir(session_id) / "research" / research_id
        research_dir.mkdir(parents=True, exist_ok=True)
        return research_dir
    
    def create_artifact(
        self,
        agent_id: str,
        name: str,
        artifact_type: str,
        content: bytes,
        experiment_id: Optional[str] = None,
        research_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by_action: str = ""
    ) -> Artifact:
        session_id = self.evidence_manager._session_id if self.evidence_manager else ""
        
        artifact_id = f"ART-{uuid.uuid4().hex[:8]}"
        content_hash = hashlib.sha256(content).hexdigest()
        
        if experiment_id:
            artifact_dir = self._get_experiment_dir(session_id, experiment_id)
        elif research_id:
            artifact_dir = self._get_research_dir(session_id, research_id)
        else:
            artifact_dir = self._get_session_dir(session_id)
        
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        if not safe_name:
            safe_name = "artifact"
        
        file_path = artifact_dir / f"{artifact_id}_{safe_name}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        size_bytes = len(content)
        
        artifact = Artifact(
            artifact_id=artifact_id,
            session_id=session_id,
            agent_id=agent_id,
            name=name,
            artifact_type=artifact_type,
            path=str(file_path),
            size_bytes=size_bytes,
            created_by_action=created_by_action,
            experiment_id=experiment_id,
            research_id=research_id,
            created_at=datetime.utcnow().isoformat(),
            metadata={
                "content_hash": content_hash,
                **(metadata or {})
            }
        )
        
        self.evidence_manager.record_artifact(artifact)
        self._artifact_cache[artifact_id] = artifact
        
        evidence = Evidence(
            session_id=session_id,
            agent_id=agent_id,
            evidence_type=EvidenceType.AGENT_ACTION,
            intent="Artifact created",
            reason=f"Created artifact: {name}",
            action_details={
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "size_bytes": size_bytes,
                "content_hash": content_hash
            },
            artifacts=[artifact_id],
            tags=["artifact", "created"]
        )
        self.evidence_manager._save_evidence(evidence)
        
        logger.info(f"Artifact created: {artifact_id} ({size_bytes} bytes)")
        
        return artifact
    
    def create_artifact_from_file(
        self,
        agent_id: str,
        name: str,
        artifact_type: str,
        source_path: str,
        experiment_id: Optional[str] = None,
        research_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by_action: str = ""
    ) -> Artifact:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        with open(source, "rb") as f:
            content = f.read()
        
        return self.create_artifact(
            agent_id=agent_id,
            name=name,
            artifact_type=artifact_type,
            content=content,
            experiment_id=experiment_id,
            research_id=research_id,
            metadata=metadata,
            created_by_action=created_by_action
        )
    
    def create_text_artifact(
        self,
        agent_id: str,
        name: str,
        artifact_type: str,
        text: str,
        experiment_id: Optional[str] = None,
        research_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by_action: str = ""
    ) -> Artifact:
        return self.create_artifact(
            agent_id=agent_id,
            name=name,
            artifact_type=artifact_type,
            content=text.encode("utf-8"),
            experiment_id=experiment_id,
            research_id=research_id,
            metadata=metadata,
            created_by_action=created_by_action
        )
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifact_cache.get(artifact_id)
    
    def get_artifact_content(self, artifact_id: str) -> Optional[bytes]:
        artifact = self._artifact_cache.get(artifact_id)
        if not artifact:
            return None
        
        try:
            with open(artifact.path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read artifact {artifact_id}: {e}")
            return None
    
    def get_artifact_text(self, artifact_id: str) -> Optional[str]:
        content = self.get_artifact_content(artifact_id)
        if content is None:
            return None
        return content.decode("utf-8", errors="replace")
    
    def list_artifacts(
        self,
        session_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        research_id: Optional[str] = None,
        artifact_type: Optional[str] = None
    ) -> List[Artifact]:
        artifacts = list(self._artifact_cache.values())
        
        if session_id:
            artifacts = [a for a in artifacts if a.session_id == session_id]
        if experiment_id:
            artifacts = [a for a in artifacts if a.experiment_id == experiment_id]
        if research_id:
            artifacts = [a for a in artifacts if a.research_id == research_id]
        if artifact_type:
            artifacts = [a for a in artifacts if a.artifact_type == artifact_type]
        
        return artifacts
    
    def delete_artifact(self, artifact_id: str) -> bool:
        artifact = self._artifact_cache.get(artifact_id)
        if not artifact:
            return False
        
        try:
            Path(artifact.path).unlink(missing_ok=True)
            del self._artifact_cache[artifact_id]
            logger.info(f"Artifact deleted: {artifact_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return False
    
    def get_artifact_info(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        artifact = self._artifact_cache.get(artifact_id)
        if not artifact:
            return None
        
        return {
            "artifact_id": artifact.artifact_id,
            "name": artifact.name,
            "type": artifact.artifact_type,
            "path": artifact.path,
            "size_bytes": artifact.size_bytes,
            "created_at": artifact.created_at,
            "created_by_action": artifact.created_by_action,
            "experiment_id": artifact.experiment_id,
            "research_id": artifact.research_id,
            "metadata": artifact.metadata
        }


_artifact_manager: Optional[ArtifactManager] = None


def get_artifact_manager() -> ArtifactManager:
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager


def set_artifact_manager(manager: ArtifactManager) -> None:
    global _artifact_manager
    _artifact_manager = manager