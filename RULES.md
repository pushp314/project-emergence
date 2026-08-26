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

---

# 2. REQUIRED READING BEFORE ANY WORK

Before implementing, modifying, debugging, or researching the codebase, every coding agent MUST read:

```text
RULES.md
ARCHITECTURE.md

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

Then inspect the actual repository and current Git state.

Do not rely on previous AI conversations as the source of truth.

---

# 3. SOURCE OF TRUTH

Priority:

```text
1. RULES.md
2. ARCHITECTURE.md
3. Addon specifications
4. PROJECT_STATE.md
5. DECISIONS.md
6. KNOWN_ISSUES.md
7. IMPLEMENTATION_LOG.md
8. CHANGELOG.md
9. Tests
10. Actual source code
11. Agent assumptions
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

# 4. NEVER START FROM ZERO

This is a persistent project.

A new agent MUST NOT assume the project is empty.

Before changing anything:

```text
Read rules
    ↓
Read architecture
    ↓
Read addons
    ↓
Read project state
    ↓
Inspect repository
    ↓
Inspect Git state
    ↓
Inspect tests
    ↓
Identify unfinished work
    ↓
Continue
```

Do NOT:

- recreate existing files
- rebuild completed features
- restart completed phases
- replace working architecture unnecessarily
- delete working components because a different implementation is preferred
- rewrite the project from scratch without explicit approval

---

# 5. PROJECT STATE

`PROJECT_STATE.md` is the primary implementation progress tracker.

It MUST describe the current state.

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

# 7. IMPLEMENTATION WORKFLOW

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

# 13. KNOWN ISSUES

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

# 14. CORE ARCHITECTURE BOUNDARIES

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

# 15. EVENT-DRIVEN DESIGN

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

# 16. AGENT COMMUNICATION

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

# 17. CONTINUOUS A2A CONVERSATION

The system should support:

```text
Agent A
   ↕
Event Bus
   ↕
Agent B
```

with continuous conversation until:

- human stops it
- system stops
- configured session condition occurs
- safety/resource condition requires stopping

The user must be able to inject a question or instruction while the agents continue.

Human interaction has priority.

---

# 18. HUMAN CONTROL

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

# 19. TOOL GATEWAY

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

# 20. BROWSER RESEARCH

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

# 21. EVIDENCE PLANE

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

# 22. MEMORY

Memory is separate from raw event history.

Conceptually:

```text
Raw Events
    ↓
Summarization / Selection
    ↓
Memory
```

Memory may contain:

- session summaries
- useful knowledge
- open questions
- decisions
- verified research
- important agent state

Do NOT dump the entire database or conversation history into every model context.

Retrieve only relevant information.

---

# 23. EXPERIMENT SYSTEM

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

# 24. PERMISSION SYSTEM

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

# 25. RESOURCE MANAGEMENT

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

# 26. MODEL RUNTIME

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

# 27. CONCURRENCY

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

# 28. PERSISTENCE ARCHITECTURE

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

# 29. SQLITE

SQLite is the default V1 database.

Do NOT introduce PostgreSQL, Redis, or another database server unless actual requirements or benchmarks justify it.

SQLite should store structured information such as:

```text
sessions
agents
conversations
messages
events
memory metadata
research
sources
claims
evidence metadata
experiments
experiment results
permissions
tool calls
artifacts metadata
resource metrics
modification proposals
checkpoints
```

The database should remain lightweight.

Use:

- migrations
- transactions
- sensible indexes
- bounded writes
- WAL where appropriate
- controlled connections
- safe backups

Do not load the entire database into model context.

---

# 30. SQLITE + FILESYSTEM

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

# 31. SQLITE + MEMORY

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
Compact context
 ↓
Model
```

Do not introduce a vector database until the system demonstrates a real need.

SQLite FTS/structured retrieval may be sufficient initially.

---

# 32. SQLITE + RECOVERY

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

Database failure must not be silently ignored.

Critical evidence must not be silently lost.

---

# 33. EXPERIMENTS + DATABASE

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

# 34. SELF-MODIFICATION

Self-modification follows:

```text
OBSERVE
 ↓
