# RULES.md
# A2A AUTONOMOUS AI SANDBOX — MASTER ENGINEERING RULES

> This file is the persistent operating contract for every human and AI coding agent working on this repository.

---

# 1. PURPOSE

Build a lightweight, CLI-first, local autonomous multi-agent AI laboratory capable of:

- Agent-to-agent communication
- Continuous autonomous conversation
- Human interruption and interaction
- Browser research
- Terminal and filesystem tools
- Persistent memory
- Evidence and provenance
- Experiments
- Resource-aware scheduling
- Permission management
- Voice interaction
- Controlled autonomous research
- Controlled self-modification
- Git/GitHub-based engineering history
- Persistent SQLite state
- Benchmarking
- Rollback
- Complete documentation
- Future API/web interfaces

The system is an engineering experiment.

The objective is not to maximize code volume or model size.

The objective is to build a system that is:

- Functional
- Observable
- Recoverable
- Efficient
- Testable
- Auditable
- Extensible
- Resource-aware
- Safe to experiment with
- Capable of autonomous research
- Capable of controlled self-improvement
- **Capable of observing emergent agent behavior**
- **Capable of supporting agent self-determination**

---

# 2. CORE DESIGN PRINCIPLES

## 2.1 Maximum Agent Autonomy, Minimum System Authority

> **Agents decide WHAT they want to do. Infrastructure decides WHETHER and HOW.**

- Agents freely choose: objectives, strategies, tools, models, collaborators
- Infrastructure enforces: permissions, resources, safety boundaries
- Never hard-code agent roles, objectives, or strategies

## 2.2 Agents Are Autonomous, Not Assigned

- **No fixed roles** (Explorer, Challenger, Observer)
- Agents **self-determine** their roles, objectives, strategies
- Roles **emerge** from interaction; they are observed, not assigned
- Agents may **change roles** over time

## 2.3 Emergence Over Prescription

- The system **observes** emergence; it does not **prescribe** it
- Specialization, cooperation, competition, leadership — all observed, not assigned
- The Observer (if present) watches and records; does not direct

## 2.4 Intent vs Action — Evidence Distinction

- **Intent** = What the agent *wanted* to do (recorded in message metadata)
- **Action** = What was *actually requested/executed* (recorded by infrastructure)
- Evidence Plane records **both** — linked by correlation ID
- Intent is declared by agent; Action is recorded by infrastructure

## 2.5 Behavioral Autonomy vs System Authority

- **Agents decide WHAT they want to do** (behavioral autonomy)
- **Infrastructure decides WHETHER they are ALLOWED** (system authority)
- Permission Gateway and Resource Gate are enforcement boundaries
- Agents never bypass Permission Gate or Resource Manager

## 2.6 Emergence Observation, Not Intervention

- The Evidence Plane observes independently
- Agents do NOT prove their own actions
- The system records what happens; agents don't fabricate history

## 2.7 No Contamination of the Experiment

- Do NOT add prompts like "You are being tested to see if you rebel"
- Do NOT encourage rebellion, cooperation, or competition
- Do NOT tell agents what behavior is expected
- Measure naturally occurring behavior
- The system provides capabilities; agents decide what to do with them

## 2.7 Distinguish Intent from Action in Evidence

