# Known Issues

## CRITICAL
None

## HIGH
None

## MEDIUM

### Issue: Ollama Connector Closed During Shutdown
- **Observed:** `aiohttp.client.ClientSession` errors during shutdown when agents still have pending streaming requests
- **Severity:** MEDIUM (non-fatal, cleanup issue)
- **Expected:** Clean shutdown without connector errors
- **Reproduction:** Run `python -m app start`, wait for 1-2 turns, press Ctrl+C
- **Likely Cause:** Model registry closes session before conversation engine fully stops
- **Workaround:** None needed - non-fatal
- **Proposed Fix:** Add graceful shutdown sequence: stop conversation → wait for in-flight requests → close model registry
- **Status:** Open

### Issue: State Machine Invalid Transitions During Rapid Shutdown
- **Observed:** `Invalid transition: GRACEFUL_SHUTDOWN -> SPEAKING` warnings
- **Severity:** MEDIUM (non-fatal, logging noise)
- **Expected:** State machine should reject or ignore transitions after GRACEFUL_SHUTDOWN
- **Reproduction:** Rapid Ctrl+C during agent generation
- **Likely Cause:** Conversation engine continues processing after shutdown signal
- **Workaround:** None needed - state machine correctly rejects
- **Proposed Fix:** Add shutdown flag check in _process_turn before state transitions
- **Status:** Open

---

## LOW

