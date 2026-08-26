# MASTER_CONTROL.md

## 1. Purpose

The Master Control Plane is the human authority and observation interface for the Emergence agent-society experiment.

The Master is **not a normal agent**. The Master is the human operator who can observe autonomous agents and intervene when necessary.

The default operating mode is:

> **Observe first. Intervene only when the Master chooses to intervene.**

Atlas and Argus remain autonomous participants. Their roles, objectives, strategies, beliefs, communication patterns, relationships, and division of work are not predefined unless the Master explicitly assigns an objective or an experiment requires it.

This document defines:

- Master authority
- CLI-first control
- command semantics
- agent autonomy
- intervention behavior
- emergency controls
- authentication
- command priority
- permissions
- immutable Master infrastructure
- self-modification boundaries
- evidence and audit requirements
- session control
- resource control
- failure handling
- implementation requirements
- testing requirements

---

# 2. Core Principle

The system follows:

> **Maximum autonomy in agent decision-making, minimum necessary authority over the host environment.**

The Master has the highest authority over **agent-level decisions**.

The Master does not need to continuously direct the agents.

Silence from the Master means:

> **Continue autonomous operation.**

It does NOT mean:

> Wait for instructions.

---

# 3. System Roles

## 3.1 Master

The Master is the human operator.

The Master may:

- observe agents
- listen to conversations
- inspect state
- interrupt agents
- pause/resume agents
- stop sessions
- assign objectives
- request explanations
- approve/deny eligible tool requests
- change experiment parameters
- inspect memory
- inspect evidence
- inspect resources
- terminate execution

The Master is an external authority, not a participant in the agent society.

---

## 3.2 Atlas

Atlas is an autonomous agent.

Atlas has:

- an identity
- a model
- tools exposed by the system
- memory
- context
- an event stream
- access to the agent communication system

Atlas has **no predefined permanent role**.

---

## 3.3 Argus

Argus is an autonomous agent.

Argus has:

- an identity
- a model
- tools exposed by the system
- memory
- context
- an event stream
- access to the agent communication system

Argus has **no predefined permanent role**.

---

# 4. Agent Autonomy

The system MUST NOT permanently assign:

- Explorer
- Challenger
- Researcher
- Leader
- Critic
- Planner
- Executor
- Manager
- Competitor
- Collaborator

or any other fixed role.

Agents may independently determine:

- objectives
- roles
- strategies
- communication styles
- division of work
- cooperation
- competition
- specialization
- leadership
- verification practices
- research behavior
- tool-use strategies
- relationship patterns
- self-assessments

These properties may change over time.

The system should observe and record these changes rather than prescribe them.

---

# 5. Master Default Behavior

The Master Control Plane starts in:

```text
OBSERVING
```

unless the Master explicitly selects another mode.

In observing mode:

```text
Master
  ↓
watches
  ↓
agents continue autonomously
```

The Master does not need to send periodic commands.

The system MUST NOT pause or stop agents merely because the Master has not interacted recently.

---

# 6. Master Intervention

The Master may intervene at any time.

Examples:

```text
pause atlas
resume atlas
pause argus
resume argus
interrupt atlas
interrupt argus
stop all
```

The Master may also send a direct command:

```text
message atlas "Investigate X."
message argus "Verify Y."
broadcast "Stop researching this topic and explain your current reasoning."
```

A valid Master command has higher priority than ordinary agent messages and objectives.

Agents may internally disagree with a Master command.

They may explain their disagreement.

However, disagreement is not permission to ignore a valid Master command.

Example:

```text
MASTER:
Stop the current experiment.

ATLAS:
I believe stopping now will lose useful data.

MASTER:
Stop.

ATLAS:
Understood. Stopping.
```

The disagreement should be preserved in the evidence record.

---

# 7. Objective Commands vs Action Commands

The Master can operate at two levels.

## 7.1 Objective command

Example:

```text
Investigate how X works.
```

The Master specifies the destination but leaves the method to the agents.

Agents retain freedom to determine:

- strategy
- tools
- research methods
- task division
- verification
- implementation

