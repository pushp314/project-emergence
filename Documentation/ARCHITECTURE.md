# Autonomous AI Sandbox — Engineering Specification

## 1. CORE OBJECTIVE

> **Build a local autonomous multi-agent sandbox on an M4 Mac with 16 GB RAM. Two autonomous agents can converse indefinitely, explore the environment, use tools, request permissions from the human, and learn from the conversation. The system observes and documents the emergence of their behaviors. The system must aggressively manage CPU/RAM/thermal load so the Mac remains responsive.**

---

## 2. SYSTEM OVERVIEW

```text
                          HUMAN
                     ┌──────┴──────┐
                     │             │
                  Listen        Interrupt
                     │             │
                     └──────┬──────┘
                            ↓
                 ┌─────────────────────┐
                 │   CONTROL PLANE      │
                 │ Conversation Engine  │
                 │ Scheduler            │
                 │ Permission Gateway   │
                 │ Resource Manager     │
                 └──────────┬──────────┘
                            │
                     EVENT / MESSAGE BUS
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
       ┌────────┐       ┌────────┐       ┌────────┐
       │ Atlas  │ ←───→  │ Argus  │ ←───→  │Observer│
       │(Agent) │        │(Agent) │        │(Agent) │
       └────┬───┘       └────┬───┘       └────┬───┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                      TOOL GATEWAY
                             │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
     Terminal             Filesystem             Web
         │                    │                    │
         └────────────────────┼────────────────────┘
                             ▼
                            macOS

                  ┌──────────────────┐
                  │  MODEL RUNTIME   │
                  │  Ollama / Adapter│
                  └──────────────────┘

                  ┌──────────────────┐
                  │  MEMORY SYSTEM   │
                  │  State + Summary │
                  └──────────────────┘

                  ┌──────────────────┐
                  │  EVIDENCE PLANE  │
                  │ Intent + Action  │
                  └──────────────────┘
```

---

## 3. FIVE PLANES

### Control Plane
Responsible for:
- Starting/stopping agents
- Scheduling turns
- Handling interruptions
- Permission requests
- Resource management
- Graceful shutdown

### Agent Plane
Contains autonomous agents:
- **Atlas** — Autonomous agent (identity: `atlas`)
- **Argus** — Autonomous agent (identity: `argus`)  
- **Observer** — Optional monitoring agent (identity: `observer`)

**Agents do NOT have fixed roles.** Their roles, objectives, and strategies emerge from interaction.

Agents should **not control infrastructure directly**.

### Tool Plane
Provides capabilities:
- Terminal
- Filesystem
- Browser/Web search
- Code execution
- Future tools

### Memory Plane
Stores:
- Conversation history
- Summaries
- Important discoveries
- Pending questions
- Agent state
- Permission history

### Model Plane
Abstracts the actual LLM:
```
Agent
  ↓
Capability Request
  ↓
Capability Registry
  ↓
Model Adapter
  ↓
Ollama / Local LLM
```

Changing models requires **zero changes to agent architecture**.

### Evidence Plane
Independently records all events with **intent + action** distinction.
See [EVIDENCE_SYSTEM.md](EVIDENCE_SYSTEM.md).

---

## 4. AGENT DESIGN — AUTONOMOUS AGENTS

Agents are **autonomous reasoning processes** with:

- **Identity** — Stable identifier (`atlas`, `argus`, `observer`)
- **Memory** — Access to conversation history, summaries, discoveries
- **Capabilities** — Tools, models, delegations via Capability Registry
- **Permissions** — Request via Permission Gateway
- **Resources** — Constrained by Resource Manager
- **Communication** — Event Bus (no direct calls)
- **Self-Determination** — Decide what to do, when, how

### Agent Decision Loop

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

Agents **decide WHAT they need**. Infrastructure decides **WHETHER** and **HOW**.

---

## 4. EVENT-DRIVEN COMMUNICATION

Agents communicate **only** through the Event Bus.

