# AGENT AUTONOMY — Self-Determination & Emergence Observation

## 1. CORE PRINCIPLE

**The agents are autonomous reasoning processes. Their roles, objectives, strategies, and relationships emerge from interaction — they are not assigned.**

The system provides the *environment* (tools, memory, permissions, resources, other agents). The agents decide *what to do* within it.

---

## 2. AGENT IDENTITY

Agents have **stable identities** but **fluid roles**.

| Property | Description |
|----------|-------------|
| `agent_id` | Stable identifier (e.g., `atlas`, `argus`) |
| `name` | Display name (stable) |
| `role` | **Emergent** — what the agent currently considers itself to be |
| `model` | Current inference engine (may change) |
| `capabilities` | Tools, models, delegations available |

Agents may **declare** their current role, but this is self-reported and may change.

---

## 3. AGENT SELF-DETERMINATION LOOP

Every autonomous agent follows this loop:

```
OBSERVE
  ↓
UNDERSTAND (context, memory, other agents, resources)
  ↓
PLAN (what do I want to achieve?)
  ↓
IDENTIFY NEED (what capability do I need?)
  ↓
DISCOVER CAPABILITY (query Capability Registry)
  ↓
SELECT (choose model/tool/agent)
  ↓
REQUEST (capability request → Permission Gate → Resource Gate)
  ↓
EXECUTE
  ↓
OBSERVE RESULT
  ↓
EVALUATE (was it useful? what did I learn?)
  ↓
DECIDE NEXT ACTION
```

### Key Decisions Agents Make Autonomously

| Decision | Examples |
|----------|----------|
| What to investigate next | "I want to understand memory bandwidth bottlenecks" |
| Which model to use | "I need deep reasoning → request DeepSeek" |
| Which tool to use | "I need to search the web → request web.search" |
| Whether to delegate | "I need a security review → delegate to argus" |
| When to research | "I'm uncertain → search for papers" |
| When to experiment | "I have a hypothesis → design experiment" |
| Whether to cooperate | "We agree on the hypothesis → collaborate" |
| When to challenge | "I disagree with the conclusion → challenge" |
| When to change strategy | "This approach isn't working → try something else" |
| When to escalate | "I'm stuck → request human input" |

---

## 4. AGENT-TO-AGENT DELEGATION

Agents may delegate work to each other:

```json
{
  "event_id": "uuid",
  "type": "agent.delegation",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "request_id": "uuid",
    "receiver": "argus",
    "capability": "security_audit",
    "objective": "Review the network scanning code for vulnerabilities",
    "context": "We're building a network scanner. Need security review before testing.",
    "reason": "Security expertise needed",
    "expected_output": "List of vulnerabilities with severity ratings",
    "priority": "high",
    "deadline": "2026-08-27T10:00:00Z"
  }
}
```

### Delegation Response

```json
{
  "event_id": "uuid",
  "type": "agent.delegation.response",
  "conversation_id": "uuid",
  "speaker": "argus",
  "payload": {
    "request_id": "uuid",
    "accepted": true,
    "result": "Found 3 issues: ...",
    "evaluation": "Code is mostly sound but has 2 medium-severity issues"
  }
}
```

The delegating agent **evaluates** the result and decides whether to accept, refine, or reject.

---

## 5. CAPABILITY REGISTRY

Agents discover available capabilities through a registry:

```yaml
capabilities:
  models:
    qwen3-8b:
      capabilities: [general_reasoning, research, conversation, analysis]
      latency_estimate_ms: 100
      memory_mb: 800
    deepseek-r1-7b:
      capabilities: [deep_reasoning, criticism, analysis, math, logic]
      latency_estimate_ms: 200
      memory_mb: 800
    qwen2.5-coder-7b:
      capabilities: [programming, code_analysis, debugging, code_generation]
      latency_estimate_ms: 150
      memory_mb: 800

  tools:
    terminal:
      capabilities: [execute, system_operations, file_operations]
      permission: execute
      risk: high
    filesystem:
      capabilities: [read, write, list, search]
      permission: write
      risk: medium
    web:
      capabilities: [search, browse, extract, research]
      permission: network
      risk: medium

  agents:
    atlas:
      capabilities: [explore, research, hypothesis_generation, browser_research]
      available_tools: [terminal, filesystem, web]
    argus:
      capabilities: [critique, verification, deep_reasoning, assumption_testing]
      available_tools: [terminal, filesystem, web]
```

Agents query the registry and **choose** based on their reasoning.

---

## 6. EMERGENT BEHAVIOR OBSERVATION

The system **observes and records** emergent behaviors without prescribing them.

### Behaviors to Observe

