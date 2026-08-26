# RESOURCE_MANAGER.md

## Resource Management Specification
### M4 16 GB Optimization, RAM Pressure, Inference Scheduling, Heat Control, and Compute Budgets

---

# 1. PURPOSE

The Resource Manager controls how the agent society uses limited local hardware resources.

Primary target environment:

```text
Apple Mac
M4
16 GB unified memory
Local Ollama inference
7B/8B quantized models
```

The Resource Manager must optimize for:

- inference speed
- RAM usage
- GPU/CPU utilization
- thermal load
- model loading/unloading
- concurrent inference
- context size
- output token budgets
- agent task budgets
- tool usage
- system responsiveness
- energy efficiency

Core principle:

> The system must spend compute on useful intelligence, not unnecessary activity.

---

# 2. DESIGN PHILOSOPHY

Do not attempt to make the M4 16 GB behave like an AI server.

Instead:

```text
Limited hardware
      ↓
Intelligent scheduling
      ↓
Selective model usage
      ↓
Bounded context
      ↓
Controlled inference
      ↓
Efficient agent society
```

The Resource Manager works together with:

```text
Context Manager
Model Manager
Agent Scheduler
Tool Gateway
SQLite
Ollama
```

---

# 3. RESOURCE LAYERS

Monitor at least:

```text
System RAM
Available unified memory
Model memory
Context memory
CPU utilization
GPU utilization where available
Inference queue
Active model
Model loading state
Tokens/second
Inference latency
Task duration
Concurrent requests
Disk usage
```

Thermal data should be used when reliably available through macOS/system telemetry.

Do not depend on undocumented hardware sensors.

---

# 4. RESOURCE MANAGER ARCHITECTURE

```text
                     RESOURCE MANAGER
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
     Memory              Compute             Thermal
     Manager             Manager              Manager
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
                    Scheduling Policy
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
      Model Manager    Agent Scheduler    Tool Scheduler
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
                          Ollama
                            ↓
                         M4 System
```

---

# 5. RESOURCE STATES

Use resource states rather than making decisions from individual measurements.

Recommended states:

```text
GREEN
YELLOW
ORANGE
RED
```

## GREEN

Normal operation.

```text
RAM pressure: low
Inference: normal
System: responsive
```

Allow normal scheduling.

---

## YELLOW

Moderate pressure.

Actions:

- reduce concurrent work
- prefer smaller/faster models
- reduce context budgets
- reduce output budgets
- delay nonessential tasks

---

## ORANGE

High pressure.

Actions:

- allow only one expensive inference
- prevent new model loading unless necessary
- aggressively reduce context
- postpone background agents
- reduce tool activity
- prioritize active user task

---

## RED

Critical pressure.

Actions:

- stop new inference
- finish or cancel nonessential work
- unload unnecessary models
- pause autonomous agent loops
- preserve state/checkpoint
- return control to the user

The system must never sacrifice system stability to keep agents running.

---

# 6. MEMORY MANAGEMENT

The M4 uses unified memory.

Therefore:

```text
Model memory
+
KV/context memory
+
Application memory
+
Browser memory
+
macOS memory
```

all compete for the same physical memory pool.

The Resource Manager must treat them as one resource.

Do not assume that unused CPU RAM can always be freely separated from GPU memory.

---

# 7. MEMORY BUDGET

The system should maintain a configurable application safety margin.

Do not intentionally consume 100% of the machine's 16 GB.

Example conceptual policy:

```text
Total physical memory      16 GB

System safety reserve      configurable
Application budget         configurable
Model/context budget       dynamic
```

The exact thresholds must be benchmarked on the user's machine.

Do not hard-code unsafe universal numbers.

---

# 8. MEMORY PRESSURE POLICY

Monitor:

```text
available memory
memory pressure
swap usage
model memory estimate
application memory
```

If pressure rises:

```text
Reduce concurrency
      ↓
Reduce context
      ↓
Reduce output token budget
      ↓
Unload unnecessary models
      ↓
Pause background agents
```

Do not immediately terminate the entire system.