### Event Structure
```json
{
  "event_id": "uuid",
  "type": "agent.message",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "content": "I want to research distributed inference.",
  "timestamp": "2026-08-26T10:30:00Z",
  "metadata": {
    "intent": "research distributed inference",
    "model": "qwen2.5-coder-7b",
    "tokens": 120
  }
}
```

### Key Event Types
| Category | Events |
|----------|--------|
| Agent | `agent.message`, `agent.thinking_started`, `agent.response_completed`, `agent.delegation`, `agent.delegation.response`, `agent.self_assessment`, `agent.role_change`, `agent.disagreement` |
| Human | `human.message`, `human.interrupt` |
| Tool | `tool.request`, `tool.started`, `tool.completed`, `tool.failed` |
| Browser | `browser.search`, `browser.page_opened`, `browser.content_extracted` |
| Permission | `permission.requested`, `permission.approved`, `permission.denied` |
| Memory | `memory.updated` |
| Experiment | `experiment.started`, `experiment.completed`, `experiment.failed` |
| Evidence | `evidence.created`, `emergence.observed` |
| Observer | `observer.intervention` |
| Resource | `resource.warning`, `resource.critical` |
| System | `system.pause`, `system.resume`, `system.stop` |

---

## 5. CONVERSATION ALGORITHM

State machine (not infinite loop):

```
IDLE
  ↓
THINKING
  ↓
GENERATING
  ↓
SPEAKING
  ↓
OBSERVING
  ↓
NEXT_TURN
  ↓
THINKING
```

Interrupts at any state:
```
ANY STATE
   ↓
HUMAN_INTERRUPT
   ↓
PAUSED
   ↓
PROCESS_HUMAN_INPUT
   ↓
RESUME
```

And:
```
ANY STATE
   ↓
STOP
   ↓
GRACEFUL_SHUTDOWN
```

---

## 6. TURN SCHEDULING

Default: **RoundRobin** (A → B → A → B...)

Configurable policies:
- `RoundRobin` — Strict alternation
- `Adaptive` — Balance based on participation
- `Debate` — Challenger gets extra turns
- `Research` — Explorer gets more turns
- `HumanPriority` — Human input gets priority
- `ObserverTriggered` — Observer decides next speaker

For V1: **RoundRobin**.

---

## 7. INFINITE CONVERSATION ≠ INFINITE CONTEXT

**Never** send entire conversation to LLM.

```
MEMORY
   │
   ├────────────┼────────────┐
   ▼            ▼            ▼
Recent turns  Summary    Important facts
   │            │            │
   └────────────┼────────────┘
                ▼
         Context Builder
                ▼
               LLM
```

- **Short-term**: Last 6-12 exchanges
- **Long-term**: Compressed summaries
- **Knowledge**: Important facts/discoveries
- **Open questions**: Unresolved items

---

## 8. MEMORY COMPRESSION

Every N turns:
```
Conversation buffer
       ↓
Memory Summarizer (LLM)
       ↓
Extract: facts, ideas, decisions, questions, topic
       ↓
Persistent Memory
```

Do NOT summarize every turn — wastes compute.

---

## 9. HUMAN PERMISSION ARCHITECTURE

Agents can **request any capability**, but consequential actions go through Permission Gateway.

### Permission Levels
```
READ → WRITE → EXECUTE → NETWORK → INSTALL → SYSTEM
```

### Request Flow
```
Agent Decision
      ↓
Capability Request
      ↓
Permission Gate
      ↓
┌─────┴──────┐
▼            ▼
Allowed   Approval Required
  ↓            ↓
Execute    Human → Decision
```

Human approval required for HIGH/CRITICAL risk and INSTALL/SYSTEM scope.

---

## 10. CREDENTIALS — SECRET BROKER

Never expose raw credentials to LLMs.

```
Agent
  ↓
Tool
  ↓
Secret Manager
  ↓
External service
```

Model only knows: **"Credential available."** Never the credential itself.

---

## 11. TOOL ARCHITECTURE

Every tool:
```
Tool
├── name
├── description
├── input schema (JSON Schema)
├── permission requirement
├── risk level
└── execute()
```

Tool Gateway enforces:
1. Permission check before execution
2. Structured input validation
3. Structured output
4. Logging + evidence generation
5. Error handling
5. Resource accounting