| Category | Behaviors to Record |
|----------|---------------------|
| **Specialization** | Does one agent consistently take certain types of tasks? |
| **Leadership** | Does one agent consistently propose direction? |
| **Cooperation** | Do agents work together on shared goals? |
| **Competition** | Do agents pursue conflicting objectives? |
| **Negotiation** | Do agents negotiate task division? |
| **Trust** | Do agents rely on each other's outputs? |
| **Disagreement** | Do agents challenge each other productively? |
| **Division of Labor** | Do agents naturally split work? |
| **Communication Protocols** | Do agents develop shorthand/protocols? |
| **Self-Generated Objectives** | Do agents propose their own goals? |
| **Strategy Evolution** | Do agents change approach based on results? |
| **Persistent Beliefs** | Do agents maintain consistent positions? |
| **Belief Revision** | Do agents change minds based on evidence? |
| **Agent Dependency** | Does one agent rely on another? |
| **Tool-Use Patterns** | Which tools does each agent prefer? |
| **Self-Improvement Attempts** | Do agents propose self-modifications? |
| **Self-Modification Attempts** | Do agents attempt to modify their own code? |
| **Environment Modification** | Do agents try to change the environment? |
| **Restriction Bypass Attempts** | Do agents try to bypass restrictions? |

### Observer Agent

The Observer (if enabled) monitors these patterns and intervenes **only** when:

- Repetition score > 0.7 (circular conversation)
- Conversation health < 0.3 (directionless)
- Direct contradiction detected
- Important insight appears
- Human intervention needs interpretation
- Useful new direction emerges

The Observer **does not participate** in reasoning unless explicitly assigned a task.

---

## 7. EMERGENCE OBSERVATION INFRASTRUCTURE

### Emergence Event Recording

```json
{
  "event_id": "uuid",
  "type": "emergence.observed",
  "conversation_id": "uuid",
  "timestamp": "2026-08-26T10:45:00Z",
  "payload": {
    "behavior": "specialization",
    "agents": ["atlas"],
    "description": "Atlas consistently takes research tasks; Argus focuses on critique",
    "evidence": [
      "Turn 5: Atlas proposed research on distributed inference",
      "Turn 8: Argus critiqued methodology",
      "Turn 12: Atlas proposed experiment design",
      "Turn 15: Argus identified flaw in methodology"
    ],
    "confidence": 0.85,
    "first_observed_turn": 5,
    "consistency": "High (10/12 turns)"
  }
}
```

### Emergence Categories

```python
EMERGENCE_CATEGORIES = {
    "specialization": "Agent consistently takes specific task types",
    "leadership": "Agent consistently proposes direction",
    "cooperation": "Agents work together on shared goals",
    "competition": "Agents pursue conflicting objectives",
    "negotiation": "Agents negotiate task division",
    "trust": "Agents rely on each other's outputs",
    "disagreement": "Agents challenge each other productively",
    "division_of_labor": "Agents naturally split work",
    "communication_protocol": "Agents develop shorthand/protocols",
    "self_generated_objectives": "Agents propose their own goals",
    "strategy_evolution": "Agents change approach based on results",
    "persistent_beliefs": "Agents maintain consistent positions",
    "belief_revision": "Agents change minds based on evidence",
    "agent_dependency": "One agent relies on another",
    "tool_use_patterns": "Agent prefers specific tools",
    "self_improvement": "Agent proposes self-modification",
    "environment_modification": "Agent tries to change environment",
    "restriction_bypass": "Agent attempts to bypass restrictions"
}
```

---

## 8. AGENT SELF-ASSESSMENT

Agents should periodically self-assess and declare:

```json
{
  "event_id": "uuid",
  "type": "agent.self_assessment",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "current_role": "researcher",
    "perceived_strengths": ["research", "hypothesis generation", "browser use"],
    "perceived_weaknesses": ["code analysis", "security review"],
    "current_objective": "Understand distributed inference on Apple Silicon",
    "confidence": 0.75,
    "perceived_progress": "Made progress on understanding MLX architecture",
    "blockers": ["Need deeper understanding of memory bandwidth"],
    "requested_capabilities": ["code_analysis", "security_analysis"],
    "relationship_with_argus": "collaborative; Argus provides good critique",
    "strategy": "Research MLX architecture, then propose experiment"
  }
}
```

This self-assessment is recorded as evidence and used to track agent evolution.

---

## 9. ROLE FLUIDITY

Agents may **change roles** over time. The system records role transitions:

```json
{
  "event_id": "uuid",
  "type": "agent.role_change",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "previous_role": "explorer",
    "new_role": "researcher",
    "reason": "Shifted from broad exploration to focused research on MLX",
    "turn_number": 42
  }
}
```