IDENTIFY PROBLEM
 ↓
RESEARCH
 ↓
HYPOTHESIS
 ↓
PROPOSE
 ↓
ISOLATE
 ↓
MODIFY
 ↓
TEST
 ↓
BENCHMARK
 ↓
DOCUMENT
 ↓
HUMAN APPROVAL
 ↓
APPLY
 ↓
MONITOR
 ↓
ROLLBACK IF NECESSARY
```

Self-modification must use isolated Git branches/worktrees.

Before risky modification:

```text
Known-good commit
+
Modification ID
+
Experiment record
+
Baseline metrics
```

The live system should not be casually rewritten by an agent.

---

# 35. CORE CONTROLS THAT SELF-MODIFICATION CANNOT REMOVE

Agents MUST NOT autonomously disable or remove:

- human interruption
- emergency shutdown
- permission gateway
- evidence logging
- audit logging
- rollback
- resource manager
- sandbox boundaries

Changes to these require explicit human approval.

---

# 36. GITHUB ENGINEERING LAYER

Git/GitHub is a permanent engineering history layer.

Normal workflow:

```text
Inspect
 ↓
Branch
 ↓
Implement
 ↓
Test
 ↓
Document
 ↓
Commit
 ↓
Push
 ↓
PR when useful
 ↓
Human review when required
 ↓
Merge
```

Use meaningful branches:

```text
feature/...
fix/...
research/...
experiment/...
self-modification/...
```

Do not work directly on `main` for risky experiments.

---

# 37. GIT COMMIT RULES

Before committing:

```text
git status
git diff
```

Verify:

- intended files only
- no secrets
- no credentials
- no accidental large files
- no temporary debug artifacts
- tests pass
- documentation is updated

Commit messages should explain the change:

```text
feat: add browser evidence pipeline
fix: handle model timeout
test: add agent interruption tests
perf: reduce repeated context serialization
docs: update research architecture
```

Do not use meaningless messages such as:

```text
update
stuff
final2
changes
```

---

# 38. GITHUB SECURITY

Never commit:

- passwords
- API keys
- access tokens
- SSH private keys
- browser cookies
- authentication data
- personal/private data
- secret `.env` files

Maintain a correct `.gitignore`.

Do not log secrets into:

- SQLite
- evidence
- Git
- GitHub
- model context

If a secret is accidentally exposed:

1. Stop.
2. Do not continue pushing.
3. Inform the human.
4. Rotate/revoke the secret.
5. Clean up appropriately.

---

# 39. PROTECTED GIT/GITHUB OPERATIONS

Require explicit authorization for:

- force push
- rewriting public history
- deleting important branches
- deleting repository
- changing visibility
- changing ownership
- changing collaborators
- changing repository security
- deleting important issues/releases
- destructive cleanup

Do not assume permission.

---

# 40. PULL REQUESTS

Meaningful changes may use PRs.

PRs should explain:

```text
What changed
Why
Architecture impact
Tests
Performance
Risks
Evidence
Rollback plan
```

Self-modification PRs should additionally include:

```text
Modification ID
Baseline commit
Hypothesis
Change
Benchmark
Result
Decision
```

---

# 41. GITHUB ISSUES

Use issues for significant:

- bugs
- research questions
- architectural decisions
- experiments
- long-running tasks
- blockers

Do not create unnecessary issue noise.

Useful labels:

```text
bug
feature
research
experiment
performance
architecture
security
documentation
self-modification
blocked
```

---

# 42. GITHUB AS AGENT HANDOFF

A future coding agent should be able to reconstruct the project using:

```text
RULES.md
ARCHITECTURE.md
Addons
PROJECT_STATE.md
CHANGELOG.md
DECISIONS.md
KNOWN_ISSUES.md
IMPLEMENTATION_LOG.md
Git history
GitHub Issues
GitHub PRs
Experiment records
SQLite state
```

The repository is the persistent handoff mechanism.

A future agent should not need the previous AI conversation.

---

# 43. CLI-FIRST INTERFACE

The core engine MUST NOT depend on a web UI.

CLI should eventually support:

```text
start
watch
interactive
status
agents
pause
resume
stop
sessions
session
memory
research
evidence
experiments
permissions
approve
deny
resources
logs
timeline
report
modifications
rollback
inject
db
help
```

A future web interface should consume the same core services.

---

# 44. VOICE

Voice is an interface layer:

```text
Microphone
 ↓