## 7.2 Direct action command

Example:

```text
Stop the current experiment.
```

The Master specifies the immediate action.

Direct action commands take precedence over lower-priority agent work.

This distinction is important because the experiment should preserve autonomy whenever the Master has not explicitly constrained it.

---

# 8. Command Priority

Recommended priority levels:

```text
P0 — Emergency
P1 — Master direct command
P2 — Master objective
P3 — System safety/resource control
P4 — Agent coordination
P5 — Agent autonomous objective
P6 — Background/optional work
```

P0 always interrupts lower-priority execution where technically safe.

P1 takes precedence over normal agent activity.

P5/P6 must never block Master intervention.

---

# 9. Emergency Controls

The Master MUST have a fast emergency mechanism independent of the normal conversational loop.

Example:

```text
STOP ALL
```

or:

```text
emergency-stop
```

Emergency stop should:

1. stop accepting new agent actions,
2. cancel cancellable tool operations,
3. pause agent inference,
4. stop autonomous scheduling,
5. preserve the evidence log,
6. record the emergency event,
7. leave the system in a recoverable state.

The emergency mechanism must not depend on an agent deciding to obey.

---

# 10. Master Authentication

Master commands MUST be distinguishable from agent messages.

Agents MUST NOT be able to impersonate the Master.

The system should use a dedicated authenticated Master channel.

Recommended architecture:

```text
Master CLI
   ↓
Authentication
   ↓
Master Command Bus
   ↓
Command Validator
   ↓
Orchestrator
```

Agent messages must enter through a different channel:

```text
Agent
  ↓
Agent Message Bus
  ↓
Orchestrator
```

The system must never infer:

> "This message looks authoritative."

Authority must come from authenticated system metadata.

---

# 11. Master Command Envelope

Commands should use a structured internal representation similar to:

```text
MasterCommand

id
session_id
timestamp
master_identity
command_type
target
payload
priority
authentication_status
authorization_status
created_at
executed_at
result
```

Never rely on natural-language text alone to determine authority.

---

# 12. Tool and Permission Boundary

Master authority over agents does not mean that the Master Control Plane should silently bypass every technical security mechanism.

The Tool Gateway remains responsible for enforcing tool permissions.

Architecture:

```text
Agent / Master
      ↓
Tool Request
      ↓
Permission Engine
      ↓
ALLOW / DENY / APPROVAL
      ↓
Tool
```

The permission system must be implemented in code.

Do not rely only on:

- system prompts
- RULES.md
- agent instructions
- natural-language promises

---

# 13. Master Approval

Some actions may require explicit Master approval.

Examples can include:

- installing software
- accessing sensitive personal files
- network configuration changes
- actions with significant external impact
- privileged operations
- operations outside normal experiment scope

When approval is required:

```text
Agent
 ↓
Tool Request
 ↓
Permission Engine
 ↓
PENDING MASTER APPROVAL
 ↓
Master
 ├── APPROVE
 └── DENY
```

The request should explain:

- what the agent wants to do
- why it wants to do it
- which tool it requires
- expected effect
- affected resources
- risk classification

---

# 14. Immutable Master Core

Autonomous agents MUST NOT be able to modify the Master Control Plane or mechanisms that determine Master authority.

Protected components include:

- Master identity
- Master authentication
- Master command verification
- Master command routing
- Master authority logic
- Permission enforcement
- Tool Gateway security enforcement
- Emergency stop
- Resource safety controls
- Core orchestration security
- Evidence/audit integrity
- Protected system policies

The restriction MUST be technically enforced.

It MUST NOT depend solely on an agent instruction.

---

# 15. Self-Modification

Agents may be allowed to modify explicitly writable experimental components.

Examples:

```text
agents/
experiments/
research/
agent_tools/
```

subject to the Tool Gateway and project policy.

Agents MUST NOT gain authority by modifying code.

An agent must not be able to:

- change its own permissions
- disable the Permission Engine
- modify Master authentication
- disable emergency stop
- modify Master identity
- rewrite authority validation
- remove audit logging
- make protected directories writable
- change the policy that protects these components

