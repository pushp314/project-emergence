from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import (
    Evidence, EvidenceType, Source, Claim, ClaimType,
    ResearchSession, VerificationStatus
)
from app.tools.gateway import get_tool_gateway
from app.tools.web import WebTool

logger = logging.getLogger(__name__)


class ResearchManager:
    def __init__(
        self,
        evidence_manager=None,
        tool_gateway=None,
        web_tool: Optional[WebTool] = None
    ):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self.tool_gateway = tool_gateway or get_tool_gateway()
        self.web_tool = web_tool
        self._research_cache: Dict[str, ResearchSession] = {}
        self._source_cache: Dict[str, Source] = {}
        self._claim_cache: Dict[str, Claim] = {}
    
    async def research(
        self,
        agent_id: str,
        question: str,
        reason: str = "",
        max_sources: int = 5,
        use_cache: bool = True
    ) -> ResearchSession:
        session_id = self.evidence_manager._session_id if self.evidence_manager else ""
        
        cache_key = self._generate_cache_key(question)
        
        if use_cache and cache_key in self._research_cache:
            cached = self._research_cache[cache_key]
            logger.info(f"Returning cached research for: {question}")
            
            evidence = Evidence(
                session_id=session_id,
                agent_id=agent_id,
                evidence_type=EvidenceType.RESEARCH_STARTED,
                intent="Cached research retrieved",
                reason=f"Cache hit for question: {question}",
                action_details={"cache_key": cache_key, "original_question": question},
                tags=["research", "cache", "cached"]
            )
            self.evidence_manager._save_evidence(evidence)
            
            return cached
        
        research = ResearchSession(
            session_id=session_id,
            agent_id=agent_id,
            question=question,
            reason=reason,
            status="in_progress",
            started_at=datetime.now(timezone.utc).isoformat()
        )
        
        self._research_cache[cache_key] = research
        
        evidence = Evidence(
            session_id=session_id,
            agent_id=agent_id,
            evidence_type=EvidenceType.RESEARCH_STARTED,
            intent="Research started",
            reason=reason,
            action_details={"question": question, "max_sources": max_sources},
            tags=["research", "started"]
        )
        self.evidence_manager._save_evidence(evidence)
        
        try:
            if self.web_tool:
                search_result = await self.web_tool.execute({
                    "operation": "search",
                    "query": question,
                    "max_results": max_sources
                })
            else:
                web_tool = self.tool_gateway.get_tool("web")
                if web_tool:
                    search_result = await web_tool.execute({
                        "operation": "search",
                        "query": question,
                        "max_results": max_sources
                    })
                else:
                    search_result = {"error": "Web tool not available", "results": []}
            
            results = search_result.get("results", [])
            
            for i, result in enumerate(results):
                source = Source(
                    research_id=research.research_id,
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    domain=self._extract_domain(result.get("url", "")),
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    content_reference=result.get("snippet", ""),
                    metadata={"search_rank": i, "result": result}
                )
                self.evidence_manager.record_source(source)
                research.sources.append(source.source_id)
                self._source_cache[source.source_id] = source
            
            evidence = Evidence(
                session_id=session_id,
                agent_id=agent_id,
                evidence_type=EvidenceType.BROWSER_SEARCH,
                intent="Browser search completed",
                reason=f"Search returned {len(results)} results",
                action_details={"question": question, "result_count": len(results)},
                tags=["research", "search", "completed"]
            )
            self.evidence_manager._save_evidence(evidence)
            
            if results:
                for result in results[:3]:
                    url = result.get("url", "")
                    if url:
                        await self._extract_content(agent_id, research, url)
            
            research.status = "completed"
            research.completed_at = datetime.now(timezone.utc).isoformat()
            self.evidence_manager.record_research(research)
            
            evidence = Evidence(
                session_id=session_id,
                agent_id=agent_id,
                evidence_type=EvidenceType.RESEARCH_COMPLETED,
                intent="Research completed",
                reason=f"Research completed with {len(research.sources)} sources",
                action_details={"research_id": research.research_id, "source_count": len(research.sources)},
                tags=["research", "completed"]
            )
            self.evidence_manager._save_evidence(evidence)
            
            return research
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            research.status = "failed"
            research.completed_at = datetime.now(timezone.utc).isoformat()
            self.evidence_manager.record_research(research)
            
            evidence = Evidence(
                session_id=session_id,
                agent_id=agent_id,
                evidence_type=EvidenceType.RESEARCH_STARTED,
                intent="Research failed",
                reason=f"Research error: {str(e)}",
                tags=["research", "failed"]
            )
            self.evidence_manager._save_evidence(evidence)
            
            return research
    
    async def _extract_content(self, agent_id: str, research: ResearchSession, url: str) -> None:
        session_id = self.evidence_manager._session_id if self.evidence_manager else ""
        
        try:
            if self.web_tool:
                extract_result = await self.web_tool.execute({
                    "operation": "extract",
                    "url": url
                })
            else:
                web_tool = self.tool_gateway.get_tool("web")
                if web_tool:
                    extract_result = await web_tool.execute({
                        "operation": "extract",
                        "url": url
                    })
                else:
                    return
            
            extracted = extract_result.get("extracted", [])
            
            for content in extracted:
                if content and len(content) > 100:
                    source_id = f"SRC-{uuid.uuid4().hex[:8]}"
                    source = Source(
                        source_id=source_id,
                        research_id=research.research_id,
                        url=url,
                        title=extract_result.get("title", ""),
                        domain=self._extract_domain(url),
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        content_reference=content[:5000],
                        metadata={"extracted_length": len(content)}
                    )
                    self.evidence_manager.record_source(source)
                    research.sources.append(source_id)
                    self._source_cache[source_id] = source
                    
                    evidence = Evidence(
                        session_id=session_id,
                        agent_id=agent_id,
                        evidence_type=EvidenceType.CONTENT_EXTRACTED,
                        intent="Content extracted from source",
                        reason=f"Extracted content from {url}",
                        action_details={"source_id": source_id, "url": url, "content_length": len(content)},
                        tags=["research", "extraction"]
                    )
                    self.evidence_manager._save_evidence(evidence)
                    
        except Exception as e:
            logger.warning(f"Content extraction failed for {url}: {e}")
    
    def _generate_cache_key(self, question: str) -> str:
        return hashlib.sha256(question.lower().strip().encode()).hexdigest()[:16]
    
    def _extract_domain(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return ""
    
    def add_claim(
        self,
        research_id: str,
        agent_id: str,
        claim: str,
        claim_type: ClaimType = ClaimType.AGENT_CLAIM,
        confidence: float = 0.5,
        source_id: str = "",
        supporting_evidence: Optional[List[str]] = None
    ) -> Claim:
        claim_obj = Claim(
            research_id=research_id,
            source_id=source_id,
            agent_id=agent_id,
            claim=claim,
            claim_type=claim_type,
            confidence=confidence,
            verification_status=VerificationStatus.PENDING,
            supporting_evidence=supporting_evidence or [],
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        self.evidence_manager.record_claim(claim_obj)
        self._claim_cache[claim_obj.claim_id] = claim_obj
        
        return claim_obj
    
    def verify_claim(self, claim_id: str, status: VerificationStatus, evidence_ids: Optional[List[str]] = None) -> bool:
        if claim_id not in self._claim_cache:
            return False
        
        claim = self._claim_cache[claim_id]
        claim.verification_status = status
        claim.verified_at = datetime.now(timezone.utc).isoformat()
        
        if evidence_ids:
            claim.supporting_evidence = evidence_ids
        
        self.evidence_manager.record_claim(claim)
        
        return True
    
    def get_research(self, research_id: str) -> Optional[ResearchSession]:
        return self._research_cache.get(research_id)
    
    def get_source(self, source_id: str) -> Optional[Source]:
        return self._source_cache.get(source_id)
    
    def get_claim(self, claim_id: str) -> Optional[Claim]:
        return self._claim_cache.get(claim_id)
    
    def get_cached_research(self, question: str) -> Optional[ResearchSession]:
        cache_key = self._generate_cache_key(question)
        return self._research_cache.get(cache_key)
    
    def detect_duplicate_research(self, question: str) -> Optional[ResearchSession]:
        return self.get_cached_research(question)
    
    def clear_cache(self) -> None:
        self._research_cache.clear()
        self._source_cache.clear()
        self._claim_cache.clear()


_research_manager: Optional[ResearchManager] = None


def get_research_manager() -> ResearchManager:
    global _research_manager
    if _research_manager is None:
        _research_manager = ResearchManager()
    return _research_manager


def set_research_manager(manager: ResearchManager) -> None:
    global _research_manager
    _research_manager = manager