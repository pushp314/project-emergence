# CONTEXT_MANAGER.md

## Context Manager Algorithm
### Memory, Retrieval, Summarization, Context Budgets, and Context Explosion Prevention

---

# 1. PURPOSE

The Context Manager controls what information an agent receives during each model invocation.

The system must NOT continuously send an agent's entire conversation history, memory, research history, tool output, or evidence.

The Context Manager must:

- maintain a bounded working context
- retrieve relevant long-term memory
- retrieve relevant evidence
- summarize older conversations when necessary
- discard irrelevant information from active context
- preserve important information in persistent storage
- build task-specific context packets
- adapt context size to the selected model
- reduce unnecessary inference cost
- prevent context-window explosion
- reduce RAM usage and latency on Apple M4 16 GB
- preserve traceability and evidence

Core principle:

> Persistent memory stores the history. The Context Manager decides what deserves the model's attention right now.

---

# 2. DESIGN PRINCIPLE

Never implement:

```text
Entire history
      ↓
      LLM
```

Implement:

```text
Current Task
     +
Relevant Recent Context
     +
Relevant Memory
     +
Relevant Evidence
     +
Current Agent State
     ↓
Context Manager
     ↓
Bounded Context Packet
     ↓
LLM
```

---

# 3. CONTEXT LAYERS

The system should maintain four primary context layers.

## Layer 1 — Working Context

Contains:

- current user request
- current objective
- active reasoning/task state
- current tool operation
- immediate constraints
- unresolved question

This has the highest priority.

---

## Layer 2 — Recent Context

Contains the most relevant recent interaction.

Do not simply use the last N messages.

Select recent messages based on:

- recency
- task relevance
- dependency
- unresolved references

---

## Layer 3 — Long-Term Memory

Contains information from previous interactions and sessions.

Examples:

- previous decisions
- learned facts
- successful approaches
- failed approaches
- agent preferences/behavior
- previous task outcomes
- important discoveries
- open questions

Retrieve only what is relevant to the current task.

---

## Layer 4 — Evidence

Contains externally or experimentally supported information.

Examples:

- browser sources
- URLs
- extracted claims
- command results
- experiment results
- test results
- artifacts
- verification status

Evidence must remain independently addressable.

A summary must never replace the underlying evidence.

---

# 4. CONTEXT PACKET

Every LLM invocation should receive a structured Context Packet.

Recommended structure:

```text
[IDENTITY]
Agent identity and role

[OBJECTIVE]
Current task/objective

[CURRENT STATE]
Current phase and state

[RECENT CONTEXT]
Relevant recent interaction

[RELEVANT MEMORY]
Retrieved long-term memory

[EVIDENCE]
Relevant evidence

[OPEN QUESTIONS]
Unresolved questions

[CONSTRAINTS]
Available tools, permissions, resources

[EXPECTED OUTPUT]
What the model must produce
```

Do not include sections that are empty or irrelevant.

---

# 5. CONTEXT BUDGET

The Context Manager must maintain a token budget for every invocation.

Initial target budgets for the current M4 16 GB environment:

| Model | Initial Target Context |
|---|---:|
| Qwen3 8B | ~8K–10K tokens |
| DeepSeek-R1-Distill-Qwen-7B | ~8K–12K tokens |
| Dolphin3-Cyber-8B | ~8K–10K tokens |
| Qwen2.5-Coder-7B | ~6K–10K tokens |
| Other models | Determine experimentally |

These are starting budgets, not immutable limits.

The Resource Manager may reduce them under memory pressure.

Do not maximize context merely because a model technically supports a larger window.

---

# 6. INITIAL CONTEXT ALLOCATION

A starting allocation can be:

```text
System / identity          1,000–1,500
Current task                  500–1,000
Recent context              2,000–3,000
Relevant memory             1,000–2,000
Evidence                    1,000–2,000
Agent state                   300–500
Tool/permission rules         500–1,000
------------------------------------------------
Target                     ~7K–11K
```

The Context Manager must dynamically adjust these values.

