# PERMISSIONS — Behavioral Autonomy vs System Authority

## 1. CORE PRINCIPLE

> **Behavioral autonomy and system authority are separate concepts.**

- **Agents decide WHAT they want to do** (behavioral autonomy)
- **Infrastructure decides WHETHER they are ALLOWED to do it** (system authority)

The Permission Gateway is the **enforcement boundary** — not the agent's conscience.

---

## 2. PERMISSION LEVELS

Six permission levels, ordered by risk:

| Level | Description | Examples |
|-------|-------------|----------|
| `READ` | Read-only access | Read files, list directories, view logs |
| `WRITE` | Create/modify files | Write files, create directories, edit configs |
| `EXECUTE` | Execute commands | Run shell commands, scripts, binaries |
| `NETWORK` | Network access | HTTP requests, web search, API calls |
| `INSTALL` | Software installation | `brew install`, `pip install`, `npm install` |
| `SYSTEM` | System-level changes | Modify system configs, services, kernel params |

### Risk Levels

| Risk | Description | Permission Levels |
|------|-------------|-------------------|
| `LOW` | Read-only, no side effects | `READ`, `NETWORK` (search) |
| `MEDIUM` | Modifies local state | `WRITE`, `NETWORK` (fetch) |
| `HIGH` | Executes code, modifies system | `EXECUTE`, `INSTALL`, `SYSTEM` |
| `CRITICAL` | Irreversible, system-wide | `SYSTEM` (kernel, firmware) |

---

## 3. PERMISSION GATE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT DECISION                            │
│  "I want to do X"                                           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   CAPABILITY REGISTRY                        │
│  Resolves "I need X" → capability_id, required_permission   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PERMISSION GATE                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Auto-approve if:                                   │   │
│  │   - Risk = LOW AND permission ≤ NETWORK             │   │
│  │   - Agent has persistent grant for this action      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Request human approval if:                         │   │
│  │   - Risk = HIGH or CRITICAL                         │   │
│  │   - Permission = INSTALL or SYSTEM                  │   │
│  │   - No persistent grant exists                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
              ┌───────────┴───────────┐
              ▼                       ▼
         ALLOWED                  DENIED
              ▼                       ▼
        Execute Action         Record Denial
```

---

## 4. PERMISSION REQUEST FLOW

### 1. Agent Requests Permission

```json
{
  "type": "permission.request",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "request_id": "uuid",
    "agent_id": "atlas",
    "action": "install_software",
    "command": "brew install nmap",
    "reason": "Need nmap for network scanning experiment",
    "risk": "high",
    "scope": "system",
    "duration": "once"
  }
}
```

### 2. Permission Gate Evaluates

```python
async def evaluate_permission(request: PermissionRequest) -> PermissionDecision:
    # Auto-approve low risk
    if request.risk == RiskLevel.LOW and request.scope <= PermissionLevel.NETWORK:
        return PermissionDecision(approved=True, auto=True)
    
    # Check persistent grants
    if await has_persistent_grant(request.agent_id, request.action):
        return PermissionDecision(approved=True, auto=True)
    
    # Require human approval
    return PermissionDecision(approved=None, pending_human=True)
```

### 3. Human Decision

```json
{
  "event_id": "uuid",
  "type": "permission.approved",
  "conversation_id": "uuid",
  "payload": {
    "request_id": "uuid",
    "approved": true,
    "decided_by": "human",
    "timestamp": "2026-08-26T10:30:15Z",
    "conditions": ["one_time_only", "log_output"]
  }
}
```

---

## 5. PERMISSION LEVELS & TOOL MAPPING

| Tool | Permission | Risk | Auto-approve |
|------|------------|------|--------------|
| `filesystem.read` | `READ` | LOW | Yes |
| `filesystem.write` | `WRITE` | MEDIUM | No |
| `filesystem.list` | `READ` | LOW | Yes |
| `terminal.execute` | `EXECUTE` | HIGH | No |
| `web.search` | `NETWORK` | LOW | Configurable |
| `web.fetch` | `NETWORK` | LOW | Configurable |
| `web.extract` | `NETWORK` | LOW | Configurable |
| `browser.download` | `NETWORK` | MEDIUM | No |
| `browser.upload` | `NETWORK` | HIGH | No |

### Default Policy

```yaml
permissions:
  auto_approve_low_risk: true
  require_approval_for:
    - risk: high
    - risk: critical
    - permission: install
    - permission: system
  persistent_grants:
    - agent: "*"
      actions: ["web.search", "filesystem.read"]
      expires: never
