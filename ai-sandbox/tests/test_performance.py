"""Performance benchmark suite for ai-sandbox core components.

Run with: pytest tests/test_performance.py -m performance -v
"""
from __future__ import annotations

import asyncio
import gc
import os
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest

from app.events.bus import Event, EventBus, EventType
from app.evidence.manager import EvidenceManager
from app.evidence.schemas import Evidence, EvidenceType
from app.memory.context_manager import ContextManager
from app.memory.store import SQLiteStore, ConversationRecord, MemoryRecord, SummaryRecord
from app.orchestration.scheduler import (
    AdaptivePolicy,
    RoundRobinPolicy,
    Scheduler,
    create_scheduler,
)

ITERATIONS = 1000

pytestmark = pytest.mark.performance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event_bus() -> EventBus:
    return EventBus()


def _temp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


def _make_store(db_path: Optional[str] = None) -> SQLiteStore:
    return SQLiteStore(db_path or _temp_db())


class _FakeSummarizer:
    """Minimal summarizer stub that avoids LLM calls."""

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


# ---------------------------------------------------------------------------
# 1. EventBus publish / subscribe throughput
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_event_bus_throughput():
    bus = _make_event_bus()
    received: list[Event] = []

    async def _handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(EventType.AGENT_MESSAGE, _handler)

    async def _run() -> float:
        start = time.perf_counter()
        for _ in range(ITERATIONS):
            event = Event(
                type=EventType.AGENT_MESSAGE,
                conversation_id="bench",
                payload={"agent_id": "a1", "content": "hello"},
            )
            await bus.publish(event)
        elapsed = time.perf_counter() - start
        return elapsed

    loop = asyncio.new_event_loop()
    elapsed = loop.run_until_complete(_run())
    loop.close()

    events_per_sec = ITERATIONS / elapsed
    avg_us = (elapsed / ITERATIONS) * 1_000_000

    print(f"\n  EventBus: {ITERATIONS} publish in {elapsed:.4f}s "
          f"({events_per_sec:,.0f} events/s, {avg_us:.1f} µs avg)")

    assert len(received) == ITERATIONS, f"Expected {ITERATIONS} received, got {len(received)}"
    assert elapsed < 30.0, f"EventBus throughput too slow: {elapsed:.2f}s for {ITERATIONS} events"


# ---------------------------------------------------------------------------
# 2. SQLite write latency (evidence events)
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_sqlite_write_latency():
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
                    "2026-01-01T00:00:00", "", "bench", "benchmark write",
                    "{}", "{}", "{}", 0, None, "[]", "[]", "{}",
                ),
            )
        conn.commit()
        elapsed = time.perf_counter() - start
        conn.close()

        writes_per_sec = ITERATIONS / elapsed
        avg_us = (elapsed / ITERATIONS) * 1_000_000

        print(f"\n  SQLite writes: {ITERATIONS} inserts in {elapsed:.4f}s "
              f"({writes_per_sec:,.0f} writes/s, {avg_us:.1f} µs avg)")

        count = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        assert count == ITERATIONS
        assert elapsed < 10.0, f"SQLite writes too slow: {elapsed:.2f}s for {ITERATIONS} writes"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# 3. ContextManager update latency
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_context_manager_update_latency():
    store = _make_store()
    summarizer = _FakeSummarizer()
    ctx = ContextManager(store=store, summarizer=summarizer)

    async def _run() -> float:
        ctx.set_conversation("bench-ctx")

        start = time.perf_counter()
        for i in range(ITERATIONS):
            msg = Mock(
                agent_id=f"agent-{i % 3}",
                agent_identity="explorer",
                content=f"Message {i} with some content for benchmarking",
                turn_number=i + 1,
                timestamp="2026-01-01T00:00:00",
                metadata={},
                evidence_type="agent_action",
            )
            await ctx.update_from_message(msg, current_turn=i + 1)
        elapsed = time.perf_counter() - start
        return elapsed

    loop = asyncio.new_event_loop()
    elapsed = loop.run_until_complete(_run())
    loop.close()

    updates_per_sec = ITERATIONS / elapsed
    avg_us = (elapsed / ITERATIONS) * 1_000_000

    print(f"\n  ContextManager updates: {ITERATIONS} in {elapsed:.4f}s "
          f"({updates_per_sec:,.0f} updates/s, {avg_us:.1f} µs avg)")

    assert elapsed < 30.0, f"ContextManager updates too slow: {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# 4. Scheduler throughput (turn switching)
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_scheduler_throughput_round_robin():
    agents = ["explorer", "challenger", "observer"]
    sched = create_scheduler(agents, policy_name="round_robin")

    sched.start()

    start = time.perf_counter()
    for _ in range(ITERATIONS):
        sched.next_turn()
    elapsed = time.perf_counter() - start

    switches_per_sec = ITERATIONS / elapsed
    avg_ns = (elapsed / ITERATIONS) * 1_000_000_000

    print(f"\n  Scheduler (round_robin): {ITERATIONS} turns in {elapsed:.6f}s "
          f"({switches_per_sec:,.0f} switches/s, {avg_ns:.0f} ns avg)")

    assert elapsed < 1.0, f"Scheduler too slow: {elapsed:.4f}s for {ITERATIONS} turns"


