# Implementation Status Matrix

## Requirements Coverage: Documentation vs Code Implementation

### Legend
- [COMPLETE] Fully implemented in code
- [PARTIAL] Implemented but missing features/gaps
- [MISSING] Not yet implemented
- [NEEDS_CHANGE] Requires code changes to align with documentation

---

## 1. Agent Autonomy & Roles

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Agents have emergent (not fixed) roles | ARCHITECTURE.md §2.1 | PARTIAL | Remove AgentRole enum from schemas.py; replace role prescriptions in system prompts |
| Agent Atlas: emergent explorer role | AGENT_AUTONOMY.md | COMPLETE (doc) | Code: replace system prompt |
| Agent Argus: emergent challenger role | AGENT_AUTONOMY.md | COMPLETE (doc) | Code: replace system prompt |
| Agent Observer: emergent observer role | AGENT_AUTONOMY.md | COMPLETE (doc) | Code: replace system prompt |
| Agent identity based on capability, not role | PROJECT_STATE.md | MISSING | Add identity field to AgentConfig |
| System prompts describe capabilities, not prescribe roles | ARCHITECTURE.md §3.2 | PARTIAL | Replace all three system prompts |

### Code Files to Change
- `app/events/schemas.py` - Remove AgentRole enum
- `app/agents/explorer.py` - Replace role-based system prompt
- `app/agents/challenger.py` - Replace role-based system prompt  
- `app/agents/observer.py` - Replace role-based system prompt
- `app/capabilities/registry.py` - Remove fixed role assignments from DEFAULT_AGENT_CAPABILITIES

---

## 2. Evidence System - Intent vs Action 7-Stage Distinction

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| 7-stage intent→action distinction documented | EVIDENCE_SYSTEM.md | PARTIAL | EvidenceManager records basic intent/action; 7-stage pipeline not implemented |
| Evidence records intent field | EVIDENCE_SYSTEM.md §3 | COMPLETE | Basic intent field exists |
| Evidence records action field | EVIDENCE_SYSTEM.md §3 | COMPLETE | Basic action field exists |
| 7-stage pipeline: sense→categorize→intend→plan→act→observe→learn | EVIDENCE_SYSTEM.md | MISSING | Add pipeline stages to evidence recording |
| emergence.observed event type | EVIDENCE_SYSTEM.md | MISSING | Add to EventType enum and evidence schemas |
| agent.self_assessment event type | EVIDENCE_SYSTEM.md | MISSING | Add to EventType enum and evidence schemas |
| agent.role_change event type | EVIDENCE_SYSTEM.md | MISSING | Add to EventType enum and evidence schemas |
| agent.disagreement event type | EVIDENCE_SYSTEM.md | MISSING | Add to EventType enum and evidence schemas |

### Code Files to Change
- `app/events/schemas.py` - Add new EventType entries, update AgentMessage to include intent metadata
- `app/evidence/schemas.py` - Add new EvidenceType entries for emergence events
- `app/evidence/manager.py` - Add 7-stage pipeline recording logic
- `app/events/bus.py` - Update Event dataclass to support intent metadata

---

## 3. Emergence Observation Framework

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| emergence.observed event type when agent observes novel pattern | AGENT_AUTONOMY.md | MISSING | Add event type to EventType enum |
| Recording agent self-assessments | EVIDENCE_SYSTEM.md | MISSING | Add to evidence schemas |
| Recording agent role changes | EVIDENCE_SYSTEM.md | MISSING | Add to evidence schemas |
| Recording agent disagreements | EVIDENCE_SYSTEM.md | MISSING | Add to evidence schemas |
| Observer triggers emergence events on contradiction/directionless discussion | AGENT_AUTONOMY.md | MISSING | Add emergence detection logic to observer.py |
| Emergence events include evidence_id and timestamp | AGENT_AUTONOMY.md | MISSING | Extend event schemas |

### Code Files to Change
- `app/events/schemas.py` - Add emergence.observed, agent.self_assessment, agent.role_change, agent.disagreement to EventType
- `app/evidence/schemas.py` - Add EvidenceType entries for each emergence event type
- `app/evidence/manager.py` - Add recording methods for emergence events
- `app/agents/observer.py` - Add emergence detection and event emission on contradictions/directionless discussion

