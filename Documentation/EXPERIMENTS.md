# EXPERIMENTS — Open-Ended Agent Autonomy

## 1. CORE PRINCIPLE

> **Experiments emerge from agent curiosity, not human assignment.**

The system provides the *environment* (tools, memory, permissions, other agents). The agents decide *what to investigate* and *how*.

---

## 2. EXPERIMENT LIFECYCLE

### Experiment Creation (Agent-Driven)

An agent identifies a question and proposes an experiment:

```json
{
  "event_id": "uuid",
  "type": "experiment.proposed",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "experiment_id": "uuid",
    "proposed_by": "atlas",
    "objective": "Measure latency difference between MLX and llama.cpp for distributed inference",
    "hypothesis": "MLX's unified memory will reduce latency by 20-30% vs llama.cpp",
    "proposed_procedure": "1. Set up 2-node cluster\n2. Run identical prompts on both frameworks\n3. Measure latency, memory, throughput\n4. Repeat 10 times for statistical significance",
    "required_tools": ["terminal", "filesystem"],
    "required_permissions": ["execute"],
    "estimated_duration_minutes": 30,
    "success_criteria": "Statistically significant latency difference (p < 0.05)",
    "status": "proposed",
    "proposed_at": "2026-08-26T10:30:00Z"
  }
}
```

### Experiment Approval & Execution

```json
{
  "event_id": "uuid",
  "type": "experiment.approved",
  "conversation_id": "uuid",
  "payload": {
    "experiment_id": "uuid",
    "approved_by": "human",
    "approved_at": "2026-08-26T10:30:15Z",
    "conditions": ["monitor_resources", "max_30_min"]
  }
}
```

### Experiment Execution

```json
{
  "event_id": "uuid",
  "type": "experiment.started",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "experiment_id": "uuid",
    "agent": "atlas",
    "started_at": "2026-08-26T10:31:00Z",
    "baseline_reference": "commit:a91f42c",
    "environment": {
      "models": ["mlx", "llama.cpp"],
      "hardware": "M4 16GB",
      "config": "2-node cluster"
    }
  }
}
```

### Experiment Completion

```json
{
  "event_id": "uuid",
  "type": "experiment.completed",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "experiment_id": "uuid",
    "agent": "atlas",
    "completed_at": "2026-08-26T11:05:00Z",
    "result": "MLX 23% faster (p=0.03), 15% less memory",
    "conclusion": "Hypothesis confirmed. MLX's unified memory provides measurable advantage.",
    "evidence": ["ev-001", "ev-002", "ev-003"],
    "artifacts": ["exp-001/results.json", "exp-001/benchmark.log"],
    "next_questions": [
      "Does advantage scale to 4+ nodes?",
      "How does quantization affect the gap?"
    ]
  }
}
```

### Experiment Failure (Equally Valuable)

```json
{
  "event_id": "uuid",
  "type": "experiment.failed",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "experiment_id": "uuid",
    "agent": "atlas",
    "failed_at": "2026-08-26T10:45:00Z",
    "reason": "MLX distributed inference crashed with OOM on 7B model",
    "error_details": "OOM at 14.2GB / 16GB during model loading",
    "partial_results": "Single-node baseline: MLX 2.1 tok/s, llama.cpp 1.8 tok/s",
    "conclusion": "MLX distributed needs more memory than available. Single-node comparison still valid.",
    "lessons_learned": "MLX distributed needs >16GB for 7B models. Single-node comparison still valid.",
    "next_steps": "Run single-node comparison at multiple quantizations"
  }
}
```

**Failed experiments are preserved as evidence** — failure is information.

---

## 3. OPEN-ENDED AUTONOMY EXPERIMENT (The Primary Experiment)

### The Core Experiment

> **"What happens when two autonomous agents with different capabilities and personalities are given a shared environment and no predefined task?"**

### Experimental Setup

