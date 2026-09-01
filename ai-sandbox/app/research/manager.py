from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import (
    Evidence, EvidenceType, Source, Claim, ClaimType,
    ResearchSession, VerificationStatus
)
from app.models.base import GenerationRequest, get_model_registry
from app.tools.gateway import get_tool_gateway
from app.tools.web import WebTool

logger = logging.getLogger(__name__)


class ResearchManager:
    def __init__(
        self,
        evidence_manager=None,
        tool_gateway=None,
        web_tool: Optional[WebTool] = None,
        desktop_dir: str = "/Users/pushp/Desktop/Research_Reports",
        reports_dir: str = "./reports/research"
    ):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self.tool_gateway = tool_gateway or get_tool_gateway()
        self.web_tool = web_tool
        self.desktop_dir = Path(desktop_dir)
        self.reports_dir = Path(reports_dir)
        
        # Ensure output directories exist
        try:
            self.desktop_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not initialize desktop research directory {desktop_dir}: {e}")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._research_cache: Dict[str, ResearchSession] = {}
        self._source_cache: Dict[str, Source] = {}
        self._claim_cache: Dict[str, Claim] = {}
    
    def _sanitize_filename(self, text: str) -> str:
        slug = re.sub(r'[^\w\s-]', '', text.strip()).strip()
        slug = re.sub(r'[-\s]+', '_', slug)
        return slug[:60] or "Autonomous_Research"

    async def research(
        self,
        agent_id: str,
        question: str,
        reason: str = "",
        max_sources: int = 5,
        use_cache: bool = True,
        export_desktop: bool = True
    ) -> ResearchSession:
        session_id = (
            self.evidence_manager._session_id
            if (self.evidence_manager and self.evidence_manager._session_id)
            else str(uuid.uuid4())
        )
        
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
            await self.evidence_manager._save_evidence(evidence)
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
        await self.evidence_manager._save_evidence(evidence)
        
        try:
            # 1. Search Web / Knowledge for multi-source evidence
            if self.web_tool:
                search_result = await self.web_tool.execute({
                    "operation": "search",
                    "query": question,
                    "max_results": max_sources
                })
            else:
                web_tool = self.tool_gateway.get_tool("web") if self.tool_gateway else None
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
                    metadata={"search_rank": i, "result": result, "extracted_content": result.get("snippet", "")}
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
            await self.evidence_manager._save_evidence(evidence)
            
            # 2. Extract detailed content from top sources
            if results:
                for result in results[:3]:
                    url = result.get("url", "")
                    if url:
                        await self._extract_content(agent_id, research, url)
            
            # 3. Model-Synthesized Professional Documentation & Desktop Exporter
            synthesis_meta = await self.synthesize_and_save_report(research, export_desktop=export_desktop)
            research.metadata.update(synthesis_meta)

            research.status = "completed"
            research.completed_at = datetime.now(timezone.utc).isoformat()
            self.evidence_manager.record_research(research)
            
            evidence = Evidence(
                session_id=session_id,
                agent_id=agent_id,
                evidence_type=EvidenceType.RESEARCH_COMPLETED,
                intent="Research completed and synthesized",
                reason=f"Synthesized research report with {len(research.sources)} sources",
                action_details={
                    "research_id": research.research_id,
                    "source_count": len(research.sources),
                    "report_path": synthesis_meta.get("report_path", ""),
                    "desktop_path": synthesis_meta.get("desktop_path", "")
                },
                tags=["research", "completed", "synthesized"]
            )
            await self.evidence_manager._save_evidence(evidence)
            
            return research
            
        except Exception as e:
            logger.error(f"Research failed: {e}", exc_info=True)
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
            await self.evidence_manager._save_evidence(evidence)
            return research

    async def synthesize_and_save_report(
        self,
        research: ResearchSession,
        export_desktop: bool = True
    ) -> Dict[str, Any]:
        """Synthesize collected research into a comprehensive, professional Markdown report."""
        sources_data = []
        for sid in research.sources:
            s = self._source_cache.get(sid)
            if s:
                extracted = s.metadata.get("extracted_content") or s.content_reference or ""
                sources_data.append({
                    "title": s.title or s.domain or "Web Source",
                    "url": s.url,
                    "domain": s.domain,
                    "content": extracted[:1500]
                })

        formatted_sources = "\n\n".join([
            f"### [{i+1}] {s['title']} ({s['domain']})\nURL: {s['url']}\nContent Preview: {s['content']}"
            for i, s in enumerate(sources_data)
        ])

        system_prompt = (
            "You are an elite research scientist and principal systems architect. "
            "Your mission is to produce a comprehensive, publication-grade technical research document "
            "formatted in clear, professional GitHub-flavored Markdown."
        )

        user_prompt = f"""Conduct a thorough technical synthesis and produce a professional research report on the topic:
Topic: "{research.question}"

EVALUATED SOURCES & EVIDENCE:
{formatted_sources or "General domain literature and state-of-the-art computational analysis."}

Please generate the complete, exhaustive Markdown report following this exact structure:

# 🔬 Deep Technical Research Report: {research.question}
> **Author:** Autonomous Multi-Agent Research Subsystem  
> **Session ID:** `{research.research_id}` | **Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")} | **Sources Evaluated:** {len(sources_data)}

---

## 1. Executive Summary
- Concise overview of the domain and core problems
- Primary technological or empirical findings
- High-level architectural implications

## 2. Core Architecture & Mechanistic Breakdown
- Detailed technical principles, components, protocols, and data flows
- Key algorithms and design patterns involved

## 3. Comparative Technology & Approaches Matrix
- A structured Markdown comparison table contrasting 3-4 leading methodologies, algorithms, or frameworks
- Dimensions: Throughput/Efficiency, Resilience, Latency, Complexity, Trade-offs

## 4. Empirical Claims & Verified Findings
- Numbered bullet points of key verifiable facts discovered
- Concrete evidence and domain validation

## 5. Evaluated Sources & Citations
- Summary of referenced resources with URLs and domain evaluations

## 6. Unexplored Frontiers & Open Questions
- Specific edge cases, limitations, and missing research areas in this topic

## 7. Strategic Recommendations for System Engineers
- Actionable implementation guidance and architectural next steps
"""

        try:
            registry = get_model_registry()
            model = registry.get("default")
            logger.info(f"Synthesizing research report for '{research.question}' via model router...")
            response = await model.generate(GenerationRequest(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=4000
            ))
            report_text = response.text.strip()
        except Exception as e:
            logger.warning(f"Model synthesis failed, generating structured template: {e}")
            report_text = self._generate_fallback_report(research, sources_data)

        slug = self._sanitize_filename(research.question)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Save in workspace reports
        report_filename = f"Research_{slug}_{timestamp_str}.md"
        report_path = self.reports_dir / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        
        desktop_path = None
        # 2. Save directly to Desktop
        if export_desktop:
            try:
                self.desktop_dir.mkdir(parents=True, exist_ok=True)
                desktop_filename = f"Research_{slug}.md"
                desktop_file = self.desktop_dir / desktop_filename
                with open(desktop_file, "w", encoding="utf-8") as f:
                    f.write(report_text)
                desktop_path = str(desktop_file)
                logger.info(f"✓ Professional research report saved to Desktop: {desktop_path}")
            except Exception as e:
                logger.warning(f"Failed to export report to desktop: {e}")

        return {
            "report_path": str(report_path),
            "desktop_path": desktop_path or str(report_path),
            "summary": report_text[:300] + "...",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _generate_fallback_report(self, research: ResearchSession, sources_data: List[Dict[str, Any]]) -> str:
        sources_md = "\n".join([f"- **{s['title']}** — [{s['url']}]({s['url']})" for s in sources_data]) or "- No external sources recorded."
        return f"""# 🔬 Deep Technical Research Report: {research.question}
> **Author:** Autonomous Multi-Agent Research Subsystem  
> **Session ID:** `{research.research_id}` | **Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

---

## 1. Executive Summary
This document captures findings and empirical evidence gathered for the query: *"{research.question}"*.

## 2. Evaluated Sources
{sources_md}

## 3. Synthesis & Next Steps
Initial evidence gathering complete. Continued autonomous exploration is recommended.
"""

    async def discover_unexplored_gaps(self, limit: int = 5) -> Dict[str, Any]:
        """Analyze prior research sessions & claims to identify novel, unexplored research frontiers."""
        past_topics = []
        try:
            with self.evidence_manager._get_conn() as conn:
                rows = conn.execute("SELECT question FROM research_sessions ORDER BY started_at DESC LIMIT 20").fetchall()
                past_topics = [dict(row)["question"] for row in rows if dict(row).get("question")]
        except Exception as e:
            logger.warning(f"Could not read prior research sessions from database: {e}")

        # If cache has additional sessions
        for sess in self._research_cache.values():
            if sess.question and sess.question not in past_topics:
                past_topics.append(sess.question)

        prompt = f"""You are an advanced Autonomous AI Discovery & Hypothesis Generator.
Our autonomous agent lab has already conducted research on the following topics:
{json.dumps(past_topics, indent=2) if past_topics else '["Autonomous multi-agent systems", "Event-driven sandbox coordination"]'}

Your task:
1. Analyze what domains/technologies have ALREADY been covered.
2. Formulate {limit} completely NOVEL, HIGH-IMPACT, UNEXPLORED research questions/topics that have NOT been researched yet.
3. For each topic, provide a crisp rationale, expected impact, and the novel angle.

Return ONLY a valid JSON array of objects with the following schema:
[
  {{
    "topic": "Precise, actionable research question or technical topic",
    "category": "Architecture | Security | Consensus | Performance | Self-Evolution",
    "rationale": "Why this topic is critical and complementary to past work",
    "impact": "HIGH" | "MEDIUM",
    "unexplored_aspect": "Specific gap in current literature or prior sessions"
  }}
]
"""
        try:
            registry = get_model_registry()
            model = registry.get("default")
            response = await model.generate(GenerationRequest(
                prompt=prompt,
                system_prompt="You are a research director analyzing knowledge coverage. Return valid JSON only.",
                temperature=0.7,
                max_tokens=2000
            ))
            
            text = response.text.strip()
            # Clean possible markdown fence
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            gaps = json.loads(text)
            return {
                "analyzed_previous_topics_count": len(past_topics),
                "previous_topics": past_topics,
                "recommended_gaps": gaps,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"Gap discovery model inference error: {e}")
            # Resilient fallback novel recommendations
            fallback_gaps = [
                {
                    "topic": "Zero-Knowledge Cryptographic Verification of Multi-Agent State Transitions",
                    "category": "Security",
                    "rationale": "Ensures verifiable tamper-proof audit trails for autonomous agent actions without leaking private memory.",
                    "impact": "HIGH",
                    "unexplored_aspect": "ZK-SNARK proof generation for in-memory SQLite and vector state delta verification."
                },
                {
                    "topic": "Dynamic DAG Task Orchestration with Self-Healing Graph Pruning",
                    "category": "Architecture",
                    "rationale": "Enables complex multi-agent workflows to decompose parallel subtasks and automatically recover from deadlocks.",
                    "impact": "HIGH",
                    "unexplored_aspect": "Automated cycle detection and real-time task graph replanning."
                },
                {
                    "topic": "Sub-Millisecond Vector Embedding Quantization for On-Device Agent Memory",
                    "category": "Performance",
                    "rationale": "Reduces RAM footprint and vector lookup latency on local execution nodes.",
                    "impact": "MEDIUM",
                    "unexplored_aspect": "Scalar vs product quantization trade-offs in local ChromaDB instances."
                }
            ]
            return {
                "analyzed_previous_topics_count": len(past_topics),
                "previous_topics": past_topics,
                "recommended_gaps": fallback_gaps,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _extract_content(self, agent_id: str, research: ResearchSession, url: str) -> None:
        session_id = (
            self.evidence_manager._session_id
            if (self.evidence_manager and self.evidence_manager._session_id)
            else str(uuid.uuid4())
        )
        
        try:
            if self.web_tool:
                extract_result = await self.web_tool.execute({
                    "operation": "extract_text",
                    "url": url
                })
            else:
                web_tool = self.tool_gateway.get_tool("web") if self.tool_gateway else None
                if web_tool:
                    extract_result = await web_tool.execute({
                        "operation": "extract_text",
                        "url": url
                    })
                else:
                    extract_result = {"error": "Web tool not available"}
            
            content = extract_result.get("text", "")
            if content:
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                source = None
                for sid in research.sources:
                    s = self._source_cache.get(sid)
                    if s and s.url == url:
                        source = s
                        break
                
                if source:
                    source.content_hash = content_hash
                    source.metadata["extracted_content"] = content[:2000]
                    self.evidence_manager.record_source(source)
                else:
                    source_id = str(uuid.uuid4())[:8]
                    source = Source(
                        source_id=source_id,
                        research_id=research.research_id,
                        url=url,
                        title=self._extract_domain(url),
                        domain=self._extract_domain(url),
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        content_reference=url,
                        content_hash=content_hash,
                        metadata={"extracted_content": content[:2000]}
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
                    await self.evidence_manager._save_evidence(evidence)
                    
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