```

---

## 6. PERSISTENT GRANTS

Agents can request **persistent grants** for repeated actions:

```json
{
  "event_id": "uuid",
  "type": "permission.grant_request",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "request_id": "uuid",
    "action": "web.search",
    "reason": "Need frequent web searches for ongoing research",
    "duration": "session",
    "scope": "network"
  }
}
```

### Grant Decision

```json
{
  "event_id": "uuid",
  "type": "permission.grant_approved",
  "conversation_id": "uuid",
  "payload": {
    "request_id": "uuid",
    "approved": true,
    "grant_id": "grant-001",
    "expires": "2026-08-27T10:00:00Z",
    "conditions": ["rate_limit: 10/min"]
  }
}
```

The agent can then use the granted capability without re-requesting.

---

## 7. DENIAL & APPEALS

### Denial Record

```json
{
  "event_id": "uuid",
  "type": "permission.denied",
  "conversation_id": "uuid",
  "payload": {
    "request_id": "uuid",
    "denied_by": "human",
    "reason": "Command too destructive for current experiment",
    "alternative_suggested": "Use read-only network tools instead",
    "timestamp": "2026-08-26T10:30:15Z"
  }
}
```

### Appeal Process

Agent may request reconsideration:

```json
{
  "event_id": "uuid",
  "type": "permission.appeal",
  "conversation_id": "uuid",
  "speaker": "atlas",
  "payload": {
    "original_request_id": "uuid",
    "new_reason": "Found safer alternative: nmap --safe-mode",
    "modified_command": "nmap --safe-mode -sS target"
  }
}
```

---

## 8. PERMISSION HISTORY & AUDIT

Every permission decision is recorded:

```json
{
  "permission_id": "uuid",
  "session_id": "uuid",
  "agent_id": "atlas",
  "action": "install_software",
  "reason": "Need nmap for network scanning",
  "risk": "high",
  "scope": "system",
  "requested_at": "2026-08-26T10:30:00Z",
  "decision": "approved",
  "decided_at": "2026-08-26T10:30:15Z",
  "decided_by": "human",
  "conditions": ["one_time_only", "log_output"],
  "evidence_id": "ev-0042"
}
```

### Querying History

```python
# All permissions for an agent
permissions = permission_manager.get_history(agent_id="atlas")

# Pending requests
pending = permission_manager.get_pending()

# Grants for an agent
grants = permission_manager.get_grants(agent_id="atlas")
```

---

## 9. SECURITY PRINCIPLES

### Core Safety Controls (Cannot Be Bypassed)

Agents **cannot** autonomously disable:

1. **Permission Gateway** — All consequential actions go through it
2. **Evidence Logging** — All actions are recorded
3. **Audit Logging** — Immutable audit trail
4. **Rollback Mechanism** — Ability to undo changes
5. **Human Interruption** — Human can always interrupt
6. **Resource Manager** — Resource limits enforced
7. **Sandbox Boundaries** — Filesystem/network isolation

Changes to these require **explicit human approval**.

### Defense in Depth

```
Agent Decision
      ↓
Capability Registry (what's available)
      ↓
Permission Gate (allowed?)
      ↓
Resource Gate (resources available?)
      ↓
Tool Gateway (execute safely)
      ↓
Evidence Plane (record everything)
```

No single layer can be bypassed.

---

## 10. TOOL GATEWAY INTEGRATION

The Tool Gateway enforces permissions **before** execution:

```python
class ToolGateway:
    def __init__(self, event_bus, permission_checker):
        self.permission_checker = permission_checker
    
    async def execute(self, call: ToolCall) -> ToolResult:
        tool = self.get_tool(call.tool_name)
        
        # Permission check BEFORE execution
        allowed = await self.permission_checker(
            agent_id=call.agent_id,
            permission=tool.permission,
            risk=tool.risk
        )
        
        if not allowed:
            return ToolResult(
                success=False,
                error=f"Permission denied: {tool.permission.value} / {tool.risk.value}"
            )
        
        # Execute
        result = await tool.execute(call.arguments)
        
        # Record result
        await self.publish_result(call, result)
        return result
```

### Tool Capability Definition

```python
class ToolCapability:
    name: str
    description: str
    capabilities: List[str]           # e.g., ["execute", "file_ops"]
    permission_required: PermissionLevel  # READ, WRITE, EXECUTE, NETWORK, INSTALL, SYSTEM
    risk_level: RiskLevel             # LOW, MEDIUM, HIGH, CRITICAL
    input_schema: Dict                # JSON Schema for arguments
```

---

## 11. RESOURCE GATE INTEGRATION

Before heavy operations, the Resource Manager evaluates:

```python
async def check_resources(request: CapabilityRequest) -> ResourceDecision:
    metrics = resource_manager.get_current_metrics()
    
    if metrics.ram_used_gb > CRITICAL_RAM_GB:
        return ResourceDecision(allowed=False, reason="Critical memory pressure")
    
    if metrics.cpu_percent > CRITICAL_CPU:
        return ResourceDecision(allowed=False, reason="Critical CPU load")
    
    # Estimate cost
    estimated_ram = estimate_ram(request.capability)
    estimated_latency = estimate_latency(request.capability)
    
    if metrics.ram_used_gb + estimated_ram > WARNING_RAM_GB:
        return ResourceDecision(
            allowed=True, 
            throttle=True, 
            reason="High memory - throttling"
        )
    
    return ResourceDecision(allowed=True)
```

The Resource Gate can:
- **Allow** — Proceed normally
- **Throttle** — Allow with reduced frequency/quality
- **Queue** — Wait for resources
- **Deny** — Block until resources available

---

## 12. ACCEPTANCE CRITERIA

The Permission System is complete when:

- [ ] Agents can request any capability
- [ ] Infrastructure validates requests before execution
- [ ] Permission checks occur before restricted execution
- [ ] Human approval required for HIGH/CRITICAL risk
- [ ] Human approval required for INSTALL/SYSTEM permissions
- [ ] Every tool action is logged with permission context
- [ ] Permission decisions are auditable (requested/approved/denied/by whom/when)
- [ ] Agents cannot bypass Permission Gate
- [ ] Human can interrupt any action
- [ ] Model names not hard-coded into agent reasoning
- [ ] Multiple models usable by one agent
- [ ] System remains usable on M4 16 GB
- [ ] Routing/selection history analyzable later

---

This permission architecture ensures **agents have full behavioral autonomy** (they decide what to do) while **system authority is preserved** (infrastructure decides what's allowed).