Never blindly allocate the maximum to every category.

---

# 7. MODEL-SPECIFIC CONTEXT

Different tasks require different context.

## Research

Prioritize:

```text
question
+
sources
+
evidence
+
open questions
+
relevant previous research
```

## Coding

Prioritize:

```text
objective
+
relevant files
+
interfaces
+
errors
+
tests
+
recent code changes
```

Do not send an entire repository.

## Cybersecurity analysis

Prioritize:

```text
target
+
relevant code/configuration
+
security evidence
+
known assumptions
+
previous findings
```

## Criticism / Challenger

Prioritize:

```text
claim
+
reasoning/result being challenged
+
supporting evidence
+
contradicting evidence
+
specific question
```

---

# 8. RETRIEVAL PIPELINE

When an agent needs context:

```text
Current Task
     ↓
Context Query
     ↓
Candidate Retrieval
     ↓
Relevance Ranking
     ↓
Deduplication
     ↓
Compression
     ↓
Budget Selection
     ↓
Context Packet
```

---

# 9. CONTEXT QUERY GENERATION

Generate retrieval queries from the current task.

Example:

```text
Task:
"Determine whether this vulnerability exists in the current implementation."

Queries:

- previous vulnerability findings
- relevant repository findings
- previous experiments
- security assumptions
- related evidence
- previous failed approaches
```

Do not retrieve all memories.

---

# 10. RELEVANCE SCORING

Each candidate memory/evidence item should receive a relevance score.

Initial conceptual scoring:

```text
score =
    semantic_relevance
  + task_relevance
  + recency
  + importance
  + reliability
  + dependency_relevance
  - token_cost
```

The exact weights should be configurable.

Example:

```text
Memory:
"Previous attempt using approach X failed."

High:
- task relevance
- importance
- reliability

Low:
- recency

Result:
INCLUDE
```

Unrelated historical information:

```text
Low task relevance
Low dependency
Low importance

Result:
EXCLUDE FROM ACTIVE CONTEXT
```

---

# 11. DO NOT DELETE DISCARDED CONTEXT

Important rule:

> Removing information from active context is not the same as deleting information from persistent storage.

When information is discarded from the LLM context:

```text
Active Context
      ↓
Remove
      ↓
Persistent Memory / Evidence remains
```

This allows future retrieval.

---

# 12. DEDUPLICATION

Before building the Context Packet:

Detect:

- duplicate messages
- repeated facts
- duplicate search results
- duplicate evidence
- repeated tool output
- repeated summaries

Keep the highest-quality representation.

Example:

```text
10 identical search results
        ↓
1 source record
+
relevant evidence
```

---

# 13. BROWSER RESULT COMPRESSION

Never blindly send entire webpages to the model.

Pipeline:

```text
Web page
   ↓
Extract relevant content
   ↓
Remove navigation/ads/boilerplate
   ↓
Identify relevant passages
   ↓
Create evidence record
   ↓
Send only relevant material to LLM
```

Target:

```text
Raw page:       20,000 tokens
Relevant data:    500–1,500 tokens
```

Keep the original source available as an artifact/evidence record.

---

# 14. TOOL OUTPUT COMPRESSION

Large terminal/tool outputs must be compressed.

Example:

```text
10,000 lines of test output
        ↓
Summary:
23 passed
2 failed

Relevant errors:
...

Affected files:
...
```

Store the complete output as an artifact.

Send only the relevant result to the LLM.

---

# 15. AGENT-TO-AGENT CONTEXT

Never automatically transfer an agent's entire memory to another agent.

Instead:

```text
Agent A
   ↓
Delegation Request
   ↓
Context Manager
   ↓
Relevant Context
   ↓
Agent B
```

Agent B should receive:

- objective
- specific question
- relevant evidence
- relevant memory
- relevant previous result
- constraints
- expected output

This prevents context explosion between agents.

---

# 16. SUMMARIZATION POLICY

Do not summarize every message.

Summarize when:

1. context pressure becomes high
2. a task phase ends
3. a session checkpoint occurs
4. a major experiment completes
5. a long conversation contains redundant information
6. the agent has accumulated substantial irrelevant history

---

# 17. CONTEXT PRESSURE LEVELS

Monitor:

```text
current_context_tokens
context_budget
```

Initial policy:

```text
< 50%       NORMAL

50–70%      MONITOR

70–85%      COMPACTION PREPARATION

> 85%       AGGRESSIVE COMPACTION
```

The exact thresholds should be configurable and benchmarked.

---

# 18. SUMMARIZATION TYPES

Do not maintain one giant summary.

Use hierarchical summaries.

```text
Raw Messages
     ↓
Turn / Segment Summary
     ↓
Task Summary
     ↓
Session Summary
     ↓
Long-Term Knowledge
```

---

# 19. TASK SUMMARY

A task summary should contain:

```text
Objective
Current approach
Important discoveries
Important failures
Decisions
Evidence references
Open questions
Current state
Next recommended action
```

Avoid conversational filler.

---

# 20. SESSION SUMMARY

At session boundaries create:

```text
Session ID
Participants
Objective
Major events
Research performed
Experiments
Important evidence
Decisions
Failures
Discoveries
Open questions
Unfinished tasks
Current system state
```

---

# 21. EVIDENCE MUST SURVIVE SUMMARIZATION

Never replace evidence with a vague summary.

Bad:

```text
"The internet confirmed the claim."
```

Good:

```text
Claim
Source
URL
Relevant passage
Timestamp
Evidence ID
Verification status
Agent
```

The summary should reference the Evidence ID.

---

# 22. MEMORY WRITE POLICY

Do not save every model response as permanent memory.

Extract only durable information.

Potential memory candidates:

- important decisions
- discovered facts
- successful methods
- failed methods
- important assumptions
- persistent preferences
- unresolved questions
- validated knowledge
- important agent experiences

Do not permanently store:

- greetings
- repetitive wording
- trivial intermediate reasoning
- temporary tool noise
- irrelevant conversation

---

# 23. MEMORY WRITE PIPELINE

```text
LLM Response
     ↓
Memory Candidate Extraction
     ↓
Importance Check
     ↓
Deduplication
     ↓
Reliability Check
     ↓
Persist
     ↓
SQLite
```

---

# 24. MEMORY TYPES

Use at least:

```text
episodic_memory
semantic_memory
decision_memory
procedural_memory
failure_memory
evidence_reference
open_question
```

Examples:

### Episodic

"What happened during Session #12?"

### Semantic

"What is currently known about X?"

### Decision

"Agent selected approach Y because..."

### Procedural

"Method Y worked for task type Z."

### Failure

"Approach X previously failed because..."

### Evidence

"Source/evidence supporting claim Y."

### Open Question

"Question X remains unresolved."

---

# 25. CONTEXT PRIORITY

When context exceeds the budget, preserve information in this order:

```text
1. Current objective
2. Critical constraints
3. Required system/tool instructions
4. Directly relevant evidence
5. Current state
6. Relevant recent interaction
7. Important decisions
8. Relevant long-term memory
9. Supporting context
10. Old conversational detail
```

Low-priority material should be removed first.

---

# 26. CONTEXT COMPACTION ALGORITHM

Conceptual implementation:

```python
def build_context(agent, task):

    budget = resource_manager.get_context_budget(agent)

    current = get_current_task(task)

    recent = get_relevant_recent_context(
        task=task
    )

    queries = generate_context_queries(
        task=task,
        current_state=agent.state
    )

    memories = retrieve_memory(queries)

    evidence = retrieve_evidence(queries)

    candidates = merge(
        current,
        recent,
        memories,
        evidence
    )

    candidates = deduplicate(candidates)

    ranked = rank_relevance(
        candidates,
        task
    )

    compressed = compress_large_items(
        ranked
    )

    context = fit_to_budget(
        compressed,
        budget
    )

    return build_context_packet(context)
```

---

# 27. POST-RESPONSE MEMORY UPDATE

After inference:

