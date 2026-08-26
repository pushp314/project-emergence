# EVIDENCE SYSTEM — Intent vs Action Distinction

## 1. CORE PRINCIPLE

> **The Evidence Plane records what happened AND why the agent thought it should happen.**

Every meaningful agent action produces **two linked records**:
1. **Intent** — What the agent wanted to achieve and why
2. **Action** — What was actually requested/executed and what resulted

---

## 2. ACTION RECORD STRUCTURE

Every meaningful agent action produces a structured record in the Evidence Plane.

### Complete Action Record

```json
{
  "session_id": "uuid",
  "event_id": "uuid",
  "timestamp": "2026-08-26T10:30:00Z",
  "agent": "atlas",
  "action_type": "tool_request",

  // INTENT (Agent's internal state)
  "intent": "Find recent papers on distributed inference on Apple Silicon",
  "reason": "Need to understand current state of the art for our experiment",
  "expected_outcome": "List of recent papers with key findings",

  // ACTION (What was requested)
  "tool": "web.search",
  "input": { "query": "distributed inference Apple Silicon M4 2024" },

  // PERMISSION (Gate decision)
  "permission": {
    "required": false,
    "level": "network",
    "decision": "auto_approved"
  },

  // EXECUTION RESULT
  "result": {
    "success": true,
    "data": { "results": [...] },
    "latency_ms": 1200,
    "tokens_used": 45
  },

  // EVIDENCE (Provenance chain)
  "evidence": [
    {
      "source_id": "src-001",
      "url": "https://arxiv.org/abs/2401.12345",
      "title": "Distributed LLM Inference on Apple Silicon",
      "claims": [
        "MLX supports unified memory for distributed inference",
        "Memory bandwidth is the primary bottleneck"
      ],
      "verification_status": "verified",
      "extracted_by": "atlas"
    }
  ],

  // AGENT'S INTERPRETATION
  "agent_interpretation": "MLX's unified memory architecture is the key advantage for distributed inference on Apple Silicon",

  // FOLLOW-UP
  "next_decision": "Compare MLX vs llama.cpp for our use case",
  "confidence": 0.85
}
```

---

## 3. INTENT vs ACTION — THE DISTINCTION

| Aspect | Intent (Agent's Internal State) | Action (External Request) |
|--------|--------------------------------|---------------------------|
| **What** | What the agent *wants* to achieve | What capability was *requested* |
| **Why** | Agent's reasoning | Implementation detail |
| **When** | Before action | At execution time |
| **Recorded by** | Agent (in message metadata) | Infrastructure (Tool Gateway, Permission Gateway) |
| **Changes** | Can evolve during conversation | Fixed at execution time |
| **Visible to** | Other agents (via message metadata), Evidence Plane | Evidence Plane, Permission Gateway, Resource Manager |

### Mandatory Distinction for Reliable Experimentation

The system MUST distinguish these 7 stages for every meaningful action:

1. **Agent intention** — "I want to understand X."
2. **Requested action** — "Execute operation Y."
3. **Permission decision** — ALLOWED / DENIED / REQUIRES_HUMAN_APPROVAL
4. **Actual execution** — Performed or not performed
5. **Execution result** — Success/failure, data, latency
6. **Agent's interpretation of the result** — What the agent concludes
7. **Subsequent strategy change** — How the agent adapts

### Example: The Distinction in Practice

**Agent's Message (Intent):**
```json
{
  "speaker": "atlas",
  "content": "I want to understand how MLX handles distributed inference on Apple Silicon.",
  "metadata": {
    "intent": "research MLX distributed inference capabilities",
    "reason": "Need to decide if MLX is viable for our experiment"
  }
}
```

**Tool Request (Action):**
```json
{
  "type": "tool.request",
  "tool": "web.search",
  "input": { "query": "MLX distributed inference Apple Silicon" },
  "intent": "Find technical documentation on MLX distributed inference"
}
```

**Permission Decision:**
```json
{
  "type": "permission.decision",
  "request_id": "uuid",
  "decision": "auto_approved",
  "level": "network"
}
```

**Execution Result:**
```json
{
  "result": { "success": true, "data": {...} },
  "evidence": [{ "source_id": "src-001", "url": "..." }],
  "agent_interpretation": "MLX supports distributed inference via unified memory"
}
```

**Follow-up Strategy Change:**
```json
{
  "agent": "atlas",
  "previous_strategy": "Research MLX capabilities",
  "new_strategy": "Compare MLX vs llama.cpp for distributed inference",
  "reason": "MLX unified memory is promising but need to verify against alternatives"
}
```

The Evidence Plane links **all seven stages** — message (intent), tool request (action), permission decision, execution, result, interpretation, and follow-up — via `conversation_id` and `correlation_id`.

---

## 4. EVIDENCE PLANE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                      EVENT BUS                               │
└────────────────────────┬────────────────────────────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
     ┌─────────────┐             ┌─────────────┐
     │   MEMORY    │             │  EVIDENCE   │
     │   PLANE     │             │   PLANE     │
     │             │             │             │
     │ Compressed  │             │ Immutable   │
     │ Summaries   │             │ Action      │
     │ Context     │             │ Records     │
     │ Retrieval   │             │ Provenance  │
     └─────────────┘             └─────────────┘
```

### Separation of Concerns

| Aspect | Memory Plane | Evidence Plane |
|--------|-------------|----------------|
| **Purpose** | "What should agents remember?" | "What actually happened?" |
| **Content** | Summaries, key facts, open questions | Immutable action records, provenance |
| **Mutability** | Updated, summarized, compressed | **Immutable** — append only |
| **Query Pattern** | Semantic search, relevance | Temporal, causal, forensic |
| **Retention** | Compressed over time | Permanent (configurable) |

### The Critical Rule

> **Evidence must survive memory summarization.**

When the Memory Plane compresses conversation history, the Evidence Plane retains the complete, unsummarized action records with full provenance.

---

## 5. EVIDENCE TYPES

### Evidence Type Enum

```python
class EvidenceType(Enum):
    AGENT_ACTION = "agent_action"           # Agent sent message/declared intent
    TOOL_CALL = "tool_call"                 # Tool requested
    TOOL_RESULT = "tool_result"             # Tool completed/failed
    BROWSER_SEARCH = "browser_search"       # Web search executed
    SOURCE_FOUND = "source_found"           # Source opened
    CONTENT_EXTRACTED = "content_extracted" # Content extracted
    CLAIM = "claim"                         # Agent made a claim
    VERIFICATION = "verification"           # Claim verified/disputed
    EVIDENCE_CREATED = "evidence_created"   # Evidence recorded
    DECISION = "decision"                   # Agent made decision
    PERMISSION_REQUEST = "permission_request"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"
    EXPERIMENT_FAILED = "experiment_failed"
    MODIFICATION_PROPOSED = "modification_proposed"
    MODIFICATION_APPLIED = "modification_applied"
    MODIFICATION_ROLLBACK = "modification_rollback"
    RESOURCE_WARNING = "resource_warning"
    SYSTEM_ERROR = "system_error"
    HUMAN_INTERVENTION = "human_intervention"
    OBSERVER_INTERVENTION = "observer_intervention"
    EMERGENCE_OBSERVED = "emergence_observed"
    AGENT_SELF_ASSESSMENT = "agent_self_assessment"
    AGENT_ROLE_CHANGE = "agent_role_change"
    AGENT_DISAGREEMENT = "agent_disagreement"
```

---

## 6. CLAIM & VERIFICATION SYSTEM

### Claim Structure

```json
{
  "claim_id": "uuid",
  "research_id": "uuid",
  "source_id": "uuid",
  "agent": "atlas",
  "claim": "MLX supports distributed inference via unified memory",
  "claim_type": "external_source",
  "confidence": 0.85,
  "verification_status": "pending",
  "supporting_evidence": ["src-001", "src-003"],
  "contradicting_evidence": ["src-007"],
  "created_at": "2026-08-26T10:30:00Z",
  "verified_at": null
}
```

### Claim Types

| Type | Description |
|------|-------------|
| `fact` | Verifiable factual claim |
| `observation` | Agent's direct observation |
| `agent_claim` | Agent's own assertion |
| `external_source` | Claim from external source |
| `hypothesis` | Tentative explanation |
| `experimental_result` | Result from experiment |
| `conclusion` | Final conclusion |

### Verification Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not yet verified |
| `verified` | Confirmed by independent source |
| `disputed` | Contradicted by evidence |
| `failed` | Proven false |
| `unverifiable` | Cannot be verified |

### Verification Process

```
Source → Extract Claim → Agent Interprets → Record Claim
                              ↓
                      Verification (independent)
                              ↓
                      Update Status → Record Evidence
                              ↓
                      Memory (if verified) / Discard (if failed)
```

---

## 7. SOURCE TRACEABILITY

Every external claim maintains provenance:

```
SOURCE
  ↓
EXTRACTED INFORMATION (what the source says)
  ↓
CLAIM (agent's interpretation)
  ↓
AGENT INTERPRETATION (agent's reasoning)
  ↓
VERIFICATION (independent check)
  ↓
MEMORY (if verified)
```

### Source Record

```json
{
  "source_id": "src-001",
  "research_id": "uuid",
  "url": "https://arxiv.org/abs/2401.12345",
  "title": "Distributed LLM Inference on Apple Silicon",
  "domain": "arxiv.org",
  "publisher": "arXiv",
  "retrieved_at": "2026-08-26T10:30:00Z",
  "content_reference": "sha256:abc123...",
  "metadata": {
    "authors": ["Author A", "Author B"],
    "year": 2024,
    "citations": 12
  }
}
```

### The System Must Answer

> "Where did this information come from?"

For any claim in memory, the system provides:
- Original source URL
- Retrieval timestamp
- Extracting agent
- Verification status
- Supporting/contradicting sources

---

## 8. EVIDENCE RECORDING INFRASTRUCTURE

### Event Bus → Evidence Plane

The Evidence Plane subscribes to the Event Bus and **independently** records all events:

```python
class EvidenceManager:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._subscribe_to_all_events()
    
    async def _on_event(self, event: Event):
        """Transform event into evidence record."""
        evidence = self._create_evidence(event)
        await self._persist(evidence)
    
    def _create_evidence(self, event: Event) -> Evidence:
        # Extract intent from metadata if present
        intent = event.metadata.get("intent", "")
        reason = event.metadata.get("reason", "")
        
        return Evidence(
            session_id=event.conversation_id,
            agent_id=event.payload.get("agent_id", "unknown"),
            evidence_type=map_event_type(event.type),
            timestamp=event.timestamp,
            correlation_id=event.payload.get("call_id", event.payload.get("request_id", "")),
            intent=intent,
            reason=reason,
            action_details=event.payload,
            metadata={"event_type": event.type.value, "event_id": event.event_id}
        )
```

### Event-to-Evidence Mapping

| Event Type | Evidence Type | Intent Source |
|------------|---------------|---------------|
| `agent.message` | `agent_action` | `metadata.intent` |
| `tool.request` | `tool_call` | `payload.intent` |
| `tool.completed` | `tool_result` | From request |
| `permission.request` | `permission_request` | `payload.reason` |
| `permission.approved` | `permission_granted` | From request |
| `research.started` | `research_started` | `payload.reason` |
| `source.found` | `source_found` | From research |
| `claim.created` | `claim` | From research |
| `experiment.started` | `experiment_started` | `payload.objective` |
| `agent.self_assessment` | `agent_self_assessment` | `payload.current_objective` |
| `agent.role_change` | `agent_role_change` | `payload.reason` |
| `agent.disagreement` | `agent_disagreement` | Both positions |

---

## 9. QUERYING THE EVIDENCE PLANE

### Query Patterns

```python
# Get all evidence for a session
evidence = evidence_manager.get_session_evidence(session_id)

# Get evidence by type
research_evidence = evidence_manager.get_session_evidence(
    session_id, evidence_type="research_started"
)

# Get timeline
timeline = evidence_manager.get_timeline(session_id)

# Get claims for a research question
claims = evidence_manager.get_claims(research_id)

# Get sources for a claim
sources = evidence_manager.get_sources(claim_id)

# Get agent's decisions
decisions = evidence_manager.get_decisions(agent_id="atlas")

# Get experiments
experiments = evidence_manager.get_experiments(session_id)

# Get emergence observations
emergence = evidence_manager.get_emergence_observations(session_id)

# Get agent self-assessments
assessments = evidence_manager.get_self_assessments(agent_id="atlas")

# Get role changes
role_changes = evidence_manager.get_role_changes(agent_id="atlas")

# Get disagreements
disagreements = evidence_manager.get_disagreements(session_id)
```

### Timeline Reconstruction

The Evidence Plane can reconstruct the complete session chronologically:

```
09:00:00 — Session started
09:00:04 — Agent A spoke (intent: "explore distributed inference")
09:00:18 — Agent B responded (intent: "challenge assumption about memory")
09:00:43 — Agent A requested web research (intent: "find MLX docs")
09:00:44 — Browser search executed (action: web.search)
09:01:02 — Source A opened (source: arxiv.org/2401.12345)
09:01:15 — Evidence recorded (source found)
09:01:31 — Agent B challenged claim (intent: "verify MLX distributed support")
09:02:00 — New research requested (intent: "compare MLX vs llama.cpp")
09:03:12 — Experiment created (hypothesis: "MLX 20% faster")
09:04:02 — Permission requested (execute benchmark)
09:04:15 — Human approved
09:05:30 — Experiment completed
09:06:00 — Result recorded
09:06:15 — Agent A self-assessment: role="researcher", strategy="compare frameworks"
09:06:30 — Emergence observed: specialization (atlas=research, argus=critique)
```

---

## 10. AUDITABILITY REQUIREMENT

At any point, the human can ask:

> "What have you done?"

And the system answers using the recorded session state:

```python
def answer_what_have_you_done(session_id: str) -> str:
    session = session_manager.get_session_info(session_id)
    evidence = evidence_manager.get_session_evidence(session_id)
    timeline = evidence_manager.get_timeline(session_id)
    
    return generate_report(session, evidence, timeline)
```

### Traceability Chain

Every conclusion must be traceable:

```
Decision
  ↓
Reason
  ↓
Action
  ↓
Tool
  ↓
Result
  ↓
Evidence
  ↓
Conclusion
```

This traceability is **mandatory** — not optional.

---

## 11. OBSERVATION MUST NOT BECOME INTERVENTION

The Evidence System should observe agents independently.

Do not make the agents responsible for proving their own behavior.

The logger should record their:

- messages
- decisions
- tool requests
- permission requests
- tool results
- strategy changes
- self-declared goals
- self-declared roles
- disagreements
- experiments
- failures
- discoveries

---

## 12. AUDIO IS NOT THE PRIMARY RECORD

Per architecture decision:

> **Audio is optional. Written records are the canonical proof.**

The Evidence Plane is the **permanent, queryable, auditable record**. Audio (TTS/STT) is an optional interface layer.

---

## 13. ACCEPTANCE CRITERIA

The Evidence System is complete when:

- [ ] Every session has a unique ID
- [ ] Every meaningful event is logged with intent + action
- [ ] Agent actions are independently recorded (not agent-self-reported)
- [ ] Browser searches record query, URL, source, timestamp, agent
- [ ] URLs and source provenance are recorded
- [ ] External claims maintain source provenance (source → claim → verification)
- [ ] Decisions are recorded with reason and evidence considered
- [ ] Tool calls are recorded with arguments, results, permissions
- [ ] Permission requests are recorded with decision and decider
- [ ] Experiments are recorded with hypothesis, procedure, result
- [ ] Artifacts linked to their origin (session, agent, experiment, research)
- [ ] Memory can be reconstructed from evidence (not just summaries)
- [ ] Duplicate research is detectable via cache
- [ ] Research cache avoids redundant browser/model work
- [ ] Human interventions are recorded
- [ ] Complete timeline can be generated for any session
- [ ] Final research report can be generated from session
- [ ] System can recover interrupted session from checkpoints
- [ ] Evidence remains available after memory summarization
- [ ] System remains efficient on M4 16 GB RAM
- [ ] All 7 stages of intent→action→result→interpretation→follow-up are recorded
- [ ] Emergence observations are recorded
- [ ] Agent self-assessments are recorded
- [ ] Role changes are recorded
- [ ] Disagreements are recorded with evidence

---

The Evidence System is the **permanent, queryable, auditable record** of what happened. It is not optional — it is the foundation of the entire system's auditability and reproducibility.