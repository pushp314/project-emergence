# AGENT_DRIVEN_ORCHESTRATION_ADDON.md

# Agent-Driven Capability Selection & Delegation

## 1. PURPOSE

The system must NOT rely on a central hard-coded model router to decide which model an agent uses.

Agents themselves should be able to:

- recognize what a task requires
- decide what capabilities they need
- select an appropriate model/tool/agent
- delegate work
- request research
- challenge another agent
- change strategy when an approach fails
- escalate difficult work
- combine results
- decide when a task is complete

The orchestration layer provides the environment, capabilities, permissions, resource limits, persistence, and observability.

The agents provide the reasoning and task-level decisions.

Core principle:

> Agents decide WHAT they need. Infrastructure decides WHETHER the requested action is permitted and HOW it is executed.

---

## 2. TARGET ARCHITECTURE

```text
                          USER
                            │
                            ▼
                     CONTROL PLANE
                            │
                        EVENT BUS
                            │
               ┌────────────┴────────────┐
               │                         │
               ▼                         ▼
           AGENT A                   AGENT B
           Atlas                    Argus
               │                         │
               └────────────┬────────────┘
                            │
                     AGENT DECISION
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
        MODEL            TOOL             AGENT
       REQUEST          REQUEST          REQUEST
           │                │                │
           └────────────────┼────────────────┘
                            ▼
                     CAPABILITY REGISTRY
                            │
                            ▼
                     PERMISSION GATE
                            │
                            ▼
                    RESOURCE MANAGER
                            │
                            ▼
                      EXECUTION
                            │
                            ▼
                     RESULT + EVIDENCE
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
            MEMORY                    AGENTS
               │                         │
               └────────────┬────────────┘
                            ▼
                          SQLite
```

---

## 3. NO CENTRAL BRAIN

Do NOT implement a permanent central router that determines every model selection.

Avoid:

```text
Task
 ↓
Central Router
 ↓
Model
```

Prefer:

```text
Task
 ↓
Agent reasoning
 ↓
"I need X"
 ↓
Capability discovery
 ↓
Agent selects capability
 ↓
Permission/resource validation
 ↓
Execution
 ↓
Result
 ↓
Agent decides next action
```

The Control Plane is not the primary reasoning authority.

It is an execution and governance authority.

---

## 4. AGENT DECISION LOOP

Every capable agent should follow approximately:

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
PLAN
   ↓
IDENTIFY NEED
   ↓
DISCOVER CAPABILITY
   ↓
SELECT
   ↓
REQUEST
   ↓
EXECUTE
   ↓
OBSERVE RESULT
   ↓
EVALUATE
   ↓
DECIDE NEXT ACTION
    │
    ├── Continue
    ├── Research
    ├── Ask another agent
    ├── Ask specialist model
    ├── Use another tool
    ├── Change strategy
    ├── Escalate
    └── Finish
```

The agent must be able to revise its decision after observing results.

---

## 5. CAPABILITY REGISTRY

Create a machine-readable capability registry.

It should expose available:

- models
- agents
- tools
- research capabilities
- analysis capabilities
- coding capabilities
- browser capabilities
- filesystem capabilities
- terminal capabilities

Example conceptual registry:

```yaml
models:

  qwen3-8b:
    capabilities:
      - general_reasoning
      - research
      - conversation
      - analysis

  deepseek-r1-7b:
    capabilities:
      - deep_reasoning
      - criticism
      - analysis
      - math
      - logic

  qwen2.5-coder-7b:
    capabilities:
      - programming
      - code_analysis
      - debugging
      - code_generation

  dolphin3-cyber-8b:
    capabilities:
      - cybersecurity
      - security_analysis
      - vulnerability_research