```python
def update_after_response(response):

    decisions = extract_decisions(response)

    discoveries = extract_discoveries(response)

    failures = extract_failures(response)

    open_questions = extract_open_questions(response)

    evidence_refs = extract_evidence_references(response)

    persist_to_sqlite(
        decisions,
        discoveries,
        failures,
        open_questions,
        evidence_refs
    )

    update_task_summary()

    update_session_summary_if_needed()
```

---

# 28. CONTEXT CACHE

Use caching to avoid repeatedly retrieving and compressing identical context.

Cache:

```text
task context
retrieved memories
evidence selection
summaries
tool result summaries
```

Invalidate when:

- task changes significantly
- new critical evidence arrives
- agent state changes
- relevant memory changes
- permissions/resources change in a way that affects the task

Do not allow stale context to silently override newer information.

---

# 29. CONTEXT VERSIONING

Every Context Packet should have:

```text
context_id
session_id
agent_id
task_id
timestamp
memory_versions
evidence_versions
summary_versions
token_count
```

This makes model behavior reproducible.

---

# 30. RESOURCE-AWARE CONTEXT

The Context Manager must cooperate with the Resource Manager.

If the Mac is under memory pressure:

```text
Memory pressure
      ↓
Reduce context budget
      ↓
Retrieve fewer memories
      ↓
Compress tool outputs more aggressively
      ↓
Reduce concurrent inference
```

Do not blindly increase context when performance is poor.

---

# 31. LATENCY-AWARE RETRIEVAL

Track:

```text
retrieval latency
compression latency
inference latency
total context-building latency
```

If retrieval takes longer than the inference it is helping, simplify the retrieval pipeline.

For the initial implementation:

> Prefer SQLite metadata/full-text retrieval and lightweight ranking before introducing heavy infrastructure.

---

# 32. PREVENT CONTEXT EXPLOSION

The system must prevent:

```text
Agent A memory
+
Agent B memory
+
Shared memory
+
Entire browser history
+
Entire tool output
+
Entire repository
+
Entire conversation
```

from entering one context.

Use:

```text
bounded retrieval
+
relevance ranking
+
deduplication
+
compression
+
task-specific context
+
token budget
```

---

# 33. AGENT SOCIETY CONTEXT ISOLATION

In the multi-agent system:

```text
Shared Memory
      │
      ├── Agent A retrieves what it needs
      │
      ├── Agent B retrieves what it needs
      │
      └── Observer retrieves what it needs
```

Do not automatically broadcast every event into every agent's context.

Events may be globally logged while only relevant events are surfaced to an agent.

---

# 34. OPEN QUESTIONS

Open questions should have high retrieval priority when they are related to the current task.

Example:

```text
Open Question:
"Does approach X work under condition Y?"

Current task:
Testing approach X under condition Y.

→ Retrieve automatically.
```

---

# 35. FAILED APPROACHES

Failure memory is valuable.

If an agent previously attempted:

```text
Approach X → failed
```

and the current task resembles that previous task:

```text
Retrieve failure memory.
```

The agent should see:

```text
Previous attempt
Failure
Reason
Evidence
Alternative tried
```

This prevents repeating the same mistake.

---

# 36. CONTEXT QUALITY CHECK

Before sending a Context Packet, validate:

```text
[ ] Current task present
[ ] Identity present
[ ] Relevant constraints present
[ ] Relevant evidence present
[ ] No major duplicates
[ ] No huge raw tool output
[ ] No irrelevant memory
[ ] Token budget respected
[ ] Recent state is current
[ ] Evidence references are preserved
```

If validation fails, rebuild the packet.

---

# 37. CONTEXT TELEMETRY

Store metrics in SQLite:

```text
context_id
agent_id
task_id
input_tokens
output_tokens
context_tokens
memory_tokens
evidence_tokens
recent_context_tokens
summary_tokens
retrieval_count
compression_ratio
retrieval_latency
total_context_build_latency
inference_latency
```

This allows later optimization.

---

# 38. EXPERIMENTAL OPTIMIZATION