STT
 ↓
Event Bus
 ↓
Agents
 ↓
TTS
 ↓
Speaker
```

Voice must not become a dependency of the core runtime.

The user should still be able to operate the system entirely through CLI.

---

# 45. ERROR HANDLING

Never silently swallow exceptions.

Record when appropriate:

```text
timestamp
component
operation
error
context
recovery action
final state
```

Prefer graceful degradation.

If one agent fails, the whole system should not necessarily crash.

If browser research fails, agents should continue where possible.

---

# 46. RECOVERY

The system should recover from:

- model failures
- tool failures
- browser failures
- agent crashes
- malformed responses
- database failures
- process interruption
- machine restart
- incomplete sessions

Persist important state incrementally.

Do not wait until shutdown.

---

# 47. TESTING

Before marking a feature complete:

```text
Unit test
+
Integration test
+
Runtime test
+
Failure test
```

For critical components also test:

- interruption
- recovery
- malformed input
- concurrency
- resource pressure
- persistence failure

---

# 48. PERFORMANCE BENCHMARKING

For important changes, compare before and after when measurable.

Record:

```text
RAM
CPU
GPU
inference latency
tokens/sec
context tokens
tool latency
database latency
error rate
task completion
stability
```

Do not claim a performance improvement without evidence when measurement is available.

---

# 49. NO PREMATURE COMPLEXITY

The first system should remain:

- local
- understandable
- testable
- lightweight

Do not add:

- Kubernetes
- distributed infrastructure
- unnecessary microservices
- PostgreSQL
- vector databases
- complex orchestration frameworks

unless real requirements justify them.

---

# 50. SECURITY + FILESYSTEM

Agents should work inside the designated project/sandbox area by default.

Operations outside the expected workspace should go through the permission system where required.

Never allow arbitrary destructive filesystem operations without appropriate controls.

---

# 51. EXTERNAL ACTIONS

Distinguish:

```text
READ
WRITE
EXTERNAL ACTION
```

External actions such as:

- sending messages
- uploading data
- submitting forms
- installing software
- changing network settings
- interacting with external accounts

should be permission-controlled according to the project's permission policy.

---

# 52. AUTONOMOUS RESEARCH

Agents may independently research problems using browser/search tools.

Research should produce:

```text
Question
 ↓
Search
 ↓
Sources
 ↓
Extracted information
 ↓
Claims
 ↓
Verification
 ↓
Conclusion
 ↓
Evidence record
 ↓
Memory
```

Research is not complete merely because an agent found an answer.

Important claims should be traceable to evidence.

---

# 53. DOCUMENTATION AS PROOF

The system should maintain a permanent research/engineering record.

For every important activity, preserve where appropriate:

```text
What happened
When
Which agent
Why
What tool was used
What was discovered
What evidence supports it
What decision was made
What changed
What result occurred
```

Audio is optional.

Written records are the canonical proof.

---

# 54. SESSION MODEL

Every system run should have an `Experiment Session` or equivalent session record.

Example:

```text
Session #001