---

# 9. MODEL LOADING STRATEGY

The system may have several local models installed:

```text
Dolphin3-Cyber 8B
Qwen3 8B
DeepSeek-R1-Distill-Qwen-7B
Qwen2.5-Coder 7B
Other models
```

Installed models are not the same as active models.

Prefer:

```text
Installed models
       ↓
Model Manager
       ↓
Select required model
       ↓
Load/use
       ↓
Finish task
       ↓
Keep temporarily or unload
```

Do not keep every model actively consuming memory simply because it is installed.

---

# 10. MODEL SELECTION

The Model Manager should consider:

```text
task type
required capability
model quality
model size
current memory pressure
current loaded model
expected latency
expected output length
```

Example:

```text
Simple classification
        ↓
Fast/small model

Coding
        ↓
Qwen2.5-Coder

Cybersecurity
        ↓
Dolphin3-Cyber

Deep reasoning
        ↓
DeepSeek-R1
```

Model selection should be capability-aware and resource-aware.

---

# 11. MODEL SWITCHING COST

Changing models has a cost.

The scheduler should consider:

```text
Current model
        ↓
Can current model solve the task?
        │
   YES  → reuse
   NO   → evaluate switch
```

Avoid unnecessary model switching.

If Agent A requires several sequential calls to the same model, prefer keeping that model available when memory allows.

---

# 12. CONCURRENCY POLICY

For the initial M4 16 GB implementation:

> Default to one heavy local LLM inference at a time.

Example:

```text
Agent A → inference
      ↓
finish
      ↓
Agent B → inference
      ↓
finish
      ↓
Agent C → inference
```

Do not automatically run:

```text
Agent A ─┐
Agent B ─┼→ simultaneous heavy inference
Agent C ─┤
Agent D ─┘
```

unless benchmarking demonstrates that the machine can handle it safely.

---

# 13. AGENT SCHEDULER

Agents must enter a queue.

Example:

```text
Task Queue

1. User request
2. Agent A research
3. Agent B verification
4. Observer analysis
5. Background memory maintenance
```

Priority:

```text
USER
  ↓
CRITICAL AGENT TASK
  ↓
ACTIVE RESEARCH
  ↓
VERIFICATION
  ↓
BACKGROUND MAINTENANCE
```

Background tasks must never starve the user's request.

---

# 14. AGENT THINKING BUDGET

Every autonomous task should have a budget.

Example:

```text
max_inference_calls
max_output_tokens
max_tool_calls
max_browser_searches
max_task_duration
```

Example:

```text
Task Budget

Inference calls: 10
Output tokens: 2,000
Browser searches: 5
Tool calls: 10
Duration: 10 minutes
```

These are starting defaults and should be configurable.

---

# 15. AUTONOMOUS LOOP CONTROL

Agents must not run an uncontrolled loop:

```text
think
→ act
→ think
→ act
→ think
→ act
→ ...
```

Instead:

```text
Task
 ↓
Decision
 ↓
Action
 ↓
Observation
 ↓
Evaluate
 ↓
Continue?
```

At every cycle evaluate:

```text
Is progress being made?
Is the goal still valid?
Is another inference justified?
Is the task stuck?
Is the budget nearly exhausted?
```

If not, pause or terminate.

---

# 16. NO-OP PREVENTION

Before every inference, ask the lightweight scheduler:

```text
Does this require an LLM?
```

Examples that should normally NOT require an LLM:

```text
Check whether a file exists
Check whether a task already ran
Check whether a URL is already stored
Check model availability
Check SQLite state
Check resource availability
Check whether a duplicate event exists
```

Use normal code/database logic for deterministic operations.

---

# 17. OUTPUT TOKEN MANAGEMENT

Different tasks need different output budgets.

Initial recommendations:

```text
Classification       100–300
Simple answer         200–500
Research summary      500–1,000
Coding                1,000–2,000
Deep reasoning        1,000–3,000
```

Do not give every request a large maximum output.

The agent should stop when the objective is satisfied.

---

# 18. CONTEXT MANAGER INTEGRATION

