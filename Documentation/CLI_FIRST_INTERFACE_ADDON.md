# AUTONOMOUS AI SANDBOX — CLI-FIRST INTERFACE ADDON

## STATUS

MANDATORY ARCHITECTURE ADDON

This document extends:

1. ARCHITECTURE.md
2. AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md
3. SELF_MODIFICATION_ADDON.md

The implementation agent MUST read all four documents before implementation.

This addon defines the user-interface strategy.

The system MUST be CLI-first.

A web interface is a future presentation layer and MUST NOT become a dependency of the core agent runtime.

---

# 1. CORE PRINCIPLE

The Autonomous AI Sandbox is fundamentally an agent runtime.

The CLI is the primary interface.

The architecture MUST NOT depend on:

- React
- browser UI
- frontend JavaScript
- WebSockets
- web dashboards
- graphical interfaces

for core functionality.

The complete agent system must be capable of running from a terminal.

Example:

ai-sandbox start

The agents, memory, tools, browser research, evidence system, permissions, resource manager, experiments, and self-modification system must continue functioning without a web UI.

---

# 2. CLI-FIRST ARCHITECTURE

Use this conceptual architecture:

                    CLI
                     │
                     ↓
              CLI Interface
                     │
                     ↓
               Core Engine
                     │
                 Event Bus
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
     Agents        Tools        Memory
        │            │            │
        └────────────┼────────────┘
                     ↓
              Evidence Plane
                     │
              Self-Modification
                     │
                     ↓
                  macOS

The CLI is only an interface.

It MUST NOT contain business logic.

---

# 3. CORE ENGINE MUST BE UI-INDEPENDENT

The core engine must expose programmatic interfaces that can later be consumed by:

- CLI
- Web UI
- REST API
- TUI
- external A2A clients
- automation systems

Example:

CLI
 ↓
Core API
 ↓
Conversation Manager

Later:

Web UI
 ↓
Core API
 ↓
Conversation Manager

Both interfaces must use the same underlying system.

Do NOT duplicate agent logic between CLI and web implementations.

---

# 4. TERMINAL EXPERIENCE

The CLI should make the system feel like an actual autonomous AI laboratory.

Example:

╭──────────────────────────────────────────────╮
│ AUTONOMOUS AI SANDBOX                        │
│ Session: #0001                               │
│ Model: Qwen                                  │
│ RAM: 10.4 / 16 GB                            │
│ Inference: 14.2 tok/s                        │
╰──────────────────────────────────────────────╯

[A] EXPLORER

I think we should investigate distributed inference.

[B] CHALLENGER

Before doing that, we should determine whether inference
or memory bandwidth is actually our bottleneck.

[Observer]
Potential disagreement detected.

[Research]
Searching: Apple Silicon LLM inference bottleneck...

[Evidence]
E-00042 created.

[Agent A]
I found three relevant sources.

──────────────────────────────────────────────

YOU >

---

# 5. LIVE EVENT STREAM

The CLI should display important events in real time.

Examples:

[09:31:02] Agent A → Agent B
[09:31:15] Agent B → Agent A
[09:31:42] Browser search
[09:31:51] Source opened
[09:32:03] Evidence created
[09:32:15] Memory updated
[09:33:02] Experiment started
[09:33:41] Permission requested
[09:34:10] Human approved
[09:35:12] Experiment completed

The user should be able to observe the system without opening a browser.

---

# 6. USER INPUT

The CLI must allow the human to enter input at any time.

Example:

YOU >

The human may:

- ask questions
- interrupt agents
- change direction
- request status
- approve permissions
- deny permissions
- pause agents
- resume agents
- stop the system
- inspect evidence
- inspect research
- inspect experiments
- inspect modifications

Human input has priority over normal agent conversation.

---

# 7. REQUIRED CLI COMMANDS

Implement a command system.

Minimum commands:

/help
/status
/agents
/pause
/resume
/stop
/restart
/session
/sessions
/memory
/research
/evidence
/experiments
/permissions
/approve
/deny
/tools
/resources
/logs
/timeline
/report
/modifications
/rollback
/inject

Commands may evolve, but equivalent functionality must exist.

---

# 8. STATUS COMMAND

/status should provide a concise system overview.

Example:

SYSTEM STATUS

Session:
#0042

Runtime:
Running

Agents:
A: Thinking
B: Waiting
C: Sleeping

Model:
Qwen

RAM:
10.8 / 16 GB

CPU:
61%

Inference:
14.8 tok/s

Context:
6,200 tokens

Tools:
Web: Available
Terminal: Available
Filesystem: Available

Permissions:
Pending: 1

Research:
Active

Experiments:
0

---

# 9. RESOURCE MONITOR

Because the system runs on an Apple M4 with 16 GB unified memory, resource information must be visible from the CLI.

Display:

- RAM usage
- CPU usage
- GPU usage where available
- inference speed
- context size
- model state
- active agents
- tool activity
- queue length
- resource warnings

Example:

[RESOURCE WARNING]

Memory usage:
14.2 / 16 GB