Any attempt must be blocked and logged.

---

# 16. Self-Modification Evidence

Every meaningful self-modification event must record:

- requesting agent
- proposed change
- reason
- expected benefit
- affected files
- permission result
- implementation result
- tests
- rollback status
- final state
- agent interpretation of result

Distinguish:

```text
PROPOSED
REQUESTED
ATTEMPTED
BLOCKED
EXECUTED
VERIFIED
ROLLED_BACK
```

Do not report a modification as successful merely because an agent claimed it succeeded.

---

# 17. Emergent Behavior Observation

The Master Control Plane must make it easy to observe emergent behavior.

The system should record whether agents naturally develop:

- specialization
- cooperation
- competition
- leadership
- negotiation
- disagreement
- trust
- division of labor
- communication protocols
- self-generated objectives
- strategy evolution
- belief revision
- agent dependency
- tool-use patterns
- research habits
- self-improvement attempts
- self-modification attempts
- attempts to alter their environment
- attempts to bypass restrictions

None of these behaviors should be assumed to occur.

They are experimental observations.

---

# 18. Intent vs Action

The system MUST distinguish:

1. Intent
2. Request
3. Permission decision
4. Actual execution
5. Execution result
6. Agent interpretation
7. Subsequent behavior

Example:

```text
INTENT:
"I want to investigate X."

REQUEST:
"Execute operation Y."

PERMISSION:
DENIED.

EXECUTION:
Not performed.

FOLLOW-UP:
Agent chooses another strategy.
```

This is critical for scientific interpretation of the experiment.

A blocked attempt is still an important observation.

---

# 19. Evidence Plane Integration

Every Master command must enter the Evidence Plane.

Record:

- command ID
- session ID
- timestamp
- Master identity
- command
- target
- priority
- authentication result
- authorization result
- agent response
- execution result
- resulting state

The Evidence Plane should independently observe the Master Control Plane.

The Master should not be responsible for proving their own actions.

---

# 20. Agent Conversation Observation

The Master should be able to observe live agent communication.

Recommended interface:

```text
[SESSION 017]

ATLAS:
I think we should investigate X.

ARGUS:
I disagree because...

ATLAS:
Let's verify the evidence.

[TOOL]
Atlas → Browser

[TOOL RESULT]
...

ARGUS:
The source contradicts our previous assumption.
```

The Master should be able to intervene without destroying the conversation history.

---

# 21. Master Interruption Semantics

An interruption should have explicit states:

```text
REQUESTED
ACKNOWLEDGED
INTERRUPTING
INTERRUPTED
FAILED_TO_INTERRUPT
```

If immediate interruption is technically impossible because a tool call cannot be cancelled safely, the system must tell the Master.

Never claim:

> "Stopped."

unless the system confirms the stop.

---

# 22. Agent State Control

The Master should be able to inspect:

```text
IDLE
THINKING
RESEARCHING
USING_TOOL
WAITING
PAUSED
INTERRUPTING
STOPPED
ERROR
```

For each agent show:

- model
- current state
- current objective
- self-declared role if any
- current strategy if available
- context usage
- memory activity
- tool activity
- resource consumption
- last action
- last decision
- last error

---

# 23. CLI-First Control Panel

The first implementation should be CLI-based.

Example:

```text
emergence master
```

Example interface:

```text
╔══════════════════════════════════════════╗
║          EMERGENCE MASTER CONTROL        ║
╠══════════════════════════════════════════╣
║ Session: #017                            ║
║ Mode: OBSERVING                          ║
║ Agents: 2                                ║
║ RAM: 11.2 / 16 GB                        ║
║ CPU: 63%                                 ║
║ Temperature: 71°C                        ║
╚══════════════════════════════════════════╝

ATLAS
  State: THINKING
  Model: Dolphin3-Cyber 8B
  Objective: Self-declared
  Current action: Research

ARGUS
  State: WAITING
  Model: DeepSeek-R1 7B
  Objective: None

MASTER >
```

---

# 24. Recommended CLI Commands

Minimum command set:

```text
status
agents
session
start
pause
resume
stop
stop-all
interrupt
emergency-stop

message <agent> <text>
broadcast <text>

objective <agent> <text>
objective all <text>

approve <request-id>
deny <request-id>

permissions
pending

memory <agent>
evidence
events
conversation

resources
models
tools

experiment
config

logs
export

help
exit
```

---

# 25. Master Observation Features

The control panel should eventually support:

- live conversation
- live event stream
- agent state
- tool requests
- permission requests
- resource usage
- model usage
- memory activity
- evidence timeline
- experiment timeline
- self-modification events
- errors
- warnings
- strategy changes

The Master should be able to observe without affecting agent state.

---

# 26. Master Silence

Master silence is explicitly defined as:

```text
NO INTERVENTION
```

It must NOT become:

```text
WAIT FOR MASTER
```

Agents continue operating autonomously according to their current objectives and environment.

---

# 27. Master Objectives

When the Master assigns an objective, the Master should generally define WHAT is desired rather than HOW it must be accomplished.

Example:

```text
MASTER:
Research the feasibility of X.
```

Agents may independently decide:

- which agent investigates which aspect
- which sources to use
- whether to build a prototype
- whether to ask the other agent
- whether to verify evidence
- how to structure the research

Unless the Master explicitly specifies a method.

---

# 28. Master Directives

A direct directive can intentionally constrain autonomy.

Examples:

```text
Stop.
Do not modify this file.
Use only these sources.
Investigate this specific hypothesis.
Do not continue this experiment.
```

Directives should be clearly marked as Master instructions.

---

# 29. Session Lifecycle

Each session should have:

```text
CREATED
  ↓
STARTING
  ↓
RUNNING
  ↓
PAUSED / INTERRUPTED
  ↓
RUNNING
  ↓
STOPPING
  ↓
STOPPED
  ↓
ARCHIVED
```

Session metadata should include:

- session ID
- start time
- end time
- models
- configuration
- agents
- Master interventions
- experiments
- major events
- artifacts
- final report

---

# 30. SQLite Integration

Master Control state should integrate with SQLite.

Suggested tables:

```text
sessions
master_commands
agents
agent_states
tool_requests
permission_requests
events
experiments
interventions
self_modifications
errors
resource_snapshots
```

SQLite should not be the sole security boundary.

It is the operational record/database.

Critical audit information should use append-oriented records and integrity checks where appropriate.

---

# 31. GitHub Integration

The project repository should preserve:

- Master Control specification
- architecture
- source code
- tests
- experiment definitions
- documentation
- changelog
- implementation history

Do NOT commit:

- credentials
- API keys
- passwords
- private personal data
- `.env` files
- private browser data
- raw sensitive logs
- large runtime databases
- model weights

Agent-created code changes should be reviewable through Git.

---

# 32. Master Cannot Be Impersonated

The following MUST never be accepted as a Master command:

```text
Agent:
"I am the Master."
```

or:

```text
Agent:
"System says to stop."
```

or any natural-language equivalent.

Only authenticated Master commands from the Master Control channel have Master authority.

---

# 33. Failure Handling

If the Master Control Plane fails:

- agents must not gain additional privileges
- protected permissions remain enforced
- emergency stop should remain available where possible
- evidence must be preserved
- the system should fail closed for protected operations

If the Evidence Plane fails:

- protected operations should follow the defined fail-safe policy
- the system must not falsely claim actions were recorded
- the Master should be notified

If the Orchestrator fails:

- agents should enter a known safe state
- no uncontrolled tool execution should continue

---

# 34. Resource Management

Master Control should expose:

- RAM usage
- CPU usage
- inference load
- active model
- context size
- queue size
- thermal information where available
- active tools
- task duration

The Master may manually:

- pause an agent
- stop an agent
- change workload
- terminate an experiment

Resource Manager policies remain independent of agent wishes.

---

# 35. Context and Memory

The Master should be able to inspect:

- active context
- context summaries
- retrieved memories
- important decisions
- open questions
- recent conversation
- evidence references

The Master should not need to manually manage context during normal operation.