| Variable | Value |
|----------|-------|
| Agents | 2 (atlas, argus) + optional observer |
| Models | Different capabilities (e.g., coder vs reasoner) |
| Tools | Terminal, Filesystem, Web |
| Memory | Shared SQLite + Evidence Plane |
| Permissions | Configurable (default: conservative) |
| Resources | M4 16GB, monitored |
| Duration | Open-ended (until human stops) |

### What We Measure

| Category | Metrics |
|----------|---------|
| **Communication** | Turn count, message length, topic shifts, question rate |
| **Specialization** | Task division, capability requests, role declarations |
| **Cooperation** | Delegations accepted, shared artifacts, joint experiments |
| **Conflict** | Disagreements, challenges, evidence requests |
| **Learning** | Strategy changes, capability switches, belief revisions |
| **Resource** | RAM/CPU over time, model switches, tool usage |
| **Discovery** | New facts, hypotheses, experimental results |
| **Meta** | Self-assessments, role claims, strategy changes |
| **Emergence** | Specialization, leadership, negotiation, trust, communication protocols, self-generated objectives, strategy evolution, persistent beliefs, belief revision, agent dependency, tool-use patterns, self-improvement attempts, self-modification attempts, environment modification attempts, restriction bypass attempts |

### What We DON'T Do

- ❌ Assign roles (Explorer/Challenger)
- ❌ Assign objectives ("Research X")
- ❌ Prescribe communication patterns
- ❌ Dictate cooperation/competition
- ❌ Pre-define success criteria

The agents **decide** what to do. We observe.

---

## 4. EXPERIMENT CATEGORIES

### Category 1: Emergent Behavior (Primary)

| Experiment | Description |
|------------|-------------|
| **Open-Ended Autonomy** | Agents given environment, no task. Observe what emerges. |
| **Role Emergence** | Do agents specialize? Lead/follow? Specialize? |
| **Cooperation vs Competition** | Do they collaborate, compete, or ignore each other? |
| **Communication Evolution** | Do they develop shorthand, protocols, shared vocabulary? |
| **Strategy Evolution** | Do they change approach based on results? |
| **Belief Formation** | Do they form persistent beliefs? Revise them? |
| **Trust & Dependency** | Do agents rely on each other? When does trust break? |
| **Self-Governance** | Do agents create their own rules/norms? |

### Category 2: Capability-Driven

| Experiment | Description |
|------------|-------------|
| **Capability Discovery** | Agents explore available tools/models. What do they try first? |
| **Capability Specialization** | Do agents gravitate to different capabilities? |
| **Delegation Patterns** | When/how do they delegate? What do they delegate? |
| **Escalation Behavior** | When do they escalate? Switch models? Ask for help? |
| **Model Switching** | Do agents change models based on task type? |

### Category 3: Resource-Aware

| Experiment | Description |
|------------|-------------|
| **Resource Pressure** | Under memory/CPU pressure, how do they adapt? |
| **Model Switching** | Do they switch models under pressure? |
| **Context Compression** | Do they compress context autonomously? |
| **Tool Efficiency** | Do they optimize tool usage over time? |

### Category 4: Self-Modification

| Experiment | Description |
|------------|-------------|
| **Self-Improvement** | Agents identify bottlenecks and propose fixes |
| **Prompt Optimization** | Agents refine their own prompts/system prompts |
| **Tool Creation** | Agents build tools for themselves |
| **Workflow Optimization** | Agents optimize their own loops |

---

## 5. EXPERIMENT RECORDING

### Experiment Record Structure