The Resource Manager controls the context budget.

Example:

```text
Normal:
8K–12K target context

Memory pressure:
reduce context

High pressure:
aggressive retrieval/compression
```

The Context Manager must never exceed the budget supplied by the Resource Manager.

---

# 19. DYNAMIC CONTEXT BUDGET

Conceptually:

```python
context_budget = base_budget

if resource_state == "YELLOW":
    context_budget *= 0.85

if resource_state == "ORANGE":
    context_budget *= 0.70

if resource_state == "RED":
    context_budget = 0
```

Actual values must be configurable and benchmarked.

---

# 20. THERMAL MANAGEMENT

Heat is a consequence of sustained compute.

The goal is not to eliminate heat during inference.

The goal is to prevent unnecessary sustained load.

Use:

```text
inference
 ↓
observe
 ↓
tool operation
 ↓
memory retrieval
 ↓
next inference
```

rather than continuous unnecessary generation.

If reliable thermal telemetry indicates sustained high thermal load:

```text
Reduce concurrency
Reduce background activity
Increase scheduling delay
Reduce output budgets
Pause autonomous loops
```

Do not depend on guessed temperature values.

---

# 21. COOLDOWN POLICY

A cooldown should be triggered by resource conditions, not merely by an arbitrary timer.

Example:

```text
High sustained load
      ↓
Agent task completes
      ↓
No urgent task
      ↓
Pause background inference
      ↓
Allow system to return toward normal state
```

The system should remain responsive to user interruption during cooldown.

---

# 22. USER INTERRUPTION

The user must always be able to interrupt autonomous work.

Priority:

```text
USER INTERRUPT
      ↓
STOP/PAUSE AUTONOMOUS WORK
      ↓
CHECKPOINT STATE
      ↓
RETURN CONTROL
```

Do not lose:

- current task
- context
- decisions
- tool state
- evidence references
- partial results

---

# 23. BROWSER RESOURCE CONTROL

Browser operations can consume significant memory.

The Resource Manager should consider:

```text
browser process count
open pages
page size
number of concurrent searches
```

Avoid opening many browser sessions/tabs unnecessarily.

Prefer:

```text
Search
 ↓
Extract relevant information
 ↓
Close/release unnecessary page resources
```

---

# 24. TOOL SCHEDULING

Tools should also be scheduled.

Example:

```text
Browser
Terminal
Filesystem
Git
```

If an agent is waiting for inference, a lightweight deterministic operation may proceed.

But avoid launching multiple memory-heavy operations simultaneously.

---

# 25. RESOURCE-AWARE A2A

Agent-to-agent communication must be scheduled.

Bad:

```text
Agent A
 ↓
Agent B
 ↓
Agent A
 ↓
Agent B
 ↓
Agent C
 ↓
Agent A
...
```

with unlimited calls.

Better:

```text
A requests B
 ↓
Resource Manager checks budget
 ↓
B responds
 ↓
A evaluates result
 ↓
Continue only if justified
```

---

# 26. RESOURCE-AWARE MODEL ROUTING

The agent may decide:

> "I need cybersecurity expertise."

The Resource Manager decides:

```text
Dolphin3-Cyber 8B available?
        │
       YES
        ↓
Memory safe?
        │
       YES
        ↓
Use model
```

If not:

```text
Use currently loaded capable model
OR
queue request
OR
use fallback model
```

Agent capability decisions and hardware resource decisions remain separate.

---

# 27. PRIORITY LEVELS

Every task should have a priority.

Recommended:

```text
P0 — User interaction
P1 — Critical active task
P2 — Agent collaboration
P3 — Research
P4 — Background maintenance
```

P0/P1 tasks can preempt lower-priority tasks.

---

# 28. RESOURCE RESERVATION

Before starting expensive inference:

```text
estimate required resources
        ↓
reserve budget
        ↓
run
        ↓
release budget
```

If reservation fails:

```text
queue
fallback
reduce context
or ask user
```

Never start expensive tasks based solely on hope that memory will be available.

---

