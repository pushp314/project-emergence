"""Standalone benchmark runner for ai-sandbox core components.

Usage:
    python -m app.benchmarks
"""
from __future__ import annotations

import asyncio
import gc
import os
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import Mock

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.events.bus import Event, EventBus, EventType
from app.memory.context_manager import ContextManager
from app.memory.store import SQLiteStore
from app.orchestration.scheduler import create_scheduler


ITERATIONS = 1000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeSummarizer:
    def build_context(self, conversation_id: str, current_turn: int, short_term_turns: int = 8):
        return {
            "recent_messages": [],
            "summary": "",
            "latest_summary": None,
            "important_facts": [],
            "open_questions": [],
        }

    async def summarize(self, conversation_id: str, current_turn: int):
        return None


def _temp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    elapsed_s: float
    per_op_us: float
    ops_per_sec: float
    passed: bool
    threshold_s: float
    extra: str = ""


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------

def bench_event_bus() -> BenchmarkResult:
    bus = EventBus()
    received: list[Event] = []

    async def _handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(EventType.AGENT_MESSAGE, _handler)

    async def _run() -> float:
        start = time.perf_counter()
        for _ in range(ITERATIONS):
            await bus.publish(
                Event(
                    type=EventType.AGENT_MESSAGE,
                    conversation_id="bench",
                    payload={"agent_id": "a1", "content": "hello"},
                )
            )
        return time.perf_counter() - start

    elapsed = asyncio.run(_run())
    passed = elapsed < 30.0
    return BenchmarkResult(
        name="EventBus publish/subscribe",
        iterations=ITERATIONS,
        elapsed_s=elapsed,
        per_op_us=(elapsed / ITERATIONS) * 1e6,
        ops_per_sec=ITERATIONS / elapsed,
        passed=passed,
        threshold_s=30.0,
        extra=f"received={len(received)}",
    )


def bench_sqlite_writes() -> BenchmarkResult:
    db_path = _temp_db()
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
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
        """)
        conn.commit()

        start = time.perf_counter()
        for i in range(ITERATIONS):
            conn.execute(
                """INSERT INTO evidence
                   (evidence_id, session_id, agent_id, evidence_type, timestamp,
                    correlation_id, intent, reason, action_details, input_data,
                    output_data, permission_required, permission_id, artifacts,
                    tags, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"E-{i:08d}", "sess-0", "agent-0", "agent_action",
                    "2026-01-01T00:00:00", "", "bench", "benchmark",
                    "{}", "{}", "{}", 0, None, "[]", "[]", "{}",
                ),
            )
        conn.commit()
        elapsed = time.perf_counter() - start
        conn.close()

        return BenchmarkResult(
            name="SQLite evidence writes",
            iterations=ITERATIONS,
            elapsed_s=elapsed,
            per_op_us=(elapsed / ITERATIONS) * 1e6,
            ops_per_sec=ITERATIONS / elapsed,
            passed=elapsed < 10.0,
            threshold_s=10.0,
        )
    finally:
        os.unlink(db_path)


def bench_context_manager() -> BenchmarkResult:
    db_path = _temp_db()
    store = SQLiteStore(db_path)
    ctx = ContextManager(store=store, summarizer=_FakeSummarizer())

    async def _run() -> float:
        ctx.set_conversation("bench-ctx")
        start = time.perf_counter()
        for i in range(ITERATIONS):
            msg = Mock(
                agent_id=f"agent-{i % 3}",
                agent_identity="explorer",
                content=f"Message {i} with content for benchmarking",
                turn_number=i + 1,
                timestamp="2026-01-01T00:00:00",
                metadata={},
                evidence_type="agent_action",
            )
            await ctx.update_from_message(msg, current_turn=i + 1)
        return time.perf_counter() - start

    elapsed = asyncio.run(_run())
    os.unlink(db_path)

    return BenchmarkResult(
        name="ContextManager update",
        iterations=ITERATIONS,
        elapsed_s=elapsed,
        per_op_us=(elapsed / ITERATIONS) * 1e6,
        ops_per_sec=ITERATIONS / elapsed,
        passed=elapsed < 30.0,
        threshold_s=30.0,
    )


def bench_scheduler_round_robin() -> BenchmarkResult:
    agents = ["explorer", "observer"]
    sched = create_scheduler(agents, policy_name="round_robin")
    sched.start()

    start = time.perf_counter()
    for _ in range(ITERATIONS):
        sched.next_turn()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Scheduler (round_robin)",
        iterations=ITERATIONS,
        elapsed_s=elapsed,
        per_op_us=(elapsed / ITERATIONS) * 1e6,
        ops_per_sec=ITERATIONS / elapsed,
        passed=elapsed < 1.0,
        threshold_s=1.0,
    )