---

## 4. Context Manager

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Dedicated Context Manager class | MASTER_CONTROL.md §2.3 | MISSING | Create ContextManager class |
| Context extraction from conversation history | MASTER_CONTROL.md | MISSING | Implement context extraction logic |
| Context summarization and fact tracking | MASTER_CONTROL.md | PARTIAL | MemorySummarizer exists but ContextManager needed |
| Context persistence across sessions | MASTER_CONTROL.md | MISSING | Add cross-session context persistence |
| Context-aware model selection | MASTER_CONTROL.md | MISSING | Add context-aware model routing |

### Code Files to Change
- `app/models/base.py` - Add Context dataclass if needed
- `app/memory/manager.py` - Add ContextManager class
- `app/memory/summarizer.py` - Extend summarization with context tracking
- `app/orchestration/conversation.py` - Integrate ContextManager

---

## 5. Master Control Plane

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Master authentication and command bus | MASTER_CONTROL.md §2.1 | MISSING | Create Master class with auth |
| Command bus for cross-agent commands | MASTER_CONTROL.md §2.2 | MISSING | Implement command bus |
| Intervention manager for emergency intervention | MASTER_CONTROL.md §2.4 | MISSING | Implement intervention manager |
| Emergency controller with kill-switch | MASTER_CONTROL.md §2.5 | MISSING | Implement emergency controller |
| Master oversight of all agents | MASTER_CONTROL.md | MISSING | Add Master class integrating all planes |

### Code Files to Change
- `app/master/` - Create new module with Master class
- `app/orchestration/state_machine.py` - Integrate Master oversight
- `app/orchestration/conversation.py` - Add Master references

---

## 6. Agent Autonomy Loop

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Agents self-determine objectives | AGENT_AUTONOMY.md | MISSING | Add objective-setting in agent think() |
| Agents self-determine strategies | AGENT_AUTONOMY.md | MISSING | Add strategy selection |
| Agents self-assess capabilities | AGENT_AUTONOMY.md | MISSING | Add capability assessment |
| Plan→execute→evaluate loop per turn | AGENT_AUTONOMY.md | MISSING | Implement in base.py think() |
| Agents request tools based on objectives | AGENT_AUTONOMY.md | PARTIAL | Tool requests work but not objective-driven |
| Agents request permissions based on risk assessment | AGENT_AUTONOMY.md | PARTIAL | Permission requests work but not risk-assessed |

### Code Files to Change
- `app/agents/base.py` - Add objective/strategy/capability fields to AgentContext, implement plan→execute→evaluate
- `app/agents/explorer.py` - Replace with objective-driven agent
- `app/agents/challenger.py` - Replace with objective-driven agent
- `app/agents/observer.py` - Replace with objective-driven agent

---

## 7. Tool Gateway + Browser Autonomy

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Browser autonomy integrates with Tool Gateway | BROWSER_AUTONOMY.md | MISSING | Implement browser session in Tool Gateway |
| DOM/accessibility extraction for browser | BROWSER_AUTONOMY.md | MISSING | Add to web tool |
| Research loop with browser | BROWSER_AUTONOMY.md | MISSING | Add to ResearchManager |
| Browser session management (tabs, history) | BROWSER_AUTONOMY.md | MISSING | Add to web tool |
| Browser autonomy emergent navigation | BROWSER_AUTONOMY.md | MISSING | Add to agent system prompts |

### Code Files to Change
- `app/tools/web.py` - Add browser session management, DOM extraction, research loop
- `app/tools/gateway.py` - Integrate browser tool with permission system
- `app/agents/observer.py` - Add browser autonomy prompts

---

## 8. Capability-Driven Model Selection

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Agents request capabilities at runtime | PROJECT_STATE.md | MISSING | Add capability field to AgentConfig |
| Model selection based on task requirements | PROJECT_STATE.md | MISSING | Add model routing logic |
| Dynamic model loading | PROJECT_STATE.md | MISSING | Add to ModelRegistry |
| Capability metadata for each model | PROJECT_STATE.md | MISSING | Add model info with capabilities |

