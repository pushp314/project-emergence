# SQLITE_DATABASE_ADDON.md

## PURPOSE

This addon formally adds SQLite as the local persistence layer of the A2A Autonomous AI Sandbox.

SQLite is the default V1 database.

The database must support long-running sessions, agent communication history, memory metadata, evidence, research, experiments, permissions, resource measurements, and recovery.

This addon extends:

- `RULES.md`
- `ARCHITECTURE.md`
- `AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md`
- `SELF_MODIFICATION_ADDON.md`
- `CLI_FIRST_INTERFACE_ADDON.md`
- `GITHUB_REPOSITORY_MAINTENANCE_ADDON.md`

---

# 1. DATABASE PRINCIPLE

Use SQLite for structured local state.

Do NOT introduce PostgreSQL, Redis, or another database server for V1 unless there is a demonstrated requirement.

The system should remain lightweight on:

```text
Apple M4
16 GB unified memory
macOS
```

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

# 2. UPDATED PERSISTENCE ARCHITECTURE

The architecture becomes:

```text
                         A2A SYSTEM
                              │
             ┌────────────────┼────────────────┐
             ↓                ↓                ↓
          Agents           Event Bus          Tools
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                     Persistence Layer
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
           SQLite         Filesystem          Git
              │               │               │
              │               │               └── Source/history
              │               │
              │               └── Large artifacts
              │                   audio
              │                   reports
              │                   research
              │                   snapshots
              │
              ├── Sessions
              ├── Events
              ├── Messages
              ├── Memory metadata
              ├── Evidence metadata
              ├── Research
              ├── Experiments
              ├── Permissions
              ├── Agent state
              ├── Resource metrics
              └── Modification records
```

SQLite is the structured state layer.

Filesystem is the large-object/artifact layer.

Git is the source-code/version-history layer.

Do not mix these responsibilities unnecessarily.

---

# 3. DATABASE LOCATION

Default:

```text
data/
└── sandbox.db
```

The exact path may be configurable.

Runtime data should NOT be stored inside source-code modules.

Recommended:

```text
ai-sandbox/
├── app/
├── tests/
├── docs/
├── data/
│   └── sandbox.db
├── evidence/
├── research/
├── experiments/
├── artifacts/
├── sessions/
└── ...
```

The runtime database should normally be excluded from Git unless the project explicitly decides otherwise.

---

# 4. DATABASE MUST NOT BECOME THE ONLY STORAGE SYSTEM

Do not store huge content blobs in SQLite unnecessarily.

Prefer:

```text
SQLite
→ structured metadata

Filesystem
→ large content/artifacts

Git
→ source/documentation/version history
```

For example:

A browser page:

```text
SQLite:
source ID
URL
title
timestamp
agent
claim IDs

Filesystem:
cached/extracted document if needed
```

An audio conversation:

```text
SQLite:
audio artifact ID
timestamp
session
duration
speaker metadata

Filesystem:
audio file
```

A generated report:

```text
SQLite:
report ID
session
created timestamp
path

Filesystem:
actual report
```

---

# 5. REQUIRED DATABASE ENTITIES

The initial schema should support at least:

```text
sessions
agents
conversations
messages
events
memory_items
research_sessions
research_sources
claims
evidence
experiments
experiment_results
permissions
tool_calls
artifacts
resource_metrics
modification_proposals
checkpoints
```

The implementation may normalize or combine tables where appropriate, but the conceptual entities must remain represented.

---

# 6. SESSIONS

A session represents one execution period.

Example:

```text
Session #001
```

Store:

- session ID
- start time
- end time
- status
- configuration reference
- model configuration
- project version/commit
- environment metadata
- summary
- recovery state

Possible statuses:

```text
RUNNING
PAUSED
COMPLETED
INTERRUPTED
FAILED
RECOVERABLE
```

---

# 7. AGENTS

Store agent identity and runtime state.

Fields may include:

```text
agent_id
name
role
model
status
created_at
last_active_at
configuration
```

Do not store full prompt/context history directly in the agent table.

Messages belong in the conversation/message system.

---

# 8. CONVERSATIONS

A conversation links agents and/or the human.

Store:

```text
conversation_id
session_id
participants
started_at
ended_at
status
summary
```

A single session may contain multiple conversations.

---

# 9. MESSAGES

Messages should preserve the A2A conversation history.

Store:

```text
message_id
conversation_id
session_id
sender
receiver
timestamp
message_type
content
correlation_id
metadata
```

Large payloads should be stored externally when necessary, with a reference in SQLite.

---

# 10. EVENT STORE

The Event Bus should persist important events.

Conceptually:

```text
Event Bus
   ↓
Event Store
   ↓
SQLite
```

Events should contain:

```text
event_id
session_id
timestamp
event_type
source
payload/reference
correlation_id
```

Examples:

```text
AGENT_MESSAGE
TOOL_CALL
TOOL_RESULT
RESEARCH_STARTED
SOURCE_FOUND
EVIDENCE_CREATED
PERMISSION_REQUESTED
PERMISSION_GRANTED
EXPERIMENT_STARTED
EXPERIMENT_COMPLETED
MODIFICATION_PROPOSED
MODIFICATION_APPLIED
RESOURCE_WARNING
SYSTEM_ERROR
```

The Event Store provides the durable timeline.

---

# 11. EVIDENCE

Evidence metadata belongs in SQLite.

Example:

```text
evidence_id
session_id
agent_id
source_id
claim
evidence_type
confidence
created_at
verification_status
artifact_reference
```

Large evidence documents remain in the filesystem.

The database stores relationships and provenance.

---

# 12. RESEARCH

Research should be queryable.

Store:

```text
research_session
research_question
agent
timestamp
status
```

Sources:

```text
source_id
research_id
url
title
publisher/domain
retrieved_at
content_reference
```

Claims:

```text
claim_id
research_id
claim
source_id
agent
confidence
verification_status
```

This allows the system to answer:

> What research did the agents perform during Session #001?

without scanning every file manually.

---

# 13. MEMORY

Memory should be separated conceptually into:

```text
Short-term context
Long-term memory
Research knowledge
Evidence
Session summaries
Open questions
```

SQLite should store memory metadata and retrieval indexes.

Do not blindly dump every conversation message into long-term memory.

Memory creation should be selective.

---

# 14. EXPERIMENTS

Store:

```text
experiment_id
session_id
agent_id
hypothesis
objective
status
started_at
completed_at
baseline_reference
result
conclusion
```

Experiment artifacts should be stored on the filesystem.

Benchmark metrics may be stored in SQLite.

---

# 15. PERMISSIONS

Store every permission request and decision.

Example:

```text
permission_id
session_id
agent_id
action
reason
risk
scope
requested_at
decision
decided_at
decided_by
```

Possible decisions:

```text
PENDING
APPROVED
DENIED
EXPIRED
REVOKED
```

This creates an auditable permission history.

---

# 16. TOOL CALLS

Every important tool invocation should be queryable.

Store:

```text
tool_call_id
session_id
agent_id
tool
operation
arguments_reference
started_at
completed_at
status
result_reference
permission_id
```

Do not store secrets in arguments or results.

Sensitive values must be redacted before persistence.

---

# 17. RESOURCE METRICS

Because this system runs on an M4 with 16 GB RAM, resource metrics should be persisted.

Possible metrics:

```text
timestamp
session_id
ram_used
ram_available
cpu_usage
gpu_usage
inference_latency
tokens_per_second
context_tokens
active_agents
active_model
queue_depth
```

Use sampling rather than storing excessive high-frequency data.

The goal is useful historical performance information without creating unnecessary database overhead.

---

# 18. MODIFICATION RECORDS

Self-modification proposals should be represented in SQLite.

Store:

```text
modification_id
session_id
agent_id
proposal
reason
branch
baseline_commit
status
benchmark_result
approval
applied_commit
rollback_commit
created_at
completed_at
```

This connects:

```text
Agent reasoning
      ↓
Modification
      ↓
Git
      ↓
Benchmark
      ↓
Database record
```

---

# 19. CHECKPOINTS

Create durable checkpoints for recoverable sessions.

Store:

```text
checkpoint_id
session_id
created_at
git_commit
database_state/reference
active_agents
pending_tasks
active_experiments
configuration_reference
```

This supports recovery after:

- process crash
- machine restart
- model failure
- manual interruption

---

# 20. TRANSACTIONS

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

# 21. CONCURRENCY

SQLite is sufficient for V1, but design access carefully.

Prefer:

- one database file
- short transactions
- WAL mode where appropriate
- connection management
- bounded writes
- asynchronous/event-driven persistence where practical

Do not create uncontrolled numbers of database connections.

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

# 23. DATABASE FAILURE

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

# 24. DATABASE BACKUPS

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

# 25. DATABASE INSPECTION

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

# 26. CLI INTEGRATION

The CLI should expose high-level database information.

Example:

```text
/status

Database:
SQLite
Path: data/sandbox.db
Status: Healthy
Size: 18.4 MB
WAL: Enabled
Last checkpoint: 06:42:13
```

Do not expose raw SQL to normal users unless a developer/debug mode is enabled.

---

# 27. MIGRATIONS

Database schema changes MUST be versioned.

Use a migration system rather than modifying production schema manually.

Example:

```text
migrations/
├── 001_initial.sql
├── 002_add_research.sql
├── 003_add_experiments.sql
└── 004_add_resource_metrics.sql
```

The exact migration framework may be chosen by the implementation agent.

Never silently change the schema without a migration/checkpoint.

---

# 28. DATABASE + GIT

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

# 29. DATABASE + MEMORY

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

# 30. DATABASE + MODEL CONTEXT

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

# 31. RESOURCE EFFICIENCY

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

# 32. DATA RETENTION

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

# 33. RECOVERY FLOW

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

# 34. UPDATED PERSISTENCE RESPONSIBILITIES

Use this rule:

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

# 35. ACCEPTANCE CRITERIA

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

# FINAL IMPLEMENTATION INSTRUCTION

Integrate SQLite into the existing architecture.

Do not redesign the entire project.

The resulting persistence model should be:

```text
                    A2A SANDBOX
                         │
                     Event Bus
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
           Agents      Tools     Control
              │          │          │
              └──────────┼──────────┘
                         ↓
                Persistence Layer
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
     SQLite          Filesystem          Git
        │                │                │
   Structured       Large/raw          Code/history
      state          artifacts
        │
        ↓
 Sessions / Memory / Evidence / Research /
 Experiments / Permissions / Metrics /
 Modifications / Checkpoints

                         ↓
                      GitHub
```

Keep SQLite local, lightweight, observable, migration-based, and model-independent.

Do not introduce PostgreSQL or a separate vector database until actual system requirements and benchmarks justify the added complexity.