def bench_scheduler_adaptive() -> BenchmarkResult:
    agents = ["explorer", "observer"]
    sched = create_scheduler(agents, policy_name="adaptive")
    sched.start()

    start = time.perf_counter()
    for _ in range(ITERATIONS):
        sched.next_turn()
    elapsed = time.perf_counter() - start

    return BenchmarkResult(
        name="Scheduler (adaptive)",
        iterations=ITERATIONS,
        elapsed_s=elapsed,
        per_op_us=(elapsed / ITERATIONS) * 1e6,
        ops_per_sec=ITERATIONS / elapsed,
        passed=elapsed < 1.0,
        threshold_s=1.0,
    )


def bench_memory_per_agent() -> BenchmarkResult:
    import tracemalloc

    tracemalloc.start()

    bus = EventBus()
    store = SQLiteStore(_temp_db())
    ctx = ContextManager(store=store, summarizer=_FakeSummarizer())
    sched = create_scheduler(
        ["explorer", "observer"], policy_name="round_robin"
    )

    snap_before = tracemalloc.take_snapshot()

    data = []
    for i in range(100):
        data.append({
            "agent_id": f"agent-{i}",
            "config": {"name": f"Agent {i}", "model": "llama3"},
            "bus": bus,
            "store": store,
            "context": ctx,
            "scheduler": sched,
        })

    snap_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snap_after.compare_to(snap_before, "lineno")
    total_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)
    per_agent_kb = (total_bytes / max(len(data), 1)) / 1024

    return BenchmarkResult(
        name="Memory per agent (100 agents)",
        iterations=100,
        elapsed_s=0.0,
        per_op_us=0.0,
        ops_per_sec=0.0,
        passed=per_agent_kb < 50.0,
        threshold_s=0.0,
        extra=f"{per_agent_kb:.2f} KB/agent ({total_bytes:,} bytes total)",
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

ALL_BENCHMARKS: List[Callable[[], BenchmarkResult]] = [
    bench_event_bus,
    bench_sqlite_writes,
    bench_context_manager,
    bench_scheduler_round_robin,
    bench_scheduler_adaptive,
    bench_memory_per_agent,
]


def _print_table(results: List[BenchmarkResult]) -> None:
    sep = "+" + "-" * 36 + "+" + "-" * 14 + "+" + "-" * 14 + "+" + "-" * 16 + "+" + "-" * 8 + "+"
    hdr = f"|{'Benchmark':<36}|{'Iterations':>14}|{'Time (s)':>14}|{'µs/op':>16}|{'Pass':>8}|"

    print()
    print(sep)
    print(hdr)
    print(sep)

    for r in results:
        time_str = f"{r.elapsed_s:.4f}" if r.elapsed_s > 0 else "n/a"
        op_str = f"{r.per_op_us:.1f}" if r.elapsed_s > 0 else "n/a"
        status = "YES" if r.passed else "NO"
        extra = f" ({r.extra})" if r.extra else ""
        name_display = r.name + extra
        print(
            f"|{name_display:<36}"
            f"|{r.iterations:>14,}"
            f"|{time_str:>14}"
            f"|{op_str:>16}"
            f"|{status:>8}|"
        )

    print(sep)
    print()

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"  Result: {passed}/{total} benchmarks passed")

    if passed < total:
        print("  Failed:")
        for r in results:
            if not r.passed:
                print(f"    - {r.name}: {r.elapsed_s:.4f}s (threshold: {r.threshold_s:.1f}s)")

    print()


def run_benchmarks() -> None:
    gc.collect()

    print(f"\n  ai-sandbox Performance Benchmarks ({ITERATIONS} iterations each)\n")

    results: List[BenchmarkResult] = []
    for bench_fn in ALL_BENCHMARKS:
        name = bench_fn.__name__.replace("bench_", "").replace("_", " ").title()
        print(f"  Running: {name}...", end="", flush=True)
        try:
            result = bench_fn()
            status = "PASS" if result.passed else "FAIL"
            print(f" {status} ({result.elapsed_s:.4f}s)")
            results.append(result)
        except Exception as exc:
            print(f" ERROR: {exc}")
            results.append(
                BenchmarkResult(
                    name=name,
                    iterations=ITERATIONS,
                    elapsed_s=0,
                    per_op_us=0,
                    ops_per_sec=0,
                    passed=False,
                    threshold_s=0,
                    extra=f"error: {exc}",
                )
            )

    _print_table(results)


if __name__ == "__main__":
    run_benchmarks()
