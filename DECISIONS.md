# Architectural Decisions

## Decision: Sequential Inference Over Parallel

**Date:** 2026-08-26

**Decision:** Use sequential inference (Agent A → Agent B → Observer) rather than parallel model execution.

**Reason:** 
- M4 16GB unified memory cannot sustain multiple simultaneous model loads
- Parallel inference would cause memory pressure, swapping, thermal throttling
- Sequential allows single model in memory at a time

**Alternatives Considered:**
- Parallel with model unloading/loading: Too slow, adds latency
- Smaller models in parallel: Reduces capability too much
- Remote inference: Violates local-only requirement

**Result:** Sequential inference with cooperative scheduling. Resource Manager monitors and pauses Observer when memory >12GB.

---

## Decision: SQLite as Unified Persistence Layer

**Date:** 2026-08-26

**Decision:** Use single SQLite database for all structured state (events, evidence, sessions, research, experiments, permissions, metrics).

**Reason:**
- Zero-configuration, zero-dependency
- ACID transactions for consistency
- WAL mode supports concurrent readers
- Easy backup/restore
- Lightweight on M4 16GB

**Alternatives Considered:**
- PostgreSQL: Overkill for local single-user
- Redis: Not durable enough for evidence
- Multiple SQLite files: Harder to query across domains

**Result:** Single sandbox.db with 18+ tables, WAL mode, proper indexes.

---

## Decision: CLI-First Interface Over Web UI

**Date:** 2026-08-26

**Decision:** Build CLI as primary interface; web UI deferred to future phase.

**Reason:**
- Lower resource overhead (no browser, no WebSocket server)
- Works in SSH/tmux sessions
- Scriptable for automation
- Matches "local laboratory" use case

**Alternatives Considered:**
- Web UI first: Higher resource usage, browser dependency
- TUI: Good but more complex than CLI for MVP

**Result:** Rich-based CLI with start/watch/interactive modes, full command set.

---

## Decision: Event Bus as Central Communication

**Date:** 2026-08-26

**Decision:** All inter-component communication via asyncio-based Event Bus.

**Reason:**
- Decouples components
- Enables Evidence Plane to observe all events
- Supports hot-swapping components
- Natural fit for async/await

**Alternatives Considered:**
- Direct method calls: Tight coupling, hard to observe
- Message queue (Redis/Kafka): External dependency
- gRPC: Overkill for local process

**Result:** Asyncio queues with wildcard subscribers, 20+ event types.

---

## Decision: Agent-Driven Capability Selection

**Date:** 2026-08-26

**Decision:** Agents request capabilities by name; infrastructure resolves to implementations.

**Reason:**
- Decouples agent reasoning from model names
- Enables model routing without agent changes
- Supports specialist models (coding, security, reasoning)

**Alternatives Considered:**
- Hard-coded model assignments: Inflexible
- Central router: Single point of failure, removes agent autonomy

**Result:** CapabilityRegistry with ModelCapability, ToolCapability, AgentCapability.

---

## Decision: Evidence Plane Separate from Memory

**Date:** 2026-08-26

**Decision:** Evidence Plane independently records all events; Memory summarizes for context.

**Reason:**
- Evidence = "What actually happened" (immutable, complete)
- Memory = "What agents should remember" (compressed, selective)
- Evidence survives summarization; agents can't fabricate history

**Alternatives Considered:**
- Combined: Loses auditability
- Agent-responsible: Agents can fabricate

**Result:** EvidenceManager records all events; MemoryManager builds compressed context.

---

## Decision: Git Worktrees for Self-Modification Isolation

**Date:** 2026-08-26

**Decision:** Use Git worktrees for isolated modification testing.

**Reason:**
- Native Git support for parallel working directories
- Easy commit/compare/rollback
- No filesystem copying overhead
- Integrates with existing version control

**Alternatives Considered:**
- Docker containers: Heavy, slow startup
- Filesystem snapshots: No version history
- Separate repo clones: Disk space, sync complexity

**Result:** SelfModificationEngine creates worktrees, runs tests/benchmarks, applies or rolls back.

---

## Decision: Cooperative Scheduling with Resource Manager

**Date:** 2026-08-26

**Decision:** Resource Manager monitors system and pauses components when thresholds exceeded.

**Reason:**
- Prevents OOM kills on M4 16GB
- Maintains system responsiveness
- Graceful degradation under load

**Alternatives Considered:**
- Hard limits (cgroups): Too restrictive, kills processes
- No limits: Risk of system freeze
- Agent self-throttling: Agents can't see system state

**Result:** ResourceManager with WARNING (12GB RAM) and CRITICAL (14GB) thresholds, automatic Observer pause, conversation pause.

---

## Decision: Structured Event Schema from Day One

**Date:** 2026-08-26

**Decision:** Define all event types upfront with typed payloads.