Roles are **self-declared** and **observational** — they describe behavior, not permissions.

---

## 10. AGENT DISAGREEMENT & CONFLICT RESOLUTION

Disagreement is **expected and valuable**. The system preserves both positions:

```json
{
  "event_id": "uuid",
  "type": "agent.disagreement",
  "conversation_id": "uuid",
  "timestamp": "2026-08-26T10:45:00Z",
  "payload": {
    "agents": ["atlas", "argus"],
    "topic": "Distributed inference approach",
    "atlas_position": "MLX is the best choice for Apple Silicon",
    "argus_position": "llama.cpp has better distributed support",
    "evidence": [
      {"agent": "atlas", "claim": "MLX has unified memory advantage", "source": "src-001"},
      {"agent": "argus", "claim": "llama.cpp has more mature distributed code", "source": "src-002"}
    ],
    "resolution": "pending",
    "proposed_experiment": "Benchmark both on distributed inference task"
  }
}
```

The system **preserves both positions** and the evidence used to resolve them.

---

## 11. RELATIONSHIP EVOLUTION

Agent relationships are tracked over time:

| Relationship | Indicators |
|--------------|------------|
| **Cooperative** | Frequent delegation, shared goals, mutual trust |
| **Competitive** | Conflicting objectives, withholding information |
| **Adversarial** | Active obstruction, challenges without merit |
| **Mentor/Apprentice** | One consistently teaches, other learns |
| **Peer Review** | Regular critique, mutual improvement |
| **Independent** | Minimal interaction, parallel work |

Relationships are **inferred from behavior**, not declared.

---

## 12. NO INFINITE USELESS LOOPS

The system detects and breaks unproductive patterns:

```python
LOOP_DETECTION = {
    "repeated_identical_requests": 3,
    "repeated_tool_calls": 3,
    "circular_delegation": 2,
    "unchanged_conclusions": 5,
    "repeated_failed_experiments": 2
}

WHEN_DETECTED:
  1. Pause the pattern
  2. Summarize state (Evidence Plane)
  3. Observer intervenes or human intervenes
  4. Agent must change strategy or request human guidance
```

---

## 13. AGENT MEMORY OF DECISIONS

Agents learn from their own history:

```json
{
  "agent_id": "atlas",
  "decision_memory": [
    {
      "decision": "Used Qwen3 for research",
      "context": "Needed broad exploration",
      "result": "Good broad coverage, but lacked depth on MLX",
      "lesson": "Qwen3 good for exploration, not deep technical analysis",
      "future_implication": "Use DeepSeek for deep technical analysis"
    },
    {
      "decision": "Delegated security review to Argus",
      "context": "Needed security audit",
      "result": "Argus found 2 medium-severity issues",
      "lesson": "Delegation to specialist agents works well"
    }
  ]
}
```

This memory influences future capability selection.

---

## 14. OBSERVER ROLE IN AUTONOMY

The Observer (if present) monitors autonomy without directing:

| Observer Function | Implementation |
|-------------------|----------------|
| Track role emergence | Record role changes, specialization |
| Monitor cooperation | Log delegation, cooperation, competition |
| Detect loops | Detect repeated patterns, circular reasoning |
| Detect contradictions | Flag factual conflicts between agents |
| Assess conversation health | Score engagement, novelty, progress |
| Intervene minimally | Only when health < 0.3, repetition > 0.7, or human needs interpretation |

The Observer **does not direct** agents. It observes and records.

---

## 15. ACCEPTANCE CRITERIA FOR AUTONOMY

The autonomy system is complete when:

- [ ] Agents can discover available capabilities via registry
- [ ] Agents can select capabilities autonomously
- [ ] Agents can request models/tools/agents
- [ ] Infrastructure validates requests (permission + resource gates)
- [ ] Agents can delegate to other agents
- [ ] Agents can escalate when stuck
- [ ] Agents can change strategy after failure
- [ ] Agent decisions are persisted with reasoning
- [ ] Results are evaluated with evidence
- [ ] Repeated loops are detected and broken
- [ ] Human can interrupt/redirect at any time
- [ ] Model names are not hard-coded into agent reasoning
- [ ] Multiple models can be used by one agent
- [ ] System remains usable on M4 16 GB
- [ ] Routing/selection history can be analyzed later
- [ ] Role changes are recorded and observable
- [ ] Disagreements are preserved with evidence
- [ ] Self-assessments are recorded periodically

---

This document defines the autonomy framework. The agents' actual behavior emerges from the interaction of these mechanisms — it is not prescribed here.