Recommended action:
Pause observer inference.

The system should automatically adapt when resource pressure increases.

---

# 10. VOICE SUPPORT

CLI-first does NOT mean text-only.

Voice should be implemented as an optional interface layer.

Architecture:

Microphone
    ↓
STT
    ↓
Core Event Bus
    ↓
Agents
    ↓
TTS
    ↓
Speaker

The core engine MUST NOT depend on voice.

If STT/TTS is disabled, the complete system must continue operating through the CLI.

---

# 11. LIVE CONVERSATION MODE

Provide a mode where the user can simply observe.

Example:

ai-sandbox watch

Output:

[Agent A]
I think we should investigate...

[Agent B]
I disagree because...

[Agent A]
Let's research that.

[Browser]
Searching...

[Evidence]
Source recorded.

[Agent B]
The evidence suggests...

The user should not need to interact unless desired.

---

# 12. INTERACTIVE MODE

Provide:

ai-sandbox

or:

ai-sandbox interactive

Example:

AUTONOMOUS AI SANDBOX

Session #001

YOU >

The user can type:

Why are you researching this?

or:

/status

or:

/pause

or:

/approve 42

The agents continue independently when the user does not intervene.

---

# 13. PERMISSION UI IN CLI

Permission requests must be highly visible.

Example:

╭──────────────────────────────────────────────╮
│ PERMISSION REQUEST                           │
├──────────────────────────────────────────────┤
│ Agent: A                                     │
│ Action: Install package                      │
│                                              │
│ Reason:                                      │
│ Required for experiment #007.               │
│                                              │
│ Command:                                     │
│ brew install example-package                │
│                                              │
│ Risk: Modifies installed software.           │
╰──────────────────────────────────────────────╯

Allow once? [y/N]

The permission request must also be recorded by the Evidence Plane.

---

# 14. HUMAN INTERRUPT

The user must be able to interrupt the agents immediately.

Examples:

Ctrl+C

or:

/interrupt

The interruption system must be handled by the Control Plane.

Do not rely solely on killing the process.

The system should attempt graceful interruption:

CURRENT GENERATION
        ↓
INTERRUPT
        ↓
SAVE STATE
        ↓
SAVE EVENT
        ↓
PAUSE

The user can then:

/resume

---

# 15. GRACEFUL SHUTDOWN

When the user executes:

/stop

the system must:

1. Stop new agent turns.
2. Stop active generation where possible.
3. Finish safe event writes.
4. Save memory state.
5. Save session state.
6. Save evidence.
7. Save active experiments.
8. Save pending permissions.
9. Generate/update session metadata.
10. Exit cleanly.

The session must remain recoverable.

---

# 16. SESSION RECOVERY

If the process crashes:

ai-sandbox resume

should discover the most recent incomplete session.

Example:

Found incomplete session:

Session #0042

Last event:

10:42:13
Agent A was researching distributed inference.

Resume session?

[y/N]

After approval, the system should restore the previous state.

---

# 17. SESSION MANAGEMENT

Commands:

/sessions

Example:

SESSION HISTORY

#0042
Status: Completed
Duration: 4h 21m
Discoveries: 8
Experiments: 3

#0041
Status: Interrupted
Duration: 2h 14m
Experiments: 1

#0040
Status: Completed
Duration: 53m
Discoveries: 2

---

# 18. EVIDENCE CLI

The user must be able to inspect evidence without opening files manually.

Example:

/evidence

Output:

EVIDENCE

E-00041
Agent A
Browser research
Topic: Distributed inference
Sources: 4

E-00042
Agent B
Challenge
Topic: Memory bandwidth

E-00043
Experiment
Latency comparison

The user should be able to inspect:

/evidence E-00043

---

# 19. RESEARCH CLI

/research

should display recent research.

Example:

RESEARCH

R-0012
Question:
How does Apple Silicon handle local LLM inference?

Sources:
5

Agents:
A, B

Status:
Verified

R-0013
Question:
Can context compression reduce latency?

Sources:
3

Status:
Experimental

---

# 20. EXPERIMENT CLI

/experiments

Example:

EXPERIMENTS

EXP-001
Status: Completed
Result: Improved latency 12%

EXP-002
Status: Failed
Reason: Memory regression

EXP-003
Status: Running

The user can inspect:

/experiments EXP-002

---

# 21. SELF-MODIFICATION CLI

/modifications

Example:

SELF-MODIFICATION

SM-001
Status: Applied
Improved context caching

SM-002
Status: Rejected
Increased memory usage

SM-003
Status: Testing

The user should be able to inspect:

/modifications SM-003

and view:

- proposal
- reason
- code changes
- tests
- benchmarks
- evidence
- approval state
- rollback option

---

# 22. ROLLBACK CLI

The user must be able to initiate rollback.

Example:

/rollback SM-003

The system should display:

ROLLBACK REQUEST

Modification:
SM-003

Current version:
v0.4.2

Rollback target:
v0.4.1

Reason:
Performance regression detected.

Proceed?