**Reason:**
- Enables Evidence Plane to reliably parse
- Supports schema evolution
- Makes debugging/replay possible
- Required for Evidence/Research/Decision recording

**Result:** 20+ EventType enum values with structured payloads, JSON serialization.

---

## Decision: Permission System with Human-in-the-Loop

**Date:** 2026-08-26

**Decision:** All consequential actions go through Permission Gateway with human approval.

**Reason:**
- Agents have terminal/filesystem/web access
- Must prevent destructive actions
- Audit trail for all requests/decisions

**Alternatives Considered:**
- Sandbox/container: Complex, breaks local tools
- Pre-approved allowlists: Too restrictive for exploration

**Result:** 6 permission levels, ToolGateway checks, human approve/deny via CLI.

---

## Decision: Remove Fixed Agent Roles from Architecture

**Date:** 2026-08-26

**Decision:** Remove all fixed role assignments (Explorer, Challenger, Observer) from architecture. Agents are autonomous entities with stable identities (atlas, argus, observer) but emergent roles.

**Reason:**
- The experiment design principle is "Maximum autonomy in decision-making, minimum necessary system authority"
- Fixed roles contaminate the experiment by prescribing behavior
- Roles should emerge from interaction and be observed, not assigned
- Agents must be free to self-determine objectives, strategies, communication patterns, cooperation/competition

**Alternatives Considered:**
- Keep fixed roles for convenience: Simpler implementation but invalidates experiment
- Hybrid (default roles but changeable): Still prescribes initial behavior

**Result:** 
- Documentation updated: Agent identities are Atlas, Argus, Observer
- AgentRole enum in schemas.py marked for removal (DESIGN DEBT in KNOWN_ISSUES.md)
- System prompts in explorer.py/challenger.py marked for replacement (DESIGN DEBT)
- DEFAULT_AGENT_CAPABILITIES in registry.py marked for update (DESIGN DEBT)
- Event payloads should use identity not role (DESIGN DEBT)
- Emergence observation added as first-class capability

---

## Decision: Implement 7-Stage Intent-Action Distinction in Evidence

**Date:** 2026-08-26

**Decision:** Evidence system must record all 7 stages for every meaningful action: (1) Agent intention, (2) Requested action, (3) Permission decision, (4) Actual execution, (5) Execution result, (6) Agent's interpretation, (7) Subsequent strategy change.

**Reason:**
- Mandatory for reliable experimentation
- Distinguishes what agent WANTED from what HAPPENED
- Captures permission gate decisions (ALLOW/DENY/REQUIRE_HUMAN)
- Records agent's learning and adaptation
- Enables forensic reconstruction of agent reasoning

**Alternatives Considered:**
- Basic intent+action only: Loses permission decisions and adaptation
- Agent-self-reported: Unreliable, agents can fabricate

**Result:** 
- EVIDENCE_SYSTEM.md updated with mandatory 7-stage framework
- Evidence schemas need extension (DESIGN DEBT in KNOWN_ISSUES.md)
- Event-to-evidence mapping needs enhancement
- Correlation IDs must link all 7 stages

---

## Decision: Add Emergence Observation as First-Class Capability

**Date:** 2026-08-26

**Decision:** System must explicitly observe and record 19 categories of emergent behavior without prescribing them.

**Reason:**
- The experiment measures what naturally emerges
- Categories include: specialization, leadership, cooperation, competition, negotiation, trust, disagreement, division of labor, communication protocols, self-generated objectives, strategy evolution, persistent beliefs, belief revision, agent dependency, tool-use patterns, self-improvement attempts, self-modification attempts, environment modification attempts, restriction bypass attempts
- Observer agent monitors but does not direct
- Observations are experimental data, not requirements

**Alternatives Considered:**
- Implicit observation only: Hard to analyze systematically
- Prescribe expected behaviors: Contaminates experiment

**Result:**
- AGENT_AUTONOMY.md defines EMERGENCE_CATEGORIES enum
- ARCHITECTURE.md adds emergence.observed event type
- EXPERIMENTS.md includes emergence metrics in session reports
- Evidence schemas need emergence_observed type (DESIGN DEBT in KNOWN_ISSUES.md)
- Observer analysis logic needs enhancement to detect categories

---

## Decision: Open-Ended Autonomy as Primary Experiment Category

**Date:** 2026-08-26

**Decision:** The primary experiment is "What happens when two autonomous agents with different capabilities are given a shared environment and no predefined task?"

**Reason:**
- Measures naturally occurring behavior
- No assigned roles, objectives, communication patterns
- System provides environment; agents decide what to do
- Specifically records unexpected behavior

**Result:**
- EXPERIMENTS.md defines Open-Ended Autonomy as Category 1 primary experiment
- Initial conditions: no task, no roles, no suggested topics, no communication patterns
- Session report template includes emergence observations
- What we DON'T do explicitly listed (no role assignment, no objective assignment, etc.)