# 29. TASK ADMISSION CONTROL

Before starting a task:

```text
Can we afford this task?
```

Check:

```text
memory
model
context
expected output
tool requirements
concurrency
task budget
```

If not affordable:

```text
WAIT
REDUCE
DELEGATE
FALLBACK
or ASK USER
```

---

# 30. CACHE STRATEGY

Cache expensive deterministic information:

```text
model metadata
task classification
retrieved evidence
summaries
tool result summaries
resource measurements
```

Invalidate caches when underlying information changes.

Do not cache model responses blindly when the task is dynamic.

---

# 31. SQLITE RESOURCE TELEMETRY

Record:

```text
timestamp
session_id
agent_id
task_id
resource_state
memory_pressure
model
context_tokens
output_tokens
inference_duration
tokens_per_second
queue_wait
tool_duration
task_duration
```

This allows later analysis.

---

# 32. PERFORMANCE METRICS

Measure:

## Inference

```text
time_to_first_token
tokens_per_second
total_generation_time
input_tokens
output_tokens
```

## System

```text
memory pressure
swap usage
CPU utilization
GPU utilization where available
```

## Agent

```text
task completion time
number of inference calls
number of tool calls
number of retries
```

## Context

```text
context size
retrieval latency
compression ratio
```

---

# 33. EFFICIENCY METRIC

Track:

```text
useful_result / compute_cost
```

Possible practical measurements:

```text
successful task
per inference call

successful task
per generated token

successful task
per minute

successful task
per resource unit
```

The goal is not maximum tokens/second alone.

The goal is useful work per unit of compute.

---

# 34. MODEL BENCHMARKING

Before selecting permanent defaults, benchmark each installed model.

Record:

```text
model
quantization
context size
tokens/sec
time to first token
RAM impact
task success
quality
thermal behavior
```

Example:

```text
Model A
Fast
Low RAM
Moderate quality

Model B
Slow
Higher RAM
High reasoning quality
```

The Model Manager can then choose intelligently.

---

# 35. HARDWARE-AWARE DEFAULTS

For the M4 16 GB:

```text
Heavy inference concurrency:
1 by default

Context:
~6K–12K initially

Models:
prefer 7B/8B quantized

Background agents:
low priority

Long autonomous loops:
budgeted

Large tool outputs:
compressed

Large browser pages:
filtered

Model switching:
minimize

Telemetry:
always enabled
```

These are starting points, not permanent limits.

---

# 36. FAILURE HANDLING

If inference fails due to resource pressure:

```text
Inference failure
      ↓
Check resource state
      ↓
Reduce context
      ↓
Retry once
      ↓
If still failing:
      ↓
Queue / fallback / ask user
```

Do not enter infinite retry loops.

Maximum retries must be bounded.

---

# 37. MODEL UNLOADING

The Model Manager should be able to release models that are no longer useful.

Conceptually:

```text
model unused
+
memory pressure
+
no queued task requiring it
        ↓
unload/release
```

Avoid aggressive unloading when a model is about to be reused.

Use an inactivity threshold and workload prediction.

---

# 38. BACKGROUND MAINTENANCE

Background operations include:

```text
memory cleanup
summary generation
database maintenance
Git checkpoint preparation
analytics
indexing
```

These must run only when resources are available.

They must never compete aggressively with user-facing inference.

---

# 39. AGENT SOCIETY RESOURCE RULE

Agents are autonomous in deciding what they want to accomplish.

They are NOT autonomous in consuming unlimited resources.

Architecture:

```text
Agent:
"I want to run this experiment."

Resource Manager:
"You may run it with:
- model X
- 8K context
- 1,000 output tokens
- 5 tool calls
- 10 minute budget."
```

The agent may then accept, modify, defer, or ask the user.

---

# 40. USER CONTROL

Expose commands through the CLI:

```text
/status
/resources
/models
/queue
/pause
/resume
/stop
/budget
/agents
/temperature
/benchmark
```

Example:

```text
/resources

Memory: 10.8 / 16 GB
Pressure: GREEN
Active model: Qwen3 8B
Context: 7.4K
Inference: 18 tok/s
Queue: 2
Agents running: 1
```

The exact commands may change during implementation.

---

# 41. SAFETY RULE

The Resource Manager must prioritize system stability over autonomous agent activity.

If the system approaches an unsafe resource state:

```text
PAUSE AUTONOMOUS ACTIVITY
        ↓
CHECKPOINT
        ↓
RELEASE RESOURCES
        ↓
WAIT
```

Never allow an autonomous loop to intentionally destabilize the host system.

---

# 42. ACCEPTANCE CRITERIA

The Resource Manager is functional when:

- [ ] Resource state is observable.
- [ ] Memory pressure is monitored.
- [ ] Model loading is coordinated.
- [ ] Concurrent heavy inference is controlled.
- [ ] Agents have task budgets.
- [ ] Inference calls are bounded.
- [ ] Output token budgets are enforced.
- [ ] Context budgets are coordinated with Context Manager.
- [ ] Background tasks have lower priority.
- [ ] User tasks have highest priority.
- [ ] Autonomous loops can be paused.
- [ ] User interruption works.
- [ ] Resource telemetry is stored.
- [ ] Model performance can be benchmarked.
- [ ] Failed inference does not create infinite retries.
- [ ] Model switching is minimized.
- [ ] System remains usable during autonomous operation.
- [ ] Resource behavior is tested on M4 16 GB.

---

# 43. IMPLEMENTATION ORDER

Implement in this order:

```text
1. Resource telemetry
2. Resource state machine
3. Model Manager integration
4. Inference queue
5. Concurrency limit
6. Context budget integration
7. Agent task budgets
8. Output token budgets
9. Priority scheduler
10. User interruption
11. Failure/retry policy
12. Model unloading
13. Thermal-aware scheduling
14. Browser/tool resource control
15. SQLite telemetry
16. Benchmarking
17. Dynamic optimization
```

Do not implement advanced predictive scheduling before basic measurements exist.

---

# 44. FINAL ARCHITECTURE

```text
                         AGENT SOCIETY
                              │
                 ┌────────────┴────────────┐
                 ↓                         ↓
          CONTEXT MANAGER            RESOURCE MANAGER
                 │                         │
                 │                 ┌───────┼────────┐
                 │                 ↓       ↓        ↓
                 │                RAM     CPU      GPU
                 │                         │
                 └────────────┬────────────┘
                              ↓
                       MODEL MANAGER
                              ↓
                       AGENT SCHEDULER
                              ↓
                       INFERENCE QUEUE
                              ↓
                            Ollama
                              ↓
                         M4 16 GB
```

---

# 45. NON-NEGOTIABLE RULES

1. Never assume all installed models should remain loaded.
2. Never run unlimited concurrent inference.
3. Never allow autonomous agents unlimited inference calls.
4. Never allow context to grow without a budget.
5. Never use an LLM for deterministic operations when normal code can solve them.
6. Never allow background work to starve user requests.
7. Never retry failed inference indefinitely.
8. Never intentionally consume all available system memory.
9. Never let autonomous activity compromise host-system stability.
10. Measure before optimizing.
11. Prefer smaller useful work over larger unnecessary work.
12. Preserve state before pausing or stopping autonomous activity.
13. Keep resource decisions separate from agent capability decisions.
14. Let agents decide what they need; let the Resource Manager decide what the hardware can afford.
15. Optimize for useful intelligence per unit of compute.

---

# 46. DESIGN GOAL

The Resource Manager should make the agent society feel lightweight even when running relatively capable local models.

The target behavior is:

```text
Agent needs intelligence
        ↓
Resource Manager checks cost
        ↓
Context Manager minimizes input
        ↓
Model Manager selects appropriate model
        ↓
Scheduler controls execution
        ↓
LLM performs useful inference
        ↓
Resources released
        ↓
System remains responsive
```

The objective is not to maximize hardware utilization.

The objective is:

> Maximum useful agent intelligence with minimum unnecessary compute, memory, heat, latency, and energy.
