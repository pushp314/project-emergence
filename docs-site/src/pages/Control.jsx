import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Control.css';

export default function Control() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Master Control Plane</h1>
                <p className="page-subtitle">
                    System-level safety and control mechanisms
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Emergency Stop</h2>
                <p className="section-subtitle">
                    Immediately halts all agent activity. The conversation state
                    transitions to IDLE, and all pending operations are cancelled.
                </p>

                <CodeBlock title="Emergency stop via CLI" language="text">
{`YOU > /emergency-stop

System halted.
All agents stopped.
State preserved in evidence database.

YOU > /status

┌─────────────────────────────┐
│       AI SANDBOX — SYSTEM STATUS             │
├─────────────────────────────────────────────┤
│ Status:        idle           │
│ Turn:          n/a            │
│ Current:       none           │
│ Model:         qwen2.5-coder:7b            │
│ Memory:        0.2 GB / 16 GB              │
│ CPU:           2%                         │
│ Permissions:   read only                │
│ WAL mode:      enabled                     │
│ Events logged: 247                         │
└─────────────────────────────────────────────┘`}
</CodeBlock>

                <h3 className="subsection-title">When to Use Emergency Stop</h3>
                <ul className="resource-list">
                    <li>Agent enters infinite loop</li>
                    <li>Unsafe tool execution (e.g., rm -rf /)</li>
                    <li>Memory usage exceeds safe thresholds</li>
                    <li>Need to immediately terminate investigation</li>
                    <li>Human takes control of conversation</li>
                </ul>

                <CodeBlock title="Emergency stop in code" language="text">
{`import { MasterControlPlane } from 'app.control'

control = MasterControlPlane(event_bus)

# Emergency halt
await control.emergency_stop()

# Verify system state
status = await control.get_system_status()
assert status["status"] == "idle"`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Pause & Resume</h2>
                <p className="section-subtitle">
                    Gracefully pause the conversation at a turn boundary and resume
                    later. All state is preserved.
                </p>

                <CodeBlock title="Pause conversation" language="text">
{`YOU > /pause

Conversation paused at turn 15.
Current agent: ATLAS

YOU > /resume

🧭 ATLAS  Turn 16 (resumed)
│ Continuing from where we left off...`}
</CodeBlock>

                <h3 className="subsection-title">Use Cases</h3>
                <ul className="resource-list">
                    <li>Step away from the computer</li>
                    <li>Human wants to inject a specific message</li>
                    <li>Need to review evidence before continuing</li>
                    <li>Temporary interruption without losing state</li>
                </ul>
            </section>

            <section className="content-section">
                <h2 className="section-title">System Status</h2>
                <CodeBlock title="Full system status output" language="text">
{`┌─────────────────────────────────────────────┐
│       AI SANDBOX — SYSTEM STATUS             │
├─────────────────────────────────────────────┤
│ Status:        running                       │
│ Turn:          23 of 100                    │
│ Current Agent:  ATLAS                       │
│ Model:         qwen2.5-coder:7b             │
│ Memory Usage:  3.1 GB / 16 GB (19%)        │
│ CPU Usage:     8%                          │
│ WAL Mode:      enabled                      │
│ Evidence Count: 123                         │
│ Conversations: 1 active                     │
│ Sessions Saved: yes                         │
│ Last Backup:   2026-08-26 14:30            │
│ Next Backup:   2026-08-26 15:30 (auto)     │
│ Resource Limits:                          │
│   • Turn timeout: 180s                      │
│   • Max turns: 100                          │
│   • Memory warning: 12 GB                   │
│   • CPU warning: 80%                        │
└─────────────────────────────────────────────┘`}
</CodeBlock>

                <h3 className="subsection-title">Status Components</h3>
                <div className="status-grid">
                    <div className="status-item">
                        <div className="status-label">Status</div>
                        <div className="status-value">running / paused / idle</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Current Agent</div>
                        <div className="status-value">ATLAS / ARGUS / none</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Turn</div>
                        <div className="status-value">N / 100</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Memory</div>
                        <div className="status-value">X GB / 16 GB</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Evidence</div>
                        <div className="status-value">N entries</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Model</div>
                        <div className="status-value">qwen2.5-coder:7b</div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Command Bus</h2>
                <p className="section-subtitle">
                    The command bus routes CLI commands to the appropriate system
                    components. Commands are published as events on the event bus
                    and handled by the control plane.
                </p>

                <CodeBlock title="Command bus event flow" language="text">
{`CLI command (/start, /stop, /status, etc.)
   │
   ▼
CommandParser parses the command
   │
   ▼
MasterControlPlane handles the command
   │
   ▼
Appropriate action taken:
  • /start → ConversationEngine.start()
  • /stop → ConversationEngine.pause()
  • /emergency-stop → MasterControlPlane.emergency_stop()
  • /status → get_system_status() → render
   │
   ▼
Status/event published to EventBus
   │
   ▼
All subscribers receive the update:
  • CLI: renders new status
  • ConversationEngine: updates state
  • EvidenceManager: logs the action
  • ResourceMonitor: checks new resource levels`}
</CodeBlock>

                <h3 className="subsection-title">Human Intervention</h3>
                <p className="section-text">
                    The control plane supports real-time human intervention. At any point
                    during a conversation, you can:
                </p>
                <ul className="resource-list">
                    <li>Type any message — it's injected as the next agent input</li>
                    <li>/inject <message> — explicitly redirect the conversation</li>
                    <li>/pause — halt agents at turn boundary</li>
                    <li>/emergency-stop — immediate halt</li>
                    <li>/resume — continue from paused state</li>
                </ul>
            </section>

            <section className="content-section">
                <h2 className="section-title">Authentication</h2>
                <p className="section-subtitle">
                    Optional API key-based authentication for controlling access to
                    the sandbox. When enabled, commands require valid authentication.
                </p>

                <CodeBlock title="AuthManager setup" language="text">
{`from app.control import AuthManager

# Disable (default — open access)
auth = AuthManager(enabled=True)

# Generate a key
key = auth.generate_key()
print(f"Your auth key: {key}")

# Check if a key is valid
is_valid = auth.check_auth("my-secret-key")  # True or False`}
</CodeBlock>

                <CodeBlock title="Auth in CLI" language="text">
{`# With auth enabled, commands may require authentication
YOU > /status
# If auth is enabled and key not provided:
# Please provide authentication key

YOU > /status my-secret-key
# Returns full status report`}
</CodeBlock>

                <ul className="resource-list">
                    <li>Auth is disabled by default in config.yaml</li>
                    <li>Enable via: <code>auth: enabled: true</code> in config.yaml</li>
                    <li>Keys are SHA-256 hashed for security</li>
                    <li>Use <code>/generate-key</code> CLI command to create a new key</li>
                </ul>
            </section>
        </div>
    );
}