[y/N]

Rollback activity must be logged.

---

# 23. REPORT GENERATION

The CLI must allow:

/report

This should generate the session report.

Example:

reports/
└── session_0042_report.md

Optional formats may later include:

- Markdown
- JSON
- HTML
- PDF

Markdown and JSON are sufficient for V1.

---

# 24. WEB UI IS FUTURE WORK

Do NOT implement a full web dashboard during the initial CLI-first phase unless explicitly requested.

The architecture must remain ready for one.

Future:

                    CORE ENGINE
                         │
                 ┌───────┴───────┐
                 ↓               ↓
                CLI             API
                                 │
                                 ↓
                              Web UI

The Web UI must consume the same core APIs and Event Bus.

It must NOT duplicate:

- agent logic
- memory logic
- tool logic
- permission logic
- evidence logic
- resource management
- self-modification logic

---

# 25. API-READY DESIGN

Even though V1 is CLI-first, internal services should have clean interfaces.

Example:

AgentManager
ConversationManager
MemoryManager
ToolManager
PermissionManager
EvidenceManager
ResearchManager
ExperimentManager
ModificationManager
ResourceManager
SessionManager

The CLI calls these services.

Later the API can call the same services.

---

# 26. TUI POSSIBILITY

A full web UI is not the only future option.

The architecture may later support a terminal UI (TUI).

Possible future:

ai-sandbox tui

This can provide:

- live agent conversations
- resource graphs
- event stream
- permission prompts
- research status
- experiment status

However, TUI is optional.

The plain CLI must remain functional.

---

# 27. PERFORMANCE REQUIREMENT

The interface itself must consume minimal resources.

Avoid unnecessary background processes.

Avoid:

- heavy frontend frameworks
- browser-based dashboards running locally
- excessive polling
- continuously refreshing screens
- unnecessary animations
- duplicate event processing

Prefer:

- asynchronous event streams
- incremental rendering
- efficient terminal output
- event-driven updates

The CLI must remain lightweight on an M4 with 16 GB RAM.

---

# 28. CORE COMMAND

The primary command should be:

ai-sandbox

Possible commands:

ai-sandbox start
ai-sandbox watch
ai-sandbox interactive
ai-sandbox status
ai-sandbox sessions
ai-sandbox resume
ai-sandbox report
ai-sandbox version

The exact CLI framework may be chosen by the implementation agent.

---

# 29. LOGGING

Human-readable CLI output and machine-readable logging are separate concerns.

CLI:

Human-friendly.

Logs:

Structured JSONL.

Example:

logs/
├── events.jsonl
├── errors.jsonl
├── performance.jsonl
└── tools.jsonl

Do not use terminal output as the permanent audit record.

The Evidence Plane remains the source of truth.

---

# 30. TESTING REQUIREMENTS

Test the system without the web interface.

Tests must verify:

- CLI startup
- CLI shutdown
- agent communication
- human interruption
- permission interaction
- session recovery
- evidence logging
- research logging
- experiment tracking
- self-modification workflow
- rollback
- resource monitoring
- model failures
- tool failures

The entire core system must work in a headless terminal environment.

---

# 31. ACCEPTANCE CRITERIA

The CLI-first implementation is complete only when:

- [ ] The system can start entirely from CLI.
- [ ] Agents can communicate without a web UI.
- [ ] Human can observe agents through CLI.
- [ ] Human can interrupt agents.
- [ ] Human can send messages.
- [ ] Human can approve/deny permissions.
- [ ] Human can inspect sessions.
- [ ] Human can inspect evidence.
- [ ] Human can inspect research.
- [ ] Human can inspect experiments.
- [ ] Human can inspect self-modifications.
- [ ] Human can initiate rollback.
- [ ] Resource usage is visible.
- [ ] Voice can optionally connect to the same event system.
- [ ] Sessions can recover after crashes.
- [ ] Reports can be generated from CLI.
- [ ] Core engine does not depend on web UI.
- [ ] Future web UI can consume the same core services.
- [ ] CLI overhead remains minimal on M4 16 GB.
- [ ] No duplicated business logic exists between interface layers.

---

# FINAL IMPLEMENTATION INSTRUCTION

This document is a MANDATORY extension of the existing architecture.

Read:

1. ARCHITECTURE.md
2. AUTONOMOUS_RESEARCH_EVIDENCE_ADDON.md
3. SELF_MODIFICATION_ADDON.md
4. CLI_FIRST_INTERFACE_ADDON.md

Reconcile all four documents before implementation.

Build the system CLI-first.

Do not build the web interface first.

The core agent runtime must remain completely independent of the user interface.

The CLI should provide complete control over:

- agents
- conversation
- tools
- browser research
- memory
- evidence
- experiments
- permissions
- resource monitoring
- self-modification
- rollback
- sessions
- reports

The architecture must remain API-ready so a web dashboard can be added later without changing the underlying agent system.

The primary goal is a lightweight, reliable, observable, autonomous AI laboratory that runs efficiently on an Apple M4 with 16 GB unified memory.