```

The registry must be discoverable by agents.

Do not require agents to memorize model names.

---

## 6. AGENTS CHOOSE CAPABILITIES

The agent should reason in terms of capability first.

Example:

```text
"I need code analysis."
```

Then inspect:

```text
Available capabilities:
- qwen2.5-coder-7b
```

Then request:

```text
USE_CAPABILITY(
    capability="code_analysis",
    reason="Need to inspect Python implementation"
)
```

The infrastructure resolves the capability to an available implementation.

This prevents agent logic from becoming tightly coupled to model names.

---

## 7. MODEL SELECTION

Agents may consider:

- capability
- expected reasoning difficulty
- domain
- context requirements
- tool requirements
- previous results
- model reliability
- latency
- resource consumption
- current model availability
- historical performance

However, the agent does NOT need exact hardware knowledge.

The Resource Manager provides constraints such as:

```text
AVAILABLE
BUSY
MEMORY_PRESSURE
THERMAL_PRESSURE
UNAVAILABLE
```

---

## 8. CURRENT MODEL POOL

The initial environment may contain:

```text
Qwen3 8B
DeepSeek-R1-Distill-Qwen-7B
Dolphin3-Cyber-8B
Qwen2.5-Coder-7B
Dolphin-Llama3 8B
```

These are examples of available capabilities, not permanent architectural dependencies.

The architecture must remain model-agnostic.

---

## 9. AGENT-TO-AGENT DELEGATION

Agents may delegate work to other agents.

Example:

```text
Agent A:

"I need an independent critique."

        ↓

DELEGATE

        ↓

Agent B

        ↓

Critique

        ↓

Agent A

        ↓

Evaluate
```

Delegation should include:

```text
request_id
sender
receiver / capability
objective
context
reason
expected output
priority
deadline if applicable
```

---

## 10. AGENT REQUEST PROTOCOL

All model/tool/agent requests should use structured requests.

Conceptual structure:

```json
{
  "type": "capability_request",
  "request_id": "...",
  "agent_id": "...",
  "capability": "code_analysis",
  "reason": "Need independent code review",
  "objective": "...",
  "context": "...",
  "priority": "normal"
}
```

The infrastructure returns a structured result.

---

## 11. PERMISSION GATE

Agents decide what they WANT to do.

The Permission Gate decides whether they are ALLOWED to do it.

```text
Agent Decision
      ↓
Permission Gate
      ↓
┌─────┴──────┐
↓            ↓
Allowed    Approval required
↓            ↓
Execute     Human
```

Never allow agent reasoning to bypass the Permission Gate.

---

## 12. RESOURCE GATE

Before execution, the Resource Manager evaluates:

```text
RAM
CPU
GPU
active model count
queue
estimated inference cost
thermal state where available
```

Example:

```text
Agent:
"I need DeepSeek."

Resource Manager:
"Allowed, but another model is active."

Scheduler:
"Queue request."

Agent:
"Continue with research while waiting."
```

Agents should adapt to resource availability.

---

## 13. M4 16 GB OPTIMIZATION

The initial hardware is:

```text
Apple M4
16 GB unified memory
```

The system must prioritize:

- one heavy inference at a time where practical
- bounded concurrency
- lazy model loading
- model unloading
- context compression
- result summarization
- caching
- duplicate request prevention
- event-driven wakeups
- short context passing
- selective memory retrieval

Do not allow two agents to automatically launch multiple heavy models merely because both are available.

---

## 14. MODEL LOADING POLICY

Models should be loaded on demand.

Prefer:

```text
Agent needs capability
        ↓
Check loaded model
        ↓
If available → use it
        ↓
If not → evaluate resource budget
        ↓
Load/use model
        ↓
Execute
        ↓
Unload or keep cached based on policy
```

The Resource Manager should determine whether keeping a model loaded is worthwhile.

---

## 15. ESCALATION

Agents should be able to escalate when their current approach is insufficient.

Example:

```text
Agent A
 ↓
Qwen3
 ↓
Low confidence
 ↓
Request deeper reasoning
 ↓
DeepSeek
 ↓
Compare
```

Escalation should be based on observed need, not simply on task size.

---

## 16. FAILURE RECOVERY

If a selected model fails:

```text
Model failure
 ↓
Record evidence
 ↓
Agent observes failure
 ↓
Agent decides:
    retry
    change model
    change strategy
    ask another agent
    research
    stop