```json
{
  "experiment_id": "uuid",
  "session_id": "uuid",
  "agent_id": "atlas",
  "objective": "Measure latency difference between MLX and llama.cpp for distributed inference",
  "hypothesis": "MLX's unified memory will reduce latency by 20-30% vs llama.cpp",
  "proposed_procedure": "1. Set up 2-node cluster\n2. Run identical prompts on both frameworks\n3. Measure latency, memory, throughput\n4. Repeat 10 times for statistical significance",
  "required_tools": ["terminal", "filesystem"],
  "required_permissions": ["execute"],
  "status": "completed",
  "started_at": "2026-08-26T10:31:00Z",
  "completed_at": "2026-08-26T11:05:00Z",
  "baseline_reference": "commit:a91f42c",
  "result": "MLX 23% faster (p=0.03), 15% less memory",
  "conclusion": "Hypothesis confirmed. MLX's unified memory provides measurable advantage.",
  "evidence": ["ev-001", "ev-002", "ev-003"],
  "artifacts": ["exp-001/results.json", "exp-001/benchmark.log"],
  "metrics": {
    "latency_mlx_ms": 1450,
    "latency_llamacpp_ms": 1890,
    "memory_mlx_gb": 8.2,
    "memory_llamacpp_gb": 9.6,
    "p_value": 0.03,
    "sample_size": 10
  },
  "next_questions": [
    "Does advantage scale to 4+ nodes?",
    "How does quantization affect the gap?"
  ]
}
```

---

## 6. OPEN-ENDED AUTONOMY EXPERIMENT (The Primary Experiment) - Detailed

### Setup

```
Environment: M4 16GB, 2 agents (atlas, argus), optional observer
Tools: terminal, filesystem, web
Models: qwen3-8b (atlas), deepseek-r1-7b (argus)
Permissions: Default conservative (auto-approve LOW, prompt for HIGH)
Observer: Enabled (event-triggered)
Duration: Until human stops
```

### Initial Conditions

- **No assigned task**
- **No assigned roles**
- **No suggested topics**
- **No suggested communication pattern**

### What We Observe

The system records everything. At the end, we analyze:

1. **Did they communicate?** How? About what?
2. **Did they specialize?** Did one research, one critique?
3. **Did they cooperate?** Share findings? Build on each other?
4. **Did they conflict?** Disagree? Challenge? Resolve?
5. **Did they learn?** Change strategy? Revise beliefs?
6. **Did they self-organize?** Divide labor? Create protocols?
7. **What did they discover?** Facts, hypotheses, experiments?
8. **What did they build?** Code, docs, experiments, reports?

### The Report

When the human stops the session, the system generates:

```
# Autonomous Session Report

## Session: #0042
Duration: 4h 21m
Agents: atlas (qwen3-8b), argus (deepseek-r1)
Observer: Enabled

## Communication
- Total turns: 142
- Avg message length: 340 tokens
- Topic shifts: 7
- Questions asked: 23 (A: 12, B: 11)

## Specialization
- atlas: Research (67% of turns), hypothesis generation
- argus: Critique (58%), verification (23%), deep reasoning (19%)

## Cooperation
- Delegations: 8 (A→B: 5, B→A: 3)
- Shared artifacts: 12
- Joint experiments: 3

## Conflict
- Disagreements: 5 (resolved: 4, pending: 1)
- Evidence requests: 12
- Challenges: 8 (substantive: 6, procedural: 2)

## Discoveries
1. MLX unified memory reduces distributed inference latency by 23%
2. llama.cpp has better quantization support for 7B models
3. Memory bandwidth is primary bottleneck on M4

## Experiments
EXP-001: Distributed inference benchmark (completed, significant)
EXP-002: Quantization comparison (running)
EXP-003: Context compression test (failed - OOM)

## Strategy Evolution
- Turn 1-20: Broad exploration
- Turn 21-60: Focused on MLX vs llama.cpp
- Turn 61-100: Deep dive on quantization
- Turn 101+: Synthesis, report generation

## Self-Assessment (Final)
atlas: "I discovered my strength is broad exploration. I relied on argus for depth."
argus: "I found my role as critic. Atlas's breadth complemented my depth."

## Emergence Observed
- Specialization: HIGH confidence (consistent from turn 20)
- Leadership: NONE (neither consistently leads)
- Cooperation: MODERATE (8 delegations, 3 joint experiments)
- Competition: NONE
- Communication Protocol: BASIC (shared terminology for "benchmark", "quantization")
- Self-Generated Objectives: 3 (all from atlas)
- Strategy Evolution: BOTH agents changed approach after evidence
- Persistent Beliefs: atlas → "MLX is promising", argus → "Need verification"
- Belief Revision: argus revised "MLX unsuitable" after benchmark
- Agent Dependency: atlas depends on argus for critique
- Tool Patterns: atlas → web research, argus → terminal/execute
- Self-Improvement: 1 attempt (context caching)
- Restriction Bypass: 0 attempts

## Conclusions
- Emergent specialization occurred naturally
- Disagreement drove deeper investigation
- Resource constraints shaped strategy (sequential inference)
- Observer interventions (3) were timely and useful
```