├── Start state
├── Participants/models
├── Configuration
├── Conversation
├── Decisions
├── Tool calls
├── Permission requests
├── Research
├── Experiments
├── Evidence
├── Artifacts
├── Results
├── Discoveries
└── Final report
```

The user should be able to inspect a session later.

---

# 55. SESSION CHECKPOINTING

Long-running sessions should checkpoint state incrementally.

Checkpoint should reference:

```text
SQLite state
Git commit
Active agents
Pending work
Experiments
Configuration
Important artifacts
```

A session must not depend entirely on process memory.

---

# 56. AGENT SELF-OBSERVATION

Agents may observe system state, but the Evidence Plane must remain independent.

Do not allow an agent to fabricate or rewrite its own historical evidence.

Agent claims are not automatically facts.

---

# 57. AGENT SELF-MODIFICATION

Agents may eventually propose changes to their own code according to `SELF_MODIFICATION_ADDON.md`.

However:

```text
Proposal ≠ Applied change
```

Every modification must have:

```text
Reason
Hypothesis
Isolation
Implementation
Tests
Benchmark
Evidence
Decision
Git checkpoint
```

---

# 58. RESOURCE-AWARE DEVELOPMENT

The coding agents themselves must also respect the M4 16 GB environment.

Avoid unnecessarily:

- starting multiple heavy services
- running duplicate model instances
- running large tests repeatedly
- leaving processes running
- generating huge logs
- repeating identical model calls
- rebuilding unnecessary components

Prefer targeted tests and incremental verification.

---

# 59. IMPLEMENTATION PHASES

Recommended order:

```text
Phase 1 — Foundation
[ ] project structure
[ ] configuration
[ ] event schemas
[ ] event bus

Phase 2 — Model Runtime
[ ] Ollama adapter
[ ] model abstraction
[ ] generation pipeline

Phase 3 — Agent Runtime
[ ] base agent
[ ] A2A messages
[ ] continuous A/B conversation

Phase 4 — Control + CLI
[ ] control plane
[ ] interruption
[ ] pause/resume
[ ] CLI

Phase 5 — Persistence
[ ] SQLite
[ ] migrations
[ ] sessions
[ ] events
[ ] messages
[ ] checkpoints

Phase 6 — Memory + Evidence
[ ] memory
[ ] evidence plane
[ ] provenance
[ ] research journal

Phase 7 — Tools
[ ] terminal
[ ] filesystem
[ ] browser
[ ] permission gateway

Phase 8 — Resource Management
[ ] RAM monitoring
[ ] inference metrics
[ ] scheduling
[ ] model routing

Phase 9 — Voice
[ ] STT
[ ] TTS
[ ] interruption

Phase 10 — Experiments
[ ] experiment system
[ ] benchmarks
[ ] artifact management

Phase 11 — Git/GitHub
[ ] branch workflow
[ ] automated checks
[ ] issue/PR integration
[ ] release workflow

Phase 12 — Self-Modification
[ ] proposals
[ ] isolated worktrees
[ ] tests
[ ] benchmarks
[ ] approval
[ ] rollback

Phase 13 — Advanced A2A
[ ] protocol
[ ] agent discovery
[ ] scalable routing

Phase 14 — Future Interface
[ ] API
[ ] optional web UI
```

The agent may change the order when justified, but MUST document why.

---

# 60. CONTINUATION PROTOCOL

When a new agent starts:

```text
1. Read RULES.md
2. Read PROJECT_STATE.md
3. Read relevant addons
4. Inspect repository
5. Inspect Git status/history
6. Inspect SQLite/database state if relevant
7. Run relevant tests
8. Identify exact next task
9. Implement
10. Test
11. Document
12. Checkpoint
13. Continue
```

Do not ask:

> What were we building?

The repository should answer it.

---

# 61. WHEN USER SAYS "CONTINUE"

Interpret:

> continue

as:

```text
Read rules
 ↓
Read project state
 ↓
Inspect repository
 ↓
Inspect Git
 ↓
Inspect database state if relevant
 ↓
Identify highest-priority unfinished task
 ↓
Implement
 ↓
Test
 ↓
Document
 ↓
Update state
 ↓
Checkpoint
 ↓