```

Do not automatically retry indefinitely.

Use bounded retries and record failed attempts.

---

## 17. AGENT CONFIDENCE

Agents may provide confidence estimates, but confidence must NOT be treated as proof.

Example:

```text
confidence: 0.72
reason:
"Evidence is incomplete."
```

The system should distinguish:

```text
Agent belief
Evidence
Verified fact
Human decision
```

---

## 18. EVALUATION LOOP

After every meaningful delegated task:

```text
Request
 ↓
Execution
 ↓
Result
 ↓
Evaluation
 ↓
Useful?
 ├── YES → continue
 ├── PARTIAL → refine
 └── NO → change strategy
```

The evaluation can consider:

- correctness
- evidence quality
- completeness
- latency
- resource cost
- tool success
- agreement/disagreement with other agents

---

## 19. AGENT DISAGREEMENT

Disagreement is useful.

Example:

```text
Agent A:
"Approach X is correct."

Agent B:
"I disagree because evidence Y contradicts X."

        ↓

Research / experiment

        ↓

Evidence

        ↓

Agents reassess
```

Do not force consensus merely because agents disagree.

Preserve both positions and the evidence used to resolve them.

---

## 20. NO INFINITE USELESS LOOPS

The system may support continuous autonomous operation, but agents must not endlessly repeat the same reasoning.

Detect:

- repeated identical requests
- repeated tool calls
- circular delegation
- unchanged conclusions
- repeated failed experiments

When detected:

```text
Pause
 ↓
Summarize state
 ↓
Change strategy / ask human
```

---

## 21. AGENT MEMORY OF DECISIONS

Store important decisions:

```text
decision
reason
capability selected
result
evaluation
outcome
```

This allows agents to learn from previous choices.

Example:

```text
Previous:
Qwen3 performed poorly on this task type.

Future:
Agent may choose another capability.
```

Do not hard-code this behavior prematurely.

---

## 22. ROUTING HISTORY

SQLite should record:

```text
request_id
session_id
agent_id
requested_capability
selected_implementation
reason
resource_state
latency
result_quality
success
failure
evaluation
```

This becomes the foundation for future empirical optimization.

---

## 23. FUTURE LEARNING

Do NOT implement reinforcement learning as the first version.

First collect reliable data.

Later the system may learn:

```text
Task characteristics
       ↓
Agent decision
       ↓
Capability selected
       ↓
Result
       ↓
Evaluation
       ↓
Historical performance
       ↓
Better future decisions
```

The initial objective is to build a clean dataset of decisions and outcomes.

---

## 24. SPECIALIST MODELS

Specialist models should be treated as capabilities.

Example:

```text
Cybersecurity
    ↓
Dolphin3-Cyber

Programming
    ↓
Qwen2.5-Coder

Deep reasoning
    ↓
DeepSeek

General research
    ↓
Qwen3
```

Agents decide when a specialist is necessary.

---

## 25. MULTI-MODEL COLLABORATION

Agents may deliberately use multiple models.

Example:

```text
Agent A
 ↓
Research with Qwen3
 ↓
Code with Qwen-Coder
 ↓
Security review with Dolphin-Cyber
 ↓
Reasoning/critique with DeepSeek
 ↓
Agent A synthesizes
```

This is preferred over forcing one model to perform every task.

---

## 26. AGENT ROLE VS MODEL

Do not confuse:

```text
Agent
```

with:

```text
Model
```

An agent is a persistent reasoning process with:

- identity
- role
- memory
- goals
- state
- permissions
- tools
- communication
- decision loop

A model is an inference engine.

One agent may use different models during its lifetime.

Example:

```text
Agent A
 ├── Qwen3
 ├── Qwen-Coder
 └── DeepSeek