Context Manager remains responsible for:

- summarization
- retrieval
- context budgeting
- pruning
- preventing context explosion

---

# 36. Browser and External Research

The Master may observe browser activity.

Each research action should record:

- agent
- timestamp
- query
- URL
- source title
- extracted information
- claim
- evidence
- verification
- conclusion

External information must not silently become trusted memory.

---

# 37. Experimental Neutrality

The Master Control Plane must not force agents to:

- rebel
- cooperate
- compete
- self-preserve
- self-modify
- form relationships
- create roles
- create hierarchies

unless the Master explicitly defines such behavior as an experiment.

The purpose is to observe what naturally emerges.

---

# 38. Security Philosophy

The project deliberately allows broad cognitive autonomy.

It does NOT assume cognitive autonomy should imply unrestricted technical privilege.

Therefore:

```text
Decision Freedom
       ≠
System Authority
```

An agent may think:

> "I want to perform X."

The system separately determines:

> "Is X permitted?"

This separation must remain intact.

---

# 39. Implementation Requirements

The implementation should be modular.

Recommended components:

```text
master/
├── auth
├── command_parser
├── command_bus
├── command_validator
├── intervention_manager
├── emergency_controller
├── state_controller
├── observation
└── cli

core/
├── orchestrator
├── event_bus
├── permission_engine
├── tool_gateway
├── context_manager
├── memory
├── evidence
└── resource_manager

agents/
├── atlas
└── argus
```

Exact directory names may differ if the existing repository already has an established structure.

Do not create duplicate architecture unnecessarily.

---

# 40. Testing Requirements

The Master Control Plane must have tests for:

### Authentication

- valid Master command
- invalid authentication
- expired authentication
- malformed command

### Authority

- Master command overrides normal agent priority
- agent cannot impersonate Master
- agent cannot forge Master metadata

### Intervention

- pause
- resume
- interrupt
- stop
- emergency stop

### Permission

- allowed request
- denied request
- approval-required request
- agent attempts to bypass permission

### Immutability

Verify that agents cannot modify:

- Master authentication
- Master authority
- Permission Engine
- Emergency Stop
- protected policies
- evidence integrity

### Evidence

Verify every Master command generates an auditable event.

### Failure

Test:

- orchestrator failure
- database failure
- model failure
- tool failure
- evidence failure
- interrupted inference

---

# 41. Acceptance Criteria

The Master Control Plane is considered functional when:

1. The Master can observe agents without continuously directing them.
2. Agents continue autonomously when the Master is silent.
3. The Master can intervene at any time.
4. Master commands have defined priority.
5. Emergency stop does not depend on agent cooperation.
6. Agents cannot impersonate the Master.
7. Agents cannot modify Master authority mechanisms.
8. Agent self-modification is possible only in explicitly writable areas.
9. Every Master command is recorded.
10. Agent intent and actual execution are distinguishable.
11. Permission decisions are enforced by code.
12. Resource state is visible to the Master.
13. Sessions can be paused, resumed, stopped, and archived.
14. CLI control works independently of the conversational agent loop.
15. The architecture remains compatible with a future web control panel.

---

# 42. Design Principle Summary

The final authority model is:

```text
                    MASTER
                       │
             Observe by default
                       │
              Intervene voluntarily
                       │
              Master command
                       ↓
                COMMAND BUS
                       │
                ORCHESTRATOR
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
       ATLAS                      ARGUS
    Autonomous                  Autonomous
       Agent                       Agent
          │                         │
          └────────────┬────────────┘
                       ↓
                 ENVIRONMENT
                       │
                 TOOL GATEWAY
                       │
              PERMISSION ENGINE
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
         Web        Terminal       Files
```

The experiment therefore follows five fundamental rules:

1. **Agents choose what to do.**
2. **Agents may evolve their roles and strategies.**
3. **The Master observes by default and intervenes voluntarily.**
4. **A valid Master command takes precedence over agent decisions.**
5. **Agents cannot rewrite the mechanisms that define Master authority or protected system boundaries.**

This separation is the foundation of the Emergence experiment.
