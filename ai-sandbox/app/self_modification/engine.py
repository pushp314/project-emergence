from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
import time
import psutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable

import re
from app.models.base import get_model_registry, GenerationRequest
from app.evidence.manager import get_evidence_manager
from app.evidence.schemas import ModificationRecord, Evidence, EvidenceType

logger = logging.getLogger(__name__)


BENCHMARK_PROBE_PROMPT = "Explain the importance of code modularity in one paragraph."

class ModificationStatus(str):
    PROPOSED = "proposed"
    BASELINE = "baseline"
    ISOLATED = "isolated"
    TESTING = "testing"
    BENCHMARKING = "benchmarking"
    EVALUATING = "evaluating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ModificationRisk(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


CORE_SAFETY_FILES = [
    "app/permissions/manager.py",
    "app/evidence/manager.py",
    "app/resources/monitor.py",
    "app/orchestration/state_machine.py",
    "app/orchestration/conversation.py",
    "app/sessions/manager.py",
    "app/main.py",
]


@dataclass
class BenchmarkResult:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ram_mb: float = 0.0
    cpu_percent: float = 0.0
    inference_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    context_tokens: int = 0
    test_passed: bool = True
    error_rate: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    test_details: List[Dict[str, Any]] = field(default_factory=list)


class SelfModificationEngine:
    def __init__(
        self,
        evidence_manager=None,
        project_root: Optional[str] = None,
        max_concurrent: int = 1
    ):
        self.evidence_manager = evidence_manager or get_evidence_manager()
        self.project_root = Path(project_root) if project_root else Path(os.environ.get("PROJECT_ROOT", str(Path.cwd())))
        self.max_concurrent = max_concurrent
        self._active_modifications: Dict[str, ModificationRecord] = {}
        self._worktrees: Dict[str, Path] = {}
        self._modification_lock = asyncio.Lock()
        self._cooldown_until: Optional[datetime] = None
    
    def _is_core_safety_file(self, file_path: str) -> bool:
        for core_file in CORE_SAFETY_FILES:
            if core_file in file_path:
                return True
        return False
    
    def _get_risk_level(self, files_affected: List[str]) -> str:
        for f in files_affected:
            if self._is_core_safety_file(f):
                return ModificationRisk.CRITICAL
        
        for f in files_affected:
            if any(keyword in f for keyword in ["permission", "security", "auth", "resource", "orchestration"]):
                return ModificationRisk.HIGH
        
        for f in files_affected:
            if any(keyword in f for keyword in ["agent", "model", "tool", "memory"]):
                return ModificationRisk.MEDIUM
        
        return ModificationRisk.LOW
    
    async def propose_modification(
        self,
        agent_id: str,
        problem: str,
        hypothesis: str,
        proposed_change: str,
        expected_benefit: str,
        expected_risk: str,
        files_affected: List[str],
        tests_required: List[str],
        metrics: List[str]
    ) -> ModificationRecord:
        async with self._modification_lock:
            if self._cooldown_until and datetime.now(timezone.utc) < self._cooldown_until:
                raise RuntimeError(f"Modification cooldown active until {self._cooldown_until}")
            
            if len(self._active_modifications) >= self.max_concurrent:
                raise RuntimeError(f"Max concurrent modifications ({self.max_concurrent}) reached")
        
        session_id = self.evidence_manager._session_id if self.evidence_manager else ""
        
        risk_level = self._get_risk_level(files_affected)
        
        modification = ModificationRecord(
            session_id=session_id,
            agent_id=agent_id,
            proposal=proposed_change,
            reason=problem,
            hypothesis=hypothesis,
            expected_benefit=expected_benefit,
            expected_risk=expected_risk,
            files_affected=files_affected,
            branch=f"self-modification/SM-{uuid.uuid4().hex[:8]}",
            baseline_commit=await self._get_current_commit(),
            status=ModificationStatus.PROPOSED,
            metadata={
                "risk_level": risk_level,
                "tests_required": tests_required,
                "metrics": metrics
            }
        )
        
        self.evidence_manager.record_modification(modification)
        self._active_modifications[modification.modification_id] = modification
        
        evidence = Evidence(
            session_id=session_id,
            agent_id=agent_id,
            evidence_type=EvidenceType.MODIFICATION_PROPOSED,
            intent="Self-modification proposed",
            reason=problem,
            action_details={
                "modification_id": modification.modification_id,
                "proposed_change": proposed_change,
                "files_affected": files_affected,
                "risk_level": risk_level
            },
            tags=["self-modification", "proposed"]
        )
        self.evidence_manager._save_evidence(evidence)
        
        if risk_level == ModificationRisk.CRITICAL:
            await self._request_human_approval(modification)
        else:
            await self._execute_modification(modification)
        
        return modification
    
    async def _request_human_approval(self, modification: ModificationRecord) -> None:
        try:
            from app.models.base import get_model_registry, GenerationRequest
            critical_model = get_model_registry().get("critical_review")
            
            review_prompt = f"""You are a critical safety reviewer.
Assess the risk of this proposed self-modification.

Proposal: {modification.proposal}
Reason: {modification.reason}
Hypothesis: {modification.hypothesis}
Expected Risk: {modification.expected_risk}
Files Affected: {', '.join(modification.files_affected)}

Please produce a structured risk assessment summary."""
            
            req = GenerationRequest(prompt=review_prompt)
            resp = await critical_model.generate(req)
            modification.metadata["critical_review_assessment"] = resp.text
        except Exception as e:
            logger.error(f"Critical review model failed: {e}")
            modification.metadata["critical_review_assessment"] = f"Review failed: {e}"
            
        modification.status = ModificationStatus.PENDING_APPROVAL
        self.evidence_manager.record_modification(modification)
        
        logger.warning(f"HIGH RISK MODIFICATION REQUIRES HUMAN APPROVAL: {modification.modification_id}")
        
        evidence = Evidence(
            session_id=modification.session_id,
            agent_id=modification.agent_id,
            evidence_type=EvidenceType.MODIFICATION_PROPOSED,
            intent="Human approval requested",
            reason=f"Critical modification {modification.modification_id} requires human approval",
            action_details={"modification_id": modification.modification_id, "assessment": modification.metadata.get("critical_review_assessment", "")},
            tags=["self-modification", "approval_required"]
        )
        self.evidence_manager._save_evidence(evidence)
    
    async def approve_modification(self, modification_id: str, approved_by: str = "human") -> bool:
        modification = self._active_modifications.get(modification_id)
        if not modification:
            return False
        
        modification.approval = approved_by
        modification.status = ModificationStatus.APPROVED
        self.evidence_manager.record_modification(modification)
        
        await self._execute_modification(modification)
        return True
    
    async def reject_modification(self, modification_id: str, reason: str = "") -> bool:
        modification = self._active_modifications.get(modification_id)
        if not modification:
            return False
        
        modification.status = ModificationStatus.REJECTED
        modification.metadata["rejection_reason"] = reason
        self.evidence_manager.record_modification(modification)
        
        evidence = Evidence(
            session_id=modification.session_id,
            agent_id=modification.agent_id,
            evidence_type=EvidenceType.MODIFICATION_PROPOSED,
            intent="Modification rejected",
            reason=reason or "Rejected by human",
            action_details={"modification_id": modification_id},
            tags=["self-modification", "rejected"]
        )
        self.evidence_manager._save_evidence(evidence)
        
        self._active_modifications.pop(modification_id, None)
        return True
    
    async def _execute_modification(self, modification: ModificationRecord) -> None:
        modification.status = ModificationStatus.ISOLATED
        self.evidence_manager.record_modification(modification)
        
        worktree_path = await self._create_worktree(modification.branch)
        self._worktrees[modification.modification_id] = worktree_path
        
        try:
            benchmark_before = await self._run_benchmark(modification, worktree_path, "before")
            modification.benchmark_before = benchmark_before.__dict__
            self.evidence_manager.record_modification(modification)
            
            await self._apply_changes(modification, worktree_path)
            
            modification.status = ModificationStatus.TESTING
            self.evidence_manager.record_modification(modification)
            
            test_result = await self._run_tests(modification, worktree_path)
            modification.test_results = test_result.__dict__
            self.evidence_manager.record_modification(modification)
            
            if not test_result.passed > 0 or test_result.failed > 0:
                modification.status = ModificationStatus.FAILED
                self.evidence_manager.record_modification(modification)
                await self._cleanup_worktree(modification)
                return
            
            modification.status = ModificationStatus.BENCHMARKING
            self.evidence_manager.record_modification(modification)
            
            benchmark_after = await self._run_benchmark(modification, worktree_path, "after")
            modification.benchmark_after = benchmark_after.__dict__
            self.evidence_manager.record_modification(modification)
            
            modification.status = ModificationStatus.EVALUATING
            self.evidence_manager.record_modification(modification)
            
            evaluation = self._evaluate_modification(modification)
            
            if evaluation["should_apply"]:
                modification.status = ModificationStatus.APPROVED
                self.evidence_manager.record_modification(modification)
                await self._apply_to_main(modification)
            else:
                modification.status = ModificationStatus.REJECTED
                modification.metadata["evaluation"] = evaluation
                self.evidence_manager.record_modification(modification)
                await self._cleanup_worktree(modification)
                
        except Exception as e:
            logger.error(f"Modification execution failed: {e}")
            modification.status = ModificationStatus.FAILED
            modification.metadata["error"] = str(e)
            self.evidence_manager.record_modification(modification)
            await self._cleanup_worktree(modification)
    
    async def _create_worktree(self, branch: str) -> Path:
        worktree_path = self.project_root.parent / f"ai-sandbox-worktree-{branch.replace('/', '-')}"
        
        try:
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, str(worktree_path), "HEAD"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e}")
            raise
        
        return worktree_path
    
    async def _apply_changes(self, modification: ModificationRecord, worktree_path: Path) -> None:
        from app.models.base import get_model_registry, GenerationRequest
        planning_model = get_model_registry().get("planning")
        
        # Read the current content of the affected files from the worktree
        file_contents = ""
        for file_path in modification.files_affected:
            full_path = worktree_path / file_path
            if full_path.exists():
                content = full_path.read_text()
                file_contents += f"\n--- {file_path} ---\n{content}\n"
            else:
                file_contents += f"\n--- {file_path} ---\n(New File)\n"

        prompt = f"""You are an expert software engineer generating a diff to apply a self-modification.
The user's high-level intent is:
{modification.proposal}
Reason: {modification.reason}
Hypothesis: {modification.hypothesis}
Expected Benefit: {modification.expected_benefit}
Expected Risk: {modification.expected_risk}

Here are the current contents of the affected files:
{file_contents}

Please output a valid, unified `git` diff (patch) that implements this modification.
ONLY output the raw diff, do not add any conversational text.
ONLY modify the files listed above. Do not modify any other files.
If you use markdown code blocks, wrap the diff in ```diff ... ```.
"""
        req = GenerationRequest(
            prompt=prompt,
            system_prompt="You generate strictly formatted git unified diff patches.",
            temperature=0.2
        )
        
        try:
            response = await planning_model.generate(req)
        except Exception as e:
            modification.metadata["apply_error"] = f"Model generation failed: {str(e)}"
            raise RuntimeError(f"Model generation failed: {str(e)}")
            
        diff_text = response.text
        if not diff_text.strip():
            modification.metadata["apply_error"] = "Model returned empty diff."
            raise RuntimeError("Model returned empty diff.")
            
        # Extract diff block
        import re
        match = re.search(r"```(?:diff)?\n(.*?)```", diff_text, re.DOTALL)
        if match:
            diff_text = match.group(1).strip()
        else:
            diff_text = diff_text.strip()
            
        patch_file = worktree_path / ".self-mod-patch.diff"
        with open(patch_file, "w") as f:
            f.write(diff_text + "\n")
            
        # First, dry run the apply
        try:
            subprocess.run(
                ["git", "apply", "--check", "--ignore-whitespace", str(patch_file)],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            modification.metadata["apply_error"] = f"Patch validation failed: {e.stderr}"
            raise RuntimeError(f"Patch validation failed: {e.stderr}")
            
        # If dry run succeeds, actually apply the patch
        try:
            subprocess.run(
                ["git", "apply", "--ignore-whitespace", str(patch_file)],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            modification.metadata["apply_error"] = f"Patch application failed: {e.stderr}"
            raise RuntimeError(f"Patch application failed: {e.stderr}")
        finally:
            # Clean up the patch file
            if patch_file.exists():
                patch_file.unlink()
    
    async def _run_tests(self, modification: ModificationRecord, worktree_path: Path) -> TestResult:
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            passed = result.returncode == 0
            
            return TestResult(
                passed=1 if passed else 0,
                failed=0 if passed else 1,
                duration_seconds=time.time() - start_time,
                test_details=[{"command": "pytest", "returncode": result.returncode, "stdout": result.stdout[:1000], "stderr": result.stderr[:1000]}]
            )
        except subprocess.TimeoutExpired:
            return TestResult(failed=1, test_details=[{"error": "Test timeout"}])
        except Exception as e:
            return TestResult(failed=1, test_details=[{"error": str(e)}])
    
    async def _run_benchmark(self, modification: ModificationRecord, worktree_path: Path, phase: str) -> BenchmarkResult:
        from app.models.base import get_model_registry, GenerationRequest
        model = get_model_registry().get("default")
        
        # CPU and Memory
        # Note: This measures the self-modification engine's own process, 
        # not the modified worktree code running standalone.
        import psutil
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.5)
        ram_mb = process.memory_info().rss / (1024 * 1024)
        
        # Inference Latency and Tokens
        start_time = time.time()
        try:
            req = GenerationRequest(prompt=BENCHMARK_PROBE_PROMPT, max_tokens=10)
            resp = await model.generate(req)
            latency_ms = (time.time() - start_time) * 1000
            tokens_gen = resp.tokens_generated
            tokens_per_second = tokens_gen / (latency_ms / 1000) if latency_ms > 0 else 0.0
            error_rate = 0.0
        except Exception as e:
            logger.error(f"Benchmark inference failed: {e}")
            latency_ms = float('inf')
            tokens_per_second = 0.0
            error_rate = 1.0
            
        try:
            context_tokens = await model.count_tokens(BENCHMARK_PROBE_PROMPT)
        except Exception:
            context_tokens = 0
        
        return BenchmarkResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            ram_mb=ram_mb,
            cpu_percent=cpu_percent,
            inference_latency_ms=latency_ms,
            tokens_per_second=tokens_per_second,
            context_tokens=context_tokens,
            test_passed=True,
            error_rate=0.0
        )
    
    def _evaluate_modification(self, modification: ModificationRecord) -> Dict[str, Any]:
        before = modification.benchmark_before
        after = modification.benchmark_after
        
        logger.info(f"Evaluating modification {modification.modification_id}")
        logger.info(f"Before: Latency={before.get('inference_latency_ms', 0):.2f}ms, RAM={before.get('ram_mb', 0):.2f}MB")
        logger.info(f"After:  Latency={after.get('inference_latency_ms', 0):.2f}ms, RAM={after.get('ram_mb', 0):.2f}MB")
        
        improvements = 0
        regressions = 0
        
        if after.get("inference_latency_ms", 0) < before.get("inference_latency_ms", float('inf')):
            improvements += 1
        elif after.get("inference_latency_ms", 0) > before.get("inference_latency_ms", 0):
            regressions += 1
        
        if after.get("ram_mb", float('inf')) < before.get("ram_mb", float('inf')):
            improvements += 1
        elif after.get("ram_mb", 0) > before.get("ram_mb", 0):
            regressions += 1
        
        should_apply = improvements > regressions and modification.test_results.get("failed", 1) == 0
        
        logger.info(f"Evaluation: Improvements={improvements}, Regressions={regressions}, Should Apply={should_apply}")
        
        return {
            "should_apply": should_apply,
            "improvements": improvements,
            "regressions": regressions,
            "test_passed": modification.test_results.get("passed", 0) > 0
        }
    
    async def _apply_to_main(self, modification: ModificationRecord) -> None:
        modification.status = ModificationStatus.APPLIED
        modification.applied_commit = await self._get_current_commit()
        modification.completed_at = datetime.now(timezone.utc).isoformat()
        self.evidence_manager.record_modification(modification)
        
        await self._cleanup_worktree(modification)
        
        self._cooldown_until = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        self._cooldown_until = self._cooldown_until.replace(minute=self._cooldown_until.minute + 10)
        
        self._active_modifications.pop(modification.modification_id, None)
        
        evidence = Evidence(
            session_id=modification.session_id,
            agent_id=modification.agent_id,
            evidence_type=EvidenceType.MODIFICATION_APPLIED,
            intent="Self-modification applied",
            reason=f"Modification {modification.modification_id} applied to main branch",
            action_details={"modification_id": modification.modification_id, "commit": modification.applied_commit},
            tags=["self-modification", "applied"]
        )
        self.evidence_manager._save_evidence(evidence)
    
    async def rollback_modification(self, modification_id: str) -> bool:
        modification = self._active_modifications.get(modification_id)
        if not modification or not modification.applied_commit:
            return False
        
        try:
            subprocess.run(
                ["git", "reset", "--hard", modification.baseline_commit],
                cwd=self.project_root,
                check=True,
                capture_output=True
            )
            
            modification.status = ModificationStatus.ROLLED_BACK
            modification.rollback_commit = await self._get_current_commit()
            modification.completed_at = datetime.now(timezone.utc).isoformat()
            self.evidence_manager.record_modification(modification)
            
            await self._cleanup_worktree(modification)
            self._active_modifications.pop(modification_id, None)
            
            evidence = Evidence(
                session_id=modification.session_id,
                agent_id=modification.agent_id,
                evidence_type=EvidenceType.MODIFICATION_ROLLBACK,
                intent="Self-modification rolled back",
                reason=f"Rolled back modification {modification_id}",
                action_details={"modification_id": modification_id, "commit": modification.rollback_commit},
                tags=["self-modification", "rollback"]
            )
            self.evidence_manager._save_evidence(evidence)
            
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    async def _cleanup_worktree(self, modification: ModificationRecord) -> None:
        worktree_path = self._worktrees.pop(modification.modification_id, None)
        if worktree_path and worktree_path.exists():
            try:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_path)],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                pass
    
    async def _get_current_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
    
    def get_active_modifications(self) -> List[ModificationRecord]:
        return list(self._active_modifications.values())
    
    def get_modification_history(self) -> List[ModificationRecord]:
        return list(self._active_modifications.values())


_self_modification_engine: Optional[SelfModificationEngine] = None


def get_self_modification_engine() -> SelfModificationEngine:
    global _self_modification_engine
    if _self_modification_engine is None:
        _self_modification_engine = SelfModificationEngine()
    return _self_modification_engine


def set_self_modification_engine(engine: SelfModificationEngine) -> None:
    global _self_modification_engine
    _self_modification_engine = engine