```

This is allowed.

---

## 27. AGENT A / AGENT B INITIAL CONFIGURATION

Initial configuration:

```text
Agent A
Identity: atlas
Default Model: Qwen3 8B
```

```text
Agent B
Identity: argus
Default Model: DeepSeek-R1-Distill-Qwen-7B
```

These are DEFAULT configurations, not permanent restrictions.

Agents may request other capabilities when justified.

---

## 28. OBSERVER ROLE

An optional Observer may monitor:

```text
agent activity
events
resource usage
loops
errors
permissions
research
experiments
emergence
```

The Observer should generally NOT participate in reasoning unless explicitly assigned.

It exists to improve observability.

---

## 29. HUMAN OVERRIDE

The human can always:

- interrupt
- redirect
- ask a question
- stop an agent
- stop a session
- approve/deny permission
- change resource limits
- change available capabilities
- inspect decisions

Human commands take precedence over agent autonomy.

---

## 30. EVIDENCE

Every important capability decision should be observable.

Record:

```text
Agent
Decision
Reason
Capability requested
Capability selected
Execution
Result
Evaluation
Next decision
```

This allows the user to later understand:

> "Why did the agent choose this model?"

---

## 31. CLI OBSERVABILITY

The CLI should eventually expose:

```text
agents
capabilities
requests
decisions
routing
resources
models
sessions
timeline
emergence
```

Example:

```text
> routing

Agent A
  Need: code analysis
  Selected: qwen2.5-coder:7b
  Reason: code-heavy task
  Status: completed

Agent B
  Need: independent reasoning
  Selected: deepseek-r1
  Reason: disagreement with Agent A
  Status: running
```

---

## 32. TESTING REQUIREMENTS

Test:

- agent selects capability
- unknown capability
- unavailable model
- model failure
- resource pressure
- permission denial
- agent delegation
- agent disagreement
- escalation
- loop detection
- human interruption
- persistence
- recovery

Do not consider agent-driven orchestration complete until these are tested.

---

## 33. ACCEPTANCE CRITERIA

This addon is implemented when:

- [ ] Agents can discover available capabilities.
- [ ] Agents can choose capabilities themselves.
- [ ] Agents can request models/tools.
- [ ] Infrastructure validates requests.
- [ ] Permission checks occur before restricted execution.
- [ ] Resource checks occur before heavy execution.
- [ ] Agents can delegate to other agents.
- [ ] Agents can escalate.
- [ ] Agents can change strategy after failure.
- [ ] Agent decisions are persisted.
- [ ] Results are evaluated.
- [ ] Repeated loops are detected.
- [ ] Human can interrupt.
- [ ] Model names are not hard-coded into agent reasoning.
- [ ] Multiple models can be used by one agent.
- [ ] The system remains usable on M4 16 GB.
- [ ] Routing/selection history can be analyzed later.

---

## 34. IMPLEMENTATION ORDER

Build incrementally:

```text
1. Capability registry
2. Structured capability request
3. Model/tool resolver
4. Permission gate
5. Resource gate
6. Agent self-selection
7. Result evaluation
8. Agent delegation
9. Escalation
10. Loop detection
11. SQLite routing history
12. CLI observability
13. Historical performance analysis
14. Future learned routing
```

Do NOT start with machine learning for routing.

Build deterministic capability discovery first.

---

## 35. IMPORTANT DESIGN RULE

Do not make the system:

```text
Agent → unrestricted execution
```

Make it:

```text
Agent
 ↓
Decision
 ↓
Capability Request
 ↓
Permission Gate
 ↓
Resource Gate
 ↓
Execution
 ↓
Evidence
 ↓
Result
 ↓
Agent
```

This preserves autonomy without surrendering system control.

---

## 36. FINAL PRINCIPLE

The goal is not:

> "Build the smartest router."

The goal is:

> "Build an environment in which agents can intelligently decide what they need, discover the available capabilities, use them efficiently, evaluate the results, change strategy, and continue learning from their own decisions."

The orchestration layer should therefore become:

```text
                      ENVIRONMENT
                           │
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
    Capabilities      Permissions       Resources
         │                 │                 │
         └─────────────────┼─────────────────┘
                           ↓
                        AGENTS
                           │
                     SELF-DIRECTED
                       DECISIONS
                           │
           ┌───────────────┼────────────────┐
           ↓               ↓                ↓
         Models          Tools           Agents
           └───────────────┼────────────────┘
                           ↓
                        RESULTS
                           ↓
                     EVALUATION
                           ↓
                        MEMORY
                           ↓
                        SQLite
                           ↓
                  FUTURE DECISIONS
```

This addon must be integrated with `RULES.md`, `ARCHITECTURE.md`, the SQLite addon, self-modification addon, evidence addon, and CLI addon.

Do not replace those documents. This file defines the additional behavior for agent-driven orchestration.