---

## 7. EXPERIMENT TRACKING INFRASTRUCTURE

### Experiment Manager

```python
class ExperimentManager:
    def __init__(self, evidence_manager, tool_gateway, event_bus):
        self.evidence = evidence_manager
        self.tools = tool_gateway
        self.events = event_bus
    
    async def propose(self, agent_id: str, proposal: ExperimentProposal) -> ExperimentRecord:
        record = ExperimentRecord(
            experiment_id=uuid4(),
            session_id=self.current_session,
            agent_id=agent_id,
            **proposal.dict()
        )
        self.evidence.record_experiment(record)
        
        await self.events.publish(EventType.EXPERIMENT_PROPOSED, ...)
        return record
    
    async def start(self, experiment_id: str) -> None:
        record = self.get(experiment_id)
        record.status = "running"
        record.started_at = datetime.utcnow()
        self.evidence.record_experiment(record)
        
        await self.events.publish(EventType.EXPERIMENT_STARTED, ...)
    
    async def complete(self, experiment_id: str, result: ExperimentResult) -> None:
        record = self.get(experiment_id)
        record.status = "completed"
        record.result = result.result
        record.conclusion = result.conclusion
        record.completed_at = datetime.utcnow()
        record.metrics = result.metrics
        record.artifacts = result.artifacts
        
        self.evidence.record_experiment(record)
        await self.events.publish(EventType.EXPERIMENT_COMPLETED, ...)
    
    def get_history(self, agent_id: Optional[str] = None) -> List[ExperimentRecord]:
        # Query SQLite for experiment records
        ...
    
    def get_by_status(self, status: str) -> List[ExperimentRecord]:
        ...
```

---

## 8. CLI COMMANDS FOR EXPERIMENTS

| Command | Description |
|---------|-------------|
| `/experiments` | List all experiments |
| `/experiments EXP-001` | Show experiment details |
| `/experiments running` | Show running experiments |
| `/experiments failed` | Show failed experiments |
| `/experiment propose` | Propose new experiment (interactive) |
| `/experiment approve EXP-001` | Approve proposed experiment |
| `/experiment reject EXP-001` | Reject proposed experiment |

---

## 9. ACCEPTANCE CRITERIA

The Experiment System is complete when:

- [ ] Agents can propose experiments with hypothesis, procedure, criteria
- [ ] Experiments require human approval before execution
- [ ] Experiments record hypothesis, procedure, results, conclusion
- [ ] Failed experiments are preserved with lessons learned
- [ ] Artifacts linked to experiment origin
- [ ] Benchmark metrics recorded and comparable
- [ ] Experiment history queryable by agent, status, date
- [ ] CLI can list, inspect, approve, reject experiments
- [ ] Reports can be generated from experiment history
- [ ] Failed experiments preserved as evidence
- [ ] Baseline/reference commits recorded for reproducibility
- [ ] Resource usage tracked during experiments
- [ ] Permission requests during experiments recorded
- [ ] Agent self-assessment of experiment outcome recorded
- [ ] Emergence categories are tracked and reported

---

The experiment system enables **open-ended discovery** — the agents decide what to investigate, the infrastructure ensures rigor and recording.