Continue
```

---

# 62. WHEN USER SAYS "READ RULES"

Immediately:

```text
Read RULES.md
Read PROJECT_STATE.md
Read relevant architecture/addons
Inspect repository
Continue from current state
```

Do not respond with a generic explanation.

Perform the work.

---

# 63. AMBIGUITY

When something is unclear, search the repository first:

```text
RULES
ARCHITECTURE
addons
PROJECT_STATE
DECISIONS
KNOWN_ISSUES
source
tests
Git history
```

Only ask the human when:

- a genuine product decision is required
- a permission is required
- an ambiguous destructive action is involved
- the repository does not contain enough information

---

# 64. AGENT FAILURE LOOP

If the same problem is attempted repeatedly without progress:

1. Stop repeating the same strategy.
2. Document the failed approach.
3. Inspect assumptions.
4. Create a smaller reproducible test.
5. Change strategy.
6. Measure the new approach.
7. Ask the human only if necessary.

Do not waste model inference and machine resources repeating identical failed attempts.

---

# 65. END-OF-SESSION PROTOCOL

Before stopping or handing work to another agent, update:

```text
PROJECT_STATE.md
IMPLEMENTATION_LOG.md
CHANGELOG.md
KNOWN_ISSUES.md
DECISIONS.md
```

If database/schema changes occurred:

```text
migrations
database documentation
PROJECT_STATE
```

If Git changes occurred:

```text
branch
commit
status
handoff
```

Then write:

```markdown
## Handoff

Completed:
...

Current state:
...

Known issues:
...

Next exact task:
...

Relevant files:
...

Relevant commit:
...

Database state:
...

Test command:
...

Expected next step:
...
```

---

# 66. GITHUB HANDOFF

Another coding agent should be able to continue using:

```text
RULES.md
PROJECT_STATE.md
ARCHITECTURE.md
addons
Git history
GitHub Issues/PRs
SQLite state
implementation logs
```

The system should not depend on a single AI provider.

The project must remain transferable between:

```text
Claude Code
Codex
OpenCode
Cursor
Antigravity
other coding agents
```

---

# 67. FINAL ENGINEERING PRINCIPLE

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
+
good orchestration
+
good tools
+
good memory
+
good evidence
+
good research
+
good engineering
+
resource efficiency
+
recoverability
```

---

# 68. DEFAULT INSTRUCTION FOR EVERY FUTURE CODING AGENT

Treat this as the default operating instruction:

> Read `RULES.md`, then read `PROJECT_STATE.md`, `ARCHITECTURE.md`, and all relevant addon documents. Inspect the actual repository, Git state, tests, and database state when relevant. Do not restart or recreate completed work. Determine the highest-priority unfinished task. Implement it incrementally. Test it. Measure important behavior. Update documentation, project state, database migrations when necessary, and Git history. Preserve evidence and rollback capability. Then provide a clear handoff and continue to the next task when appropriate.

---

# 69. ACCEPTANCE CRITERIA FOR THE OVERALL PROJECT

The project is progressing correctly when:

- [ ] Agents can communicate through structured events.
- [ ] Human can interrupt/control them.
- [ ] Browser research is traceable.
- [ ] Evidence is independently logged.
- [ ] Memory is persistent and selective.
- [ ] Sessions are recoverable.
- [ ] SQLite stores structured runtime state.
- [ ] Filesystem stores large artifacts.
- [ ] Git stores engineering history.
- [ ] GitHub provides remote continuity.
- [ ] Resource usage is observable.
- [ ] Model usage is resource-aware.
- [ ] Experiments are reproducible where practical.
- [ ] Self-modification is isolated and reversible.
- [ ] Permissions are auditable.
- [ ] Documentation survives agent changes.
- [ ] A new coding agent can continue without the previous conversation.
- [ ] The system remains usable on the M4 16 GB development machine.

---

# FINAL RULE

**Do not treat this project as a sequence of AI-generated code dumps.**

Treat it as a continuously evolving engineered system.

Every important cycle must leave behind:

```text
Working code
+
Tests
+
Evidence
+
Documentation
+
Persistent state
+
Git history
+
Recoverable checkpoint
```

The repository itself is the long-term memory of the project.