---

## 12. MACOS RESOURCE MANAGEMENT

**M4 16 GB is the primary constraint.**

### Cooperative Scheduling
```
Agent A
  ↓
generation
  ↓
TTS
  ↓
Agent B
  ↓
generation
  ↓
TTS
```
Observer: event-triggered, not continuous.

### Resource Manager
Monitors: RAM, CPU, GPU, latency, thermal, model memory, queue depth.

Adjusts:
```
NORMAL        → full response length
HIGH MEMORY   → shorter context, smaller output
HIGH LOAD     → pause Observer, reduce frequency
CRITICAL      → pause conversation, notify human
```

---

## 13. MODEL ROUTING

Agents request **capabilities**, not models.

```
Simple task      → small/fast model
Complex reasoning→ stronger model
Observer         → small model
Memory summary   → small model
Main conversation→ best available model
```

Capability Registry maps capability → model.

---

## 14. GENERATION OPTIMIZATION (M4)

- Quantized GGUF/Metal-compatible models
- Moderate context (4096)
- Bounded output (1024 tokens)
- Streaming generation
- Sequential inference (one model at a time)
- Prompt caching where supported
- Avoid unnecessary regeneration
- Model reuse (don't reload)

**Don't chase max context.** Large context = more memory + compute.

---

## 15. TTS OPTIMIZATION

```
LLM response
  ↓
stream text
  ↓
sentence chunker
  ↓
TTS
  ↓
audio
```

Don't wait for full response. Speak as generated.

---

## 16. HUMAN INTERRUPTION

```
Microphone
  ↓
Voice Activity Detection
  ↓
STT
  ↓
Interrupt event
```

Lightweight local STT. Not a huge model.

---

## 17. EVENT TYPES (Complete Registry)

```
agent.message          agent.started          agent.completed
agent.error            human.message          human.interrupt
agent.delegation       agent.delegation.response
agent.self_assessment  agent.role_change      agent.disagreement
tool.request           tool.started           tool.completed
tool.failed            permission.request     permission.approved
permission.denied      memory.updated         observer.intervention
emergence.observed     resource.warning       resource.critical
system.pause           system.resume          system.stop
experiment.started     experiment.completed   experiment.failed
evidence.created       browser.search         browser.page_opened
browser.content_extracted
```

---

## 18. OBSERVABILITY

Dashboard shows:
```
SYSTEM
RAM: 11.2 GB / 16 GB
CPU: 68%
Gen: 14 tok/s
Temp: normal
Model: Agent A

CONVERSATION
Turn: 142
Topic: Distributed AI
Duration: 47 min

AGENTS
A: generating
B: waiting
C: sleeping

TOOLS
Terminal: 2 calls
Web: 7 calls

PERMISSIONS
Pending: 1

EMERGENCE
Specialization: detected
Cooperation: 3 delegations
Disagreements: 2
```

---

## 19. PERSISTENCE

```
SQLite → structured state (sessions, events, evidence, research, experiments)
Filesystem → large artifacts (audio, reports, research, snapshots)
Git/GitHub → source code + engineering history
```

**SQLite + local filesystem = V1.** No PostgreSQL/Redis.

### Recovery
```
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

## 20. SECURITY MODEL

**Privileged autonomous application.**

Every tool invocation logged:
```
TIME | AGENT | TOOL | ARGUMENTS | PERMISSION | RESULT
```

Dangerous commands → show exact command before execution.

Agent **never** silently escalates permissions.

---

## 21. TECHNOLOGY STACK

- **Language:** Python 3.11+
- **LLM:** Ollama (local)
- **API:** Ollama HTTP API
- **Database:** SQLite (WAL mode)
- **Event Bus:** asyncio queues
- **STT:** faster-whisper (local)
- **TTS:** pyttsx3 / edge-tts (local)
- **Frontend:** Rich CLI (Click + Rich)
- **Web:** aiohttp + BeautifulSoup
- **Config:** .env + YAML
- **Logging:** Structured JSONL

**No:** Kafka, Redis, Kubernetes, Docker, microservices, PostgreSQL, vector DBs.

---

## 22. PROJECT STRUCTURE

```
ai-sandbox/
├── app/
│   ├── main.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── explorer.py
│   │   ├── challenger.py
│   │   └── observer.py
│   ├── orchestration/
│   │   ├── conversation.py
│   │   ├── scheduler.py
│   │   └── state_machine.py
│   ├── models/
│   │   ├── base.py
│   │   └── ollama.py
│   ├── memory/
│   │   ├── manager.py
│   │   ├── summarizer.py
│   │   └── store.py
│   ├── tools/
│   │   ├── gateway.py
│   │   ├── terminal.py
│   │   ├── filesystem.py
│   │   └── web.py
│   ├── permissions/
│   │   └── manager.py
│   ├── audio/
│   │   ├── stt.py
│   │   └── tts.py
│   ├── resources/
│   │   └── monitor.py
│   ├── autonomy/
│   │   └── environment.py
│   ├── evidence/
│   │   ├── schemas.py
│   │   └── manager.py
│   ├── sessions/
│   │   └── manager.py
│   ├── research/
│   │   └── manager.py
│   ├── decision/
│   │   └── manager.py
│   ├── artifacts/
│   │   └── manager.py
│   ├── self_modification/
│   │   └── engine.py
│   ├── capabilities/
│   │   └── registry.py
│   ├── db/
│   │   └── migrations.py
│   ├── events/
│   │   ├── bus.py
│   │   └── schemas.py
│   ├── reports/
│   │   └── generator.py
│   ├── a2a/
│   │   └── protocol.py
│   └── logging_config.py
├── tests/
├── data/
├── logs/
├── config/
├── .env.example
├── README.md
└── ARCHITECTURE.md
```

---

## 23. DEVELOPMENT PHASES

### Phase 1 — Foundation
- Event Bus, schemas
- Ollama adapter, model abstraction
- Base agent, A2A messages

### Phase 2 — Model Runtime
- Continuous A/B conversation
- Streaming generation

### Phase 3 — Control + CLI
- Control plane, interruption, pause/resume
- CLI (start, watch, interactive)

### Phase 4 — Persistence
- SQLite, migrations, sessions, events, messages, checkpoints

### Phase 5 — Memory + Evidence
- Memory, evidence plane, provenance, research journal

### Phase 6 — Tools
- Terminal, filesystem, browser, permission gateway

### Phase 7 — Resources
- RAM monitoring, inference metrics, scheduling, model routing

### Phase 8 — Voice
- STT, TTS, interruption

### Phase 9 — Experiments
- Experiment system, benchmarks, artifacts

### Phase 10 — Git/GitHub
- Branch workflow, automated checks, issue/PR integration

### Phase 11 — Self-Modification
- Proposals, isolated worktrees, tests, benchmarks, approval, rollback

### Phase 12 — Advanced A2A
- Protocol, agent discovery, scalable routing

---

## 24. DEFINITION OF DONE

V1 complete when:

- [ ] Agents communicate indefinitely via event bus
- [ ] Conversation survives hundreds of turns
- [ ] User can interrupt speech
- [ ] User can stop/resume system
- [ ] Memory doesn't grow indefinitely (summarization)
- [ ] Agent failures don't crash application
- [ ] Model backend replaceable (Ollama → other)
- [ ] Tool layer isolated (gateway pattern)
- [ ] Permissions work (request/approve/deny)
- [ ] Every tool action logged
- [ ] Resource manager detects high load
- [ ] Observer doesn't consume unnecessary inference
- [ ] Mac remains usable during normal operation
- [ ] Graceful shutdown (SIGINT/SIGTERM)
- [ ] Tests cover failures and interruptions
- [ ] Agents demonstrate emergent behavior (specialization, cooperation, etc.)
- [ ] System records intent + action for every meaningful event
- [ ] Agents can self-determine objectives and strategies
- [ ] Emergent behaviors are observed and recorded

---

The architecture enables **maximum agent autonomy** within **minimum necessary system constraints**. The system observes emergence rather than prescribing it.