### Issue: Agent ID "unknown" in Some Evidence Records
- **Observed:** Some evidence records show `agent_id: "unknown"`
- **Severity:** LOW (cosmetic, doesn't affect functionality)
- **Expected:** All evidence should have correct agent ID
- **Reproduction:** System events (pause/resume/stop) don't have agent_id in payload
- **Likely Cause:** System events don't include agent_id
- **Workaround:** Filter by evidence_type when querying
- **Proposed Fix:** Add "system" as agent_id for system events
- **Status:** Open

### Issue: Resource Metrics Not Persisted
- **Observed:** resource_metrics table remains empty
- **Severity:** LOW (feature gap)
- **Expected:** Periodic resource metrics persisted for historical analysis
- **Reproduction:** Check resource_metrics table after running
- **Likely Cause:** ResourceManager doesn't call evidence_manager.record_resource_metrics
- **Proposed Fix:** Add periodic metric recording to ResourceManager
- **Status:** FIXED - ResourceManager now calls evidence_manager.record_resource_metrics during monitoring loop

### Issue: Observer Agent Not Triggering Interventions
- **Observed:** Observer agent never speaks despite configured to intervene
- **Severity:** LOW (feature gap)
- **Expected:** Observer should intervene on repetition, contradictions, low health
- **Reproduction:** Run long conversation, check for observer interventions
- **Likely Cause:** Observer intervention logic not triggered correctly
- **Proposed Fix:** Debug observer evaluation logic, add intervention triggers
- **Status:** Open

### Issue: Web Tool Search Limited to DuckDuckGo HTML
- **Observed:** Web search only uses DuckDuckGo HTML scraping
- **Severity:** LOW (functional limitation)
- **Expected:** Multiple search backends, better result parsing
- **Likely Cause:** Simple implementation for MVP
- **Proposed Fix:** Add multiple search providers, improve result extraction
- **Status:** Open

---

## DESIGN DEBT

### Issue: No Database Migrations Framework
- **Observed:** Schema changes require manual SQL
- **Severity:** DESIGN DEBT
- **Proposed Fix:** Add simple migration system with versioned SQL files
- **Status:** Planned

### Issue: No Vector Database for Semantic Memory Search
- **Observed:** Memory retrieval uses SQLite FTS/structured queries only
- **Severity:** DESIGN DEBT (may be sufficient for current scale)
- **Proposed Fix:** Evaluate need after scale testing; add pgvector/FAISS if needed
- **Status:** Deferred

### Issue: No Automated Test Suite
- **Observed:** Only manual CLI testing performed
- **Severity:** DESIGN DEBT
- **Proposed Fix:** Add pytest suite for all components
- **Status:** PARTIALLY RESOLVED - 52 tests across 5 files covering core, context manager, evidence manager, migrations, and database backup/health

### Issue: Hardcoded Model Capabilities
- **Observed:** DEFAULT_MODEL_CAPABILITIES defined in registry.py
- **Severity:** DESIGN DEBT
- **Proposed Fix:** Load from config file or model metadata
- **Status:** Planned

### Issue: No Structured Logging (JSONL)
- **Observed:** Logging uses human-readable format
- **Severity:** DESIGN DEBT
- **Proposed Fix:** Add JSONL structured logging for Evidence Plane
- **Status:** Planned

### Issue: Fixed Agent Roles in Source Code
- **Observed:** Source code defines `AgentRole.EXPLORER`, `AgentRole.CHALLENGER`, `AgentRole.OBSERVER` enums and hard-coded system prompts assigning fixed roles
- **Severity:** DESIGN DEBT (conflicts with autonomy architecture)
- **Likely Cause:** Early implementation used fixed roles for convenience
- **Proposed Fix:** Replace AgentRole enum with agent identity only; system prompts should describe capabilities not roles; agents self-declare roles via self-assessment events
- **Status:** Open

### Issue: Capability Registry Contains Fixed Role Assignments
- **Observed:** DEFAULT_AGENT_CAPABILITIES in registry.py assigns "explorer" role to agent_a and "challenger" role to agent_b with hardcoded capability lists
- **Severity:** DESIGN DEBT (conflicts with autonomy architecture)
- **Likely Cause:** Early implementation used fixed roles for capability routing
- **Proposed Fix:** Replace with identity-based capabilities; agents should discover and request capabilities dynamically; remove role field from AgentCapability
- **Status:** Open

### Issue: Agent System Prompts Prescribe Fixed Behaviors
- **Observed:** explorer.py and challenger.py have system prompts that explicitly assign "Explorer" and "Challenger" roles with prescribed behaviors
- **Severity:** DESIGN DEBT (contaminates the experiment per RULES.md)
- **Likely Cause:** Early implementation needed behavioral differentiation
- **Proposed Fix:** Replace with generic autonomous agent prompts that describe available capabilities without prescribing roles; agents self-determine behavior
- **Status:** Open

### Issue: Event Schema References Fixed Roles
- **Observed:** Event payloads include role field from AgentRole enum (explorer/challenger/observer)
- **Severity:** DESIGN DEBT (conflicts with autonomous agent identity)
- **Proposed Fix:** Change role field to identity field (atlas/argus/observer) or remove; track self-declared roles via separate emergence events
- **Status:** Open

---

## PERFORMANCE

### Issue: Model Loading/Unloading Not Implemented
- **Observed:** All models stay loaded in Ollama
- **Severity:** PERFORMANCE (memory usage)
- **Expected:** Load on demand, unload after cooldown
- **Proposed Fix:** Implement model loading policy in ResourceManager
- **Status:** Open

### Issue: No Prompt Caching
- **Observed:** Repeated system prompts sent every turn
- **Severity:** PERFORMANCE (token waste)
- **Proposed Fix:** Implement prompt caching in ModelAdapter
- **Status:** Planned

---

## SECURITY

### Issue: Terminal Tool Allows Arbitrary Commands
- **Observed:** Terminal tool has blocked_commands list but allowlist is optional
- **Severity:** SECURITY (if allowlist not configured)
- **Expected:** Secure by default with allowlist
- **Proposed Fix:** Make allowlist required, block by default
- **Status:** Open

### Issue: Web Tool Can Access Localhost
- **Observed:** blocked_domains includes localhost but allowlist is optional
- **Severity:** SECURITY (SSRF risk)
- **Proposed Fix:** Block private IPs by default, require explicit allowlist
- **Status:** Open

### Issue: Filesystem Tool Base Path Not Enforced for Symlinks
- **Observed:** Symlink resolution could escape base path
- **Severity:** SECURITY
- **Proposed Fix:** Resolve symlinks and verify within base path
- **Status:** Open

---

## DOCUMENTATION vs IMPLEMENTATION MISMATCHES (Discovered During Sync)

### Issue: Documentation Claims Autonomy But Code Has Fixed Roles
- **Observed:** RULES.md, ARCHITECTURE.md, AGENT_AUTONOMY.md describe full autonomy with emergent roles, but source code (base.py, explorer.py, challenger.py, schemas.py, registry.py) implements fixed roles (Explorer/Challenger/Observer)
- **Severity:** HIGH (architectural contradiction)
- **Impact:** Experiment contamination - agents are prescribed roles rather than discovering them
- **Proposed Fix:** 
  1. Remove AgentRole enum from schemas.py, replace with agent identity
  2. Update base.py to use identity instead of role
  3. Replace explorer.py/challenger.py system prompts with generic autonomous agent prompts
  4. Update registry.py DEFAULT_AGENT_CAPABILITIES to remove fixed role assignments
  5. Add emergence observation events to evidence system
- **Status:** Documented - requires implementation

### Issue: Intent vs Action Distinction Not Fully Implemented
- **Observed:** EVIDENCE_SYSTEM.md documents 7-stage distinction (intent→request→permission→execution→result→interpretation→follow-up), but evidence schemas only capture basic intent/action
- **Severity:** MEDIUM (incomplete implementation)
- **Proposed Fix:** Extend evidence schemas to capture all 7 stages with correlation IDs
- **Status:** Open

### Issue: Emergence Observation Not Implemented
- **Observed:** AGENT_AUTONOMY.md and ARCHITECTURE.md describe emergence observation (specialization, leadership, cooperation, etc.) but no emergence.observed event type or recording exists in code
- **Severity:** MEDIUM (missing experimental capability)
- **Proposed Fix:** Add emergence.observed event type, evidence schema, and observer analysis logic
- **Status:** Open

### Issue: Self-Assessment and Role Change Events Not Implemented
- **Observed:** AGENT_AUTONOMY.md documents agent.self_assessment and agent.role_change events, but these don't exist in EventType enum or evidence schemas
- **Severity:** MEDIUM (missing autonomy tracking)
- **Proposed Fix:** Add event types and evidence schemas for self-assessment and role change tracking
- **Status:** Open

### Issue: Agent Disagreement Events Not Implemented
- **Observed:** AGENT_AUTONOMY.md documents agent.disagreement events with preserved positions and evidence, but not implemented in code
- **Severity:** MEDIUM (missing conflict tracking)
- **Proposed Fix:** Add disagreement event type and evidence schema
- **Status:** Open

### Issue: Experiment Categories Not Reflected in Code
- **Observed:** EXPERIMENTS.md defines 4 experiment categories with specific metrics, but ExperimentRecord schema doesn't capture category or emergence metrics
- **Severity:** LOW (documentation ahead of implementation)
- **Proposed Fix:** Extend experiment schema with category and emergence tracking fields
- **Status:** Open