@pytest.mark.performance
def test_scheduler_throughput_adaptive():
    agents = ["explorer", "challenger", "observer"]
    sched = create_scheduler(agents, policy_name="adaptive")

    sched.start()

    start = time.perf_counter()
    for _ in range(ITERATIONS):
        sched.next_turn()
    elapsed = time.perf_counter() - start

    switches_per_sec = ITERATIONS / elapsed
    avg_ns = (elapsed / ITERATIONS) * 1_000_000_000

    print(f"\n  Scheduler (adaptive): {ITERATIONS} turns in {elapsed:.6f}s "
          f"({switches_per_sec:,.0f} switches/s, {avg_ns:.0f} ns avg)")

    assert elapsed < 1.0, f"Adaptive scheduler too slow: {elapsed:.4f}s for {ITERATIONS} turns"


# ---------------------------------------------------------------------------
# 5. Memory usage per agent
# ---------------------------------------------------------------------------

@pytest.mark.performance
def test_memory_usage_per_agent():
    """Measure baseline memory cost of core agent-related objects."""
    import tracemalloc

    tracemalloc.start()

    bus = _make_event_bus()
    store = _make_store()
    summarizer = _FakeSummarizer()
    ctx = ContextManager(store=store, summarizer=summarizer)
    sched = create_scheduler(
        ["explorer", "challenger", "observer"], policy_name="round_robin"
    )

    snapshot_before = tracemalloc.take_snapshot()

    agents_data: list[dict] = []
    for i in range(100):
        agents_data.append({
            "agent_id": f"agent-{i}",
            "config": {"name": f"Agent {i}", "model": "llama3"},
            "bus": bus,
            "store": store,
            "context": ctx,
            "scheduler": sched,
        })

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)
    per_agent_bytes = total_bytes / max(len(agents_data), 1)
    per_agent_kb = per_agent_bytes / 1024

    print(f"\n  Memory: 100 agent descriptors = {total_bytes:,} bytes "
          f"({per_agent_kb:.2f} KB per agent)")

    assert per_agent_kb < 50.0, (
        f"Per-agent memory usage too high: {per_agent_kb:.2f} KB "
        f"(expected < 50 KB)"
    )


# ---------------------------------------------------------------------------
# Summary hook
# ---------------------------------------------------------------------------

def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Print a benchmark summary after all performance tests run."""
    perf_tests = [item for item in session.items if "performance" in item.keywords]
    if perf_tests:
        print(f"\n{'='*60}")
        print(f"  Benchmark suite complete: {len(perf_tests)} performance tests")
        print(f"{'='*60}\n")