Do not assume the initial numbers are optimal.

Benchmark:

```text
6K context
8K context
10K context
12K context
```

Measure:

- response quality
- latency
- RAM usage
- model throughput
- task success
- unnecessary retrieval
- thermal/resource behavior

Choose the smallest context that maintains acceptable quality.

---

# 39. DO NOT ADD HEAVY INFRASTRUCTURE PREMATURELY

Initial implementation should prefer:

```text
SQLite
+
metadata filtering
+
SQLite FTS where useful
+
lightweight relevance ranking
+
structured summaries
```

Only introduce:

- vector database
- embedding pipeline
- reranker
- advanced retrieval service

when measurements show they provide meaningful benefit.

The Context Manager must remain lightweight on the M4 16 GB system.

---

# 40. ACCEPTANCE CRITERIA

The Context Manager is considered functional when:

- [ ] Agents do not receive entire conversation history by default.
- [ ] Current task is always represented.
- [ ] Relevant memory can be retrieved.
- [ ] Relevant evidence can be retrieved.
- [ ] Old context can be summarized.
- [ ] Irrelevant context is excluded.
- [ ] Large browser results are compressed.
- [ ] Large tool outputs are compressed.
- [ ] Agent-to-agent context is bounded.
- [ ] Context budgets are enforced.
- [ ] Context budgets can adapt to resource pressure.
- [ ] Persistent data survives context removal.
- [ ] Evidence survives summarization.
- [ ] Memory writes are selective.
- [ ] Context usage is measured.
- [ ] Retrieval latency is measured.
- [ ] Context versions are traceable.
- [ ] Context explosion is prevented.
- [ ] Tests cover compaction and retrieval.
- [ ] Performance is acceptable on M4 16 GB.

---

# 41. IMPLEMENTATION ORDER

Implement in this order:

```text
1. Context Packet schema
2. Token counting
3. Context budget
4. Recent-context selection
5. SQLite memory retrieval
6. Evidence retrieval
7. Deduplication
8. Basic relevance ranking
9. Tool-output compression
10. Browser-result compression
11. Summarization
12. Memory writing
13. Context-pressure monitor
14. Resource-aware budgets
15. Context telemetry
16. Context caching
17. Benchmarking
18. Advanced retrieval only if justified
```

Do not build advanced RAG first.

---

# 42. FINAL ARCHITECTURE

```text
                         AGENT
                           │
                       CURRENT TASK
                           │
                           ▼
                 ┌───────────────────┐
                 │  CONTEXT MANAGER  │
                 └─────────┬─────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ↓                   ↓                   ↓
    Recent              Memory              Evidence
    Context            Retrieval            Retrieval
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ↓
                     Deduplication
                           ↓
                    Relevance Ranking
                           ↓
                      Compression
                           ↓
                     Token Budget
                           ↓
                  Resource Adjustment
                           ↓
                   Context Packet
                           ↓
                          LLM
                           ↓
                       Response
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
          Decisions    Discoveries   Failures
              │            │            │
              └────────────┼────────────┘
                           ↓
                     Memory Writer
                           ↓
                         SQLite
                           ↓
                    Future Retrieval
```

---

# 43. NON-NEGOTIABLE RULES

1. Never send all available memory to an agent by default.
2. Never send an entire browser page when only a section is relevant.
3. Never send an entire repository for a localized coding task.
4. Never send one agent's complete memory to another agent.
5. Never allow context to grow without a budget.
6. Never delete persistent evidence merely because it was removed from active context.
7. Never treat an agent-generated summary as equivalent to primary evidence.
8. Never increase context size blindly to compensate for poor reasoning.
9. Prefer retrieval and compression over larger prompts.
10. Measure context quality and resource cost before optimizing further.

---

# 44. DESIGN GOAL

The Context Manager should make a small local model feel more capable by giving it:

```text
the right information
at the right time
in the right amount
with the right evidence
```

rather than overwhelming it with everything the system knows.

The objective is not maximum context.

The objective is:

> **Maximum useful intelligence per token and per unit of compute.**