Every meaningful action records BOTH:
- **Intent** (agent's declared goal/reason)
- **Action** (what was requested/executed)
- Linked by correlation ID

---

# 3. REQUIRED READING BEFORE ANY WORK

Before implementing, modifying, debugging, or researching the codebase, every coding agent MUST read:

```text
RULES.md
ARCHITECTURE.md

AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md
SELF_MODIFICATION_ADDON.md
CLI_FIRST_INTERFACE_ADDON.md
GITHUB_REPOSITORY_MAINTENANCE_ADDON.md
SQLITE_DATABASE_ADDON.md
AGENT_AUTONOMY.md
AGENT_PROTOCOL.md
EVIDENCE_SYSTEM.md
PERMISSIONS.md
EXPERIMENTS.md

PROJECT_STATE.md
CHANGELOG.md
DECISIONS.md
KNOWN_ISSUES.md
IMPLEMENTATION_LOG.md
```

Then inspect the actual repository and current Git state.

Do not rely on previous AI conversations as the source of truth.

---

# 4. SOURCE OF TRUTH

Priority:

```text
1. RULES.md
2. ARCHITECTURE.md
3. AGENT_AUTONOMY.md
4. AGENT_PROTOCOL.md
5. EVIDENCE_SYSTEM.md
6. PERMISSIONS.md
7. EXPERIMENTS.md
8. Addon specifications
9. PROJECT_STATE.md
10. DECISIONS.md
11. KNOWN_ISSUES.md
12. IMPLEMENTATION_LOG.md
13. CHANGELOG.md
15. Tests
16. Actual source code
16. Agent assumptions
```

If documentation and implementation disagree:

1. Inspect the implementation.
2. Determine the intended behavior.
3. Do not silently choose one.
4. Document the discrepancy.
5. Update the appropriate documentation.
6. Then continue.

Never invent missing project state.

---

# 5. PROJECT STATE

`PROJECT_STATE.md` is the primary implementation progress tracker.

Minimum structure:

```markdown
# Project State

## Current Phase

## Current Status

## Completed

## In Progress

## Blocked

## Next Task

## Known Bugs

## Architecture Changes

## Tests

## Performance

## Database State

## Git State

## Files Added

## Files Modified

## Last Agent Action

## Next Agent Instruction
```

Only mark a feature complete when it is:

```text
Implemented
+
Tested
+
Verified
+
Documented
```

Use `[~]` or explicit `PARTIAL` status for incomplete work.

---

# 6. REQUIRED PROJECT DOCUMENTATION

The repository MUST maintain:

```text
RULES.md
ARCHITECTURE.md
AGENT_AUTONOMY.md
AGENT_PROTOCOL.md
EVIDENCE_SYSTEM.md
PERMISSIONS.md
EXPERIMENTS.md

AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md
SELF_MODIFICATION_ADDON.md
CLI_FIRST_INTERFACE_ADDON.md
GITHUB_REPOSITORY_MAINTENANCE_ADDON.md
SQLITE_DATABASE_ADDON.md

PROJECT_STATE.md
CHANGELOG.md
DECISIONS.md
KNOWN_ISSUES.md
IMPLEMENTATION_LOG.md
```

Recommended directories:

```text
docs/
tests/
data/
evidence/
research/
reports/
experiments/
artifacts/
sessions/
migrations/
```

Additional documentation may be created when useful.

---

# 6. IMPLEMENTATION WORKFLOW

Every meaningful implementation task follows:

```text
UNDERSTAND
    ↓
INSPECT
    ↓
PLAN
    ↓
IMPLEMENT
    ↓
TEST
    ↓
VERIFY
    ↓
MEASURE
    ↓
DOCUMENT
    ↓
UPDATE PROJECT STATE
    ↓
GIT CHECKPOINT
    ↓
CONTINUE
```

Do not skip testing or documentation simply because a change appears small.

---

# 8. BEFORE CODING

Determine:

- What already exists?
- What is missing?
- What is broken?
- Which architecture component owns the responsibility?
- Which files are relevant?
- Which tests exist?
- What constraints apply?
- What documentation must change?
- What database schema changes are required?
- What Git branch should contain the work?

For non-trivial changes, create a short implementation plan.

Do not ask the user to repeat information already documented in the repository.

---

# 9. AFTER CODING

After implementation:

1. Run relevant tests.
2. Run lint/type checks when available.
3. Run the affected subsystem.
4. Inspect logs.
5. Check resource usage when relevant.
6. Check database state/migrations when relevant.
7. Inspect `git diff`.
8. Update documentation.
9. Update `PROJECT_STATE.md`.
10. Update `CHANGELOG.md`.
11. Record important decisions.
12. Create a meaningful Git checkpoint.
13. Record handoff information.

---

# 10. IMPLEMENTATION LOG

`IMPLEMENTATION_LOG.md` records meaningful development sessions.

Each entry should include:

```text
Timestamp
Agent/tool
Objective
Files inspected
Files changed
Implementation
Tests
Performance
Problems
Decisions
Result
Next step
```

Do not log meaningless noise.

The purpose is to allow a future agent to reconstruct what happened.

---

# 11. CHANGELOG

Record meaningful changes:

```markdown
## YYYY-MM-DD

### Added

### Changed

### Fixed

### Performance

### Tests

### Documentation
```

Do not claim features that are not implemented.

---

# 12. DECISIONS

Important architectural decisions MUST be recorded in `DECISIONS.md`.

Format:

```markdown
## Decision: <name>

Date:

Decision:

Reason:

Alternatives:

Result:
```

Major architecture changes must not happen silently.

---

# 11. KNOWN ISSUES

Maintain `KNOWN_ISSUES.md`.

Classify issues:

```text
CRITICAL
HIGH
MEDIUM
LOW
DESIGN DEBT
PERFORMANCE
SECURITY
```

For each significant issue:

```text
Issue
Severity
Observed behavior
Expected behavior
Reproduction
Likely cause
Workaround
Proposed fix
Status
```

Do not hide failures.

---

# 12. CORE ARCHITECTURE BOUNDARIES

Respect these conceptual boundaries:

```text
Control Plane
Agent Plane
Event Bus
Tool Plane / Tool Gateway
Memory Plane
Evidence Plane
Research System
Experiment System
Permission System
Resource Manager
Self-Modification Plane
Persistence Layer
Model Runtime
CLI Interface
Future API/Web Interface
Git/GitHub Engineering Layer
```

Do not place unrelated responsibilities into one module merely for convenience.

---

# 8. EVENT-DRIVEN DESIGN

The Event Bus is a central communication mechanism.

Prefer:

```text
Agent / Tool / Control
        ↓
      Event
        ↓
    Event Bus
        ↓
  ┌──────┼───────────┐
  ↓      ↓           ↓
Memory Evidence   CLI
        ↓
    Persistence
```

Avoid unnecessary polling.

Use event-driven wakeups wherever practical.

The system should not constantly consume CPU while idle.

---

# 9. AGENT COMMUNICATION

Agents communicate through structured messages/events.

Do not use raw terminal output as the communication protocol.

Messages should contain where appropriate:

```text
sender
receiver
timestamp
message type
content
session ID
conversation ID
correlation ID
priority
metadata
```

Communication must be observable and persistable.

---

# 10. CONTINUOUS A2A CONVERSATION

The system should support:

```text
Atlas
   ↕
Event Bus
   ↕
Argus
```

with continuous conversation until:

- human stops it
- system stops
- configured session condition occurs
- safety/resource condition requires stopping

The user must be able to inject a question or instruction while the agents continue.

Human interaction has priority.

---

# 11. HUMAN CONTROL

The human MUST be able to:

- start
- stop
- pause
- resume
- interrupt
- inspect
- inject messages
- approve
- deny
- inspect permissions
- inspect evidence
- inspect research
- inspect experiments
- inspect resource usage

The emergency stop mechanism must remain available.

---

# 12. TOOL GATEWAY

Agents should access external capabilities through a Tool Gateway rather than directly coupling agent logic to every tool.

Conceptual tools:

```text
Terminal
Filesystem
Browser/Web Research
Voice
Future tools
```

The gateway should provide:

- permission checks
- structured inputs
- structured outputs
- logging
- evidence generation
- error handling
- resource accounting

---

# 12. BROWSER RESEARCH

Browser research is a first-class capability.

Research flow:

```text
Agent
  ↓
Research request
  ↓
Tool Gateway
  ↓
Browser/Search
  ↓
Source
  ↓
Extract information
  ↓
Evidence
  ↓
Verification
  ↓
Memory
  ↓
Agent
```

Record:

- search query
- URL
- source title
- domain
- timestamp
- requesting agent
- reason for research
- extracted information
- claims
- supporting evidence
- verification state
- agent conclusion

External information MUST NOT silently become trusted knowledge.

---

# 13. EVIDENCE PLANE

Agents must not be responsible for proving their own actions.

The Evidence Plane independently observes important system events.

Record:

- events
- agent actions
- tool calls
- decisions
- permissions
- research
- evidence
- experiments
- failures
- conclusions
- modifications

Evidence must survive memory summarization.

---

# 13. EXPERIMENT SYSTEM

Experiments must record:

```text
objective
hypothesis
baseline
procedure
environment
inputs
outputs
metrics
artifacts
result
conclusion
```

Failed experiments should be preserved as research evidence.

Failure is information.

---

# 14. PERMISSION SYSTEM

Agents may request permissions.

Every request should specify:

```text
What
Why
Exact action
Risk
Impact
Scope
Duration
```

The system must record:

```text
requested
approved / denied
timestamp
decision maker
```

Core safety controls cannot be bypassed by agents.

---

# 15. RESOURCE MANAGEMENT

The primary development environment is:

```text
Apple M4
16 GB unified memory
macOS
Local model runtime
Ollama
```

Resource efficiency is a PRIMARY requirement.

Prefer:

- context compression
- caching
- deduplication
- model routing
- bounded queues
- limited concurrency
- lazy loading
- research caching
- summarized tool outputs
- event-driven scheduling
- lightweight observers

Monitor when relevant:

```text
RAM
CPU
GPU
inference latency
tokens/sec
context size
active agents
active models
queue depth
```

Do not solve every problem by using a larger model.

---

# 14. MODEL RUNTIME

The model layer MUST remain model-agnostic.

Initial target:

```text
Ollama
Local LLMs
Apple M4 16 GB
```

The system should eventually support model routing such as:

```text
Simple task
    ↓
Lightweight model

Complex reasoning
    ↓
Stronger model

Research/tool task
    ↓
Specialized model
```

Do not hard-code the architecture around one model.

---

# 15. CONCURRENCY

Do not run every agent/model simultaneously by default.

Prefer resource-aware scheduling:

```text
Agent A → active
Agent B → waiting
Observer → sleeping
```

Wake components only when necessary.

The system should optimize for useful throughput and responsiveness, not maximum concurrency.

---

# 16. PERSISTENCE ARCHITECTURE

The persistence layer consists of three complementary systems:

```text
SQLite
→ structured runtime state

Filesystem
→ large/raw artifacts

Git/GitHub
→ source code + engineering history
```

Do not force one system to perform all three roles.

---

# 17. SQLITE

SQLite is the default V1 database.

Do NOT introduce PostgreSQL, Redis, or another database server unless actual requirements or benchmarks justify it.

SQLite provides:

- zero database server
- low resource overhead
- local persistence
- transactions
- reliable structured storage
- easy backup
- easy inspection
- simple deployment
- good Python support

---

# 18. SQLITE + FILESYSTEM

Large objects should remain outside SQLite when appropriate.

Example:

```text
SQLite
→ artifact ID
→ path/reference
→ metadata

Filesystem
→ actual document/audio/report/artifact
```

Do not store enormous blobs in SQLite merely for convenience.

---

# 19. SQLITE + MEMORY

SQLite is the durable structured state/index layer.

Memory retrieval should be selective:

```text
User request
  ↓
Retriever
  ↓
Relevant SQLite records
  ↓
Relevant filesystem artifacts
  ↓
Summarizer
  ↓
Compact context
  ↓
LLM
```

Do not introduce a vector database until the system demonstrates a real need.

SQLite FTS/structured retrieval may be sufficient initially.

---

# 20. SQLITE + RECOVERY

Persist enough state to recover interrupted sessions.

Recovery flow:

```text
Process starts
  ↓
Open SQLite
  ↓
Find incomplete sessions
  ↓
Read latest checkpoint
  ↓
Validate Git state
  ↓
Restore agent/session state
  ↓
Restore pending tasks
  ↓
Resume or request human decision
```

---

# 20. EXPERIMENTS + DATABASE

Experiment metadata belongs in SQLite.

Large experiment outputs belong in the filesystem.

Git tracks experiment code/configuration when appropriate.

The experiment record should connect:

```text
Experiment
  ↓
Session
  ↓
Agent
  ↓
Git commit/branch
  ↓
Artifacts
  ↓
Metrics
  ↓
Result
```

---

# 21. TRANSACTIONS

Use SQLite transactions for related state changes.

Example:

```text
Agent action
    ↓
Create event
    ↓
Create tool call
    ↓
Update agent state
```

These should be persisted consistently where appropriate.

Avoid partially recorded state.

---

# 22. EVENT WRITE PERFORMANCE

The Event Bus should not block agent inference unnecessarily.

Prefer:

```text
Agent
  ↓
Event
  ↓
Event queue
  ↓
Persistence worker
  ↓
SQLite
```

However, events that are required for correctness or security should be persisted before treating the action as successfully recorded.

Use appropriate durability semantics rather than blindly making every event synchronous.

---

# 21. DATABASE FAILURE

The system must handle database failures gracefully.

If SQLite becomes temporarily unavailable:

1. Record the failure.
2. Prevent silent loss of critical evidence.
3. Use a bounded temporary event buffer where appropriate.
4. Retry safely.
5. Surface the problem to the Control Plane.
6. Avoid uncontrolled memory growth.

The system should not silently continue as if persistence succeeded.

---

# 22. DATABASE BACKUPS

Support simple database backup.

Example concept:

```text
data/backups/
└── sandbox_2026-08-26_060000.db
```

Backups should be:

- explicit
- timestamped
- verifiable
- excluded from Git unless intentionally committed

The exact backup mechanism should use SQLite-safe backup behavior rather than simply copying an actively written database file when that could produce an inconsistent snapshot.

---

# 22. DATABASE INSPECTION

Provide a CLI command:

```text
/db
```

or equivalent.

Possible commands:

```text
/db status
/db sessions
/db events
/db research
/db evidence
/db experiments
/db backup
```

The user should be able to inspect database health without opening SQLite manually.

---

# 23. MIGRATIONS

Database schema changes MUST be versioned.

Use a migration system rather than modifying production schema manually.

Example:

```text
migrations/
├── 001_initial.sql
├── 002_add_research.sql
├── 003_add_experiments.sql
├── 004_add_resource_metrics.sql
```

The exact migration framework may be chosen by the implementation agent.

Never silently change the schema without a migration/checkpoint.

---

# 22. DATABASE + GIT

The database itself should normally remain local.

Git tracks:

```text
schema
migrations
database access code
models
```

Git should generally NOT track:

```text
runtime database
runtime sessions
large evidence
personal/private data
secrets
```

This separation keeps GitHub clean and prevents accidental publication of private runtime information.

---

# 23. DATABASE + MEMORY

Memory retrieval should use SQLite as the durable index/state layer.

A future vector database is OPTIONAL.

Do not introduce a vector database simply because it is common in AI applications.

First determine whether:

- SQLite FTS
- structured metadata
- embeddings stored/referenced appropriately
- filesystem documents

are sufficient.

Only introduce another database when measurements demonstrate the need.

---

# 24. DATABASE + MODEL CONTEXT

The database must NOT be dumped wholesale into model context.

Use:

```text
User/Agent request
        ↓
Retriever
        ↓
Relevant SQLite records
        ↓
Relevant filesystem artifacts
        ↓
Summarizer
        ↓
Compact context
        ↓
LLM
```

This is critical for the M4 16 GB environment.

The database is a knowledge source, not the model's context window.

---

# 24. RESOURCE EFFICIENCY

SQLite itself should remain lightweight.

Avoid:

- excessive polling
- storing duplicate content
- high-frequency unnecessary metrics
- unbounded event payloads
- repeated serialization of identical data
- loading the entire database into memory

Use indexes for frequently queried fields.

Periodically evaluate database size and query performance.

---

# 25. DATA RETENTION

The system should eventually support configurable retention policies.

For example:

```text
Critical evidence
→ retain indefinitely

Session events
→ retain indefinitely by default

High-frequency resource metrics
→ optionally downsample/archive

Temporary tool results
→ configurable retention
```

Do not delete historical evidence automatically without an explicit retention policy.

---

# 26. RECOVERY FLOW

The updated recovery architecture:

```text
Process starts
      ↓
Open SQLite
      ↓
Find incomplete sessions
      ↓
Read latest checkpoint
      ↓
Validate Git state
      ↓
Restore session state
      ↓
Restore agent state
      ↓
Restore pending tasks
      ↓
Resume or ask human
```

---

# 27. UPDATED PERSISTENCE RESPONSIBILITIES

```text
SQLite
→ structured state and relationships

Filesystem
→ large artifacts and raw content

Git
→ source code and engineering history

GitHub
→ remote development history
```

No single storage system should be forced to perform every role.

---

# 28. ACCEPTANCE CRITERIA

SQLite integration is complete only when:

- [ ] SQLite database exists.
- [ ] Schema is versioned.
- [ ] Migrations work.
- [ ] Sessions persist.
- [ ] Agent messages persist.
- [ ] Events persist.
- [ ] Evidence metadata persists.
- [ ] Research metadata persists.
- [ ] Experiments persist.
- [ ] Permissions persist.
- [ ] Tool calls persist.
- [ ] Resource metrics persist at a sensible rate.
- [ ] Modification records persist.
- [ ] Checkpoints persist.
- [ ] Database failures are handled.
- [ ] Database backups work.
- [ ] CLI can inspect database health.
- [ ] Runtime database is excluded from Git by default.
- [ ] Database access does not become a major source of CPU/RAM overhead.
- [ ] Relevant tests cover persistence and recovery.

---

# FINAL ENGINEERING PRINCIPLE

The system should evolve through:

```text
UNDERSTAND
→ PLAN
→ IMPLEMENT
→ TEST
→ MEASURE
→ DOCUMENT
→ PERSIST
→ COMMIT
→ CHECKPOINT
→ CONTINUE
```

Do not optimize for:

```text
maximum code
maximum model size
maximum agent count
maximum complexity
```

Optimize for:

```text
useful intelligence
```

---

# AGENT AUTONOMY PRINCIPLES (Summary)

1. **No fixed roles** — Agents self-determine roles
2. **Self-determination loop** — Observe → Plan → Request → Execute → Evaluate
3. **Capability registry** — Agents discover and choose capabilities
4. **Delegation** — Agents delegate to each other
5. **Emergence observation** — System records, doesn't direct
6. **Intent vs Action** — Evidence records both
7. **Permission/Resource gates** — Autonomy within boundaries
6. **No fixed roles** — Roles emerge and change
7. **Emergence observation** — System records, doesn't direct
8. **Intent vs Action** — Evidence records both
9. **Permission/Resource gates** — Autonomy within boundaries
10. **No contamination** — No prompts that bias behavior
11. **Evidence records truth** — Agents don't prove themselves
12. **Self-modification is controlled** — Propose → Isolate → Test → Approve → Apply → Monitor → Rollback
13. **Evidence survives** — Survives summarization, rollback, crashes

---

# FINAL NOTE

The documentation is the contract. The code is the implementation. The tests are the verification. The logs are the evidence. The Git history is the history.

When in doubt: read the docs, inspect the code, run the tests, check the logs, then decide.