### Code Files to Change
- `app/models/base.py` - Add model capabilities metadata
- `app/models/base.py` - Add model registry capability lookup
- `app/capabilities/registry.py` - Enhance DEFAULT_AGENT_CAPABILITIES

---

## 9. Resource-Aware Scheduling

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Task budgets per agent per turn | PROJECT_STATE.md | MISSING | Add to scheduler |
| Model loading coordination | PROJECT_STATE.md | MISSING | Add to ResourceManager |
| Priority scheduler with agent objectives | PROJECT_STATE.md | MISSING | Add priority queue |
| Resource pre-allocation for proposals | PROJECT_STATE.md | MISSING | Add to ResourceManager |

### Code Files to Change
- `app/resources/monitor.py` - Add task budgets, priority scheduling
- `app/orchestration/scheduler.py` - Add priority queue, task budgets
- `app/orchestration/state_machine.py` - Integrate resource checks

---

## 10. Agent Communication with Intent Metadata

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Messages include intent field in metadata | PROJECT_STATE.md | PARTIAL | Message content type has intent but not structured |
| Agents communicate discoverable intentions | PROJECT_STATE.md | MISSING | Add intent field to AgentMessage |
| Intent taxonomy for inter-agent communication | PROJECT_STATE.md | MISSING | Define intent types |

### Code Files to Change
- `app/events/schemas.py` - Add intent field to AgentMessage dataclass
- `app/events/bus.py` - Update Event publishing to include intent

---

## 11. Self-Modification Boundaries

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Technical enforcement of protected files | SELF_MODIFICATION_ADDON.md | PARTIAL | Git worktree exists but no protected file enforcement |
| Agent-approved modifications only | SELF_MODIFICATION_ADDON.md | MISSING | Add agent approval workflow |
| Modification rollback with evidence | SELF_MODIFICATION_ADDON.md | COMPLETE | Rollback works but no audit trail |

### Code Files to Change
- `app/self_modification/engine.py` - Add protected files list, agent approval workflow
- `app/evidence/manager.py` - Add modification evidence recording

---

## 12. Agent Capability Discovery

| Requirement | Documentation Reference | Code Status | Action Required |
|---|---|---|---|
| Agents discover capabilities at runtime | PROJECT_STATE.md | MISSING | Add capability discovery in base agent |
| Publish discovered capabilities to bus | PROJECT_STATE.md | MISSING | Add capability publication event |
| Consume discovered capabilities from bus | PROJECT_STATE.md | MISSING | Add capability subscription |

### Code Files to Change
- `app/agents/base.py` - Add capability discovery/ publication methods
- `app/events/bus.py` - Add capability event types
- `app/capabilities/registry.py` - Add capability publication/consumption

---

## Summary: Priority Code Changes

### High Priority (align code with autonomy architecture)
1. **Remove AgentRole enum from schemas.py** - Replace with agent identity
2. **Replace system prompts in explorer.py/challenger.py/observer.py** - Capability-based not role-based
3. **Update DEFAULT_AGENT_CAPABILITIES in registry.py** - Remove fixed role assignments
4. **Add emergence observation events** - emergence.observed, self_assessment, role_change, disagreement
5. **Add 7-stage intent-action tracking** in evidence recording pipeline
6. **Add Context Manager** as separate component

### Medium Priority (enhance capabilities)
7. **Implement autonomous agent decision loop** (plan→execute→evaluate per turn)
8. **Add intent metadata to AgentMessage** 
9. **Add capability discovery and publication**
10. **Enhance tool gateway with browser autonomy**

### Lower Priority (polish and complete)
11. **Implement Master Control Plane** (auth, command bus, intervention, emergency)
12. **Resource-aware scheduling with task budgets**
13. **Self-modification boundaries with agent approval**
14. **Browser session management and research loop**

### Note on Tests
- No automated integration tests exist
- Manual CLI testing verified: start, watch, interactive modes
- Session persistence and recovery verified
- Evidence recording for all event types verified
- Need: pytest suite for all new code changes

Let me now start implementing the code changes, beginning with the most critical ones.