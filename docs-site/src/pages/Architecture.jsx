import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Architecture.css';

export default function Architecture() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Architecture</h1>
                <p className="page-subtitle">Layered event-driven design with complete observability</p>
            </div>

            <section className="content-section">
                <h2 className="section-title">System Overview</h2>
                <p className="section-subtitle">
                    AI Sandbox is organized into six distinct layers, each with a clearly defined
                    responsibility. Communication between layers flows through the async event bus,
                    ensuring loose coupling and making it trivial to add observers, swap components,
                    or extend functionality without modifying core logic.
                </p>

                <div className="arch-diagram">
                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">CLI Layer</div>
                            <span>Interactive Terminal &middot; Rich UI &middot; Command Parser</span>
                        </div>
                    </div>
                    <div className="arch-arrow">▼</div>

                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">Control Plane</div>
                            <span>Master Control &middot; Auth &middot; Emergency Stop &middot; Permission Manager &middot; Resource Monitor</span>
                        </div>
                    </div>
                    <div className="arch-arrow">▼</div>

                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">Orchestration</div>
                            <span>Conversation Engine &middot; Round-Robin/Adaptive Scheduler &middot; State Machine (IDLE→THINKING→GENERATING→SPEAKING→OBSERVING)</span>
                        </div>
                    </div>
                    <div className="arch-arrow">▼</div>

                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">Event Bus</div>
                            <span>Async Pub/Sub &middot; Structured Events &middot; Event History &middot; Filtered Subscriptions</span>
                        </div>
                    </div>
                    <div className="arch-arrow">▼</div>

                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">Agents</div>
                            <span>Atlas (Explorer) &middot; Argus (Challenger) &middot; BaseAgent (shared logic)</span>
                        </div>
                    </div>
                    <div className="arch-arrow">▼</div>

                    <div className="arch-row">
                        <div className="arch-layer">
                            <div className="arch-box">Infrastructure</div>
                            <span>Tool Gateway (Terminal/FS/Web) &middot; SQLiteStore (Memory) &middot; EvidenceManager &middot; Resource Monitor</span>
                        </div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Event Flow — Detailed</h2>
                <p className="section-subtitle">
                    Every interaction in AI Sandbox follows a structured event loop with full traceability:
                </p>
                <ol className="flow-steps">
                    <li className="flow-step">
                        <div className="step-index">1</div>
                        <div className="step-content">
                            <strong>User Input</strong> — A message or command enters through the CLI layer and is wrapped in a structured <code>UserMessageEvent</code>.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">2</div>
                        <div className="step-content">
                            <strong>Control Plane Check</strong> — The <code>MasterControlPlane</code> intercepts the event, validates permissions against the agent's allowed capabilities, checks resource budgets (memory, CPU, turn count), and confirms the system is not in emergency stop or paused state.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">3</div>
                        <div className="step-content">
                            <strong>Orchestration Dispatch</strong> — The <code>ConversationEngine</code> consults the <code>Scheduler</code> (round-robin by default, adaptive under load) to select the next agent to speak, then queues an <code>AgentTurnEvent</code> containing the full conversation context.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">4</div>
                        <div className="step-content">
                            <strong>Agent Processing</strong> — The assigned agent (<code>ExplorerAgent</code> or <code>ChallengerAgent</code>) receives the <code>AgentTurnEvent</code>, assembles context via <code>ContextManager</code>, reasons about a response, and optionally invokes tools by emitting <code>ToolCallEvent</code> markers in its output.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">5</div>
                        <div className="step-content">
                            <strong>Tool Execution</strong> — Tool calls are routed through the <code>ToolGateway</code> to the correct handler (<code>ShellExecutor</code>, <code>FilesystemExecutor</code>, <code>WebFetcher</code>), executed in a sandboxed environment with timeouts, and results are returned as <code>ToolResultEvent</code> with full output/error capture.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">6</div>
                        <div className="step-content">
                            <strong>Event Emission</strong> — The agent's response and any tool results are published back to the event bus as structured events (<code>AgentResponseEvent</code>, <code>ToolResultEvent</code>). All subscribers receive them in registration order.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">7</div>
                        <div className="step-content">
                            <strong>State Update</strong> — The orchestrator updates conversation state via <code>ConversationEngine</code>, persists messages via <code>ContextManager</code>, stores evidence via <code>EvidenceManager</code>, and updates memory via <code>SQLiteStore</code>.
                        </div>
                    </li>
                    <li className="flow-step">
                        <div className="step-index">8</div>
                        <div className="step-content">
                            <strong>Output Rendering</strong> — The CLI layer consumes events from the bus and renders the response to the terminal using Rich formatting with syntax highlighting, panels, and thinking indicators.
                        </div>
                    </li>
                </ol>
            </section>

            <section className="content-section">
                <h2 className="section-title">Component Dependencies</h2>
                <p className="section-subtitle">
                    Each layer depends only on the layer directly below it, with the event bus
                    serving as the integration point between all components:
                </p>
                <CodeBlock title="Component Dependencies" language="text">
{`CLI Layer
  └── depends on → Event Bus (subscribes to output events)
  └── provides → Interactive REPL, Rich rendering, command parsing

Control Plane
  └── depends on → Event Bus (intercepts and gates all events)
  └── owns → Permission Manager, Resource Monitor, Emergency Stop
  └── provides → AuthManager, Command Bus, Intervention System

Orchestration
  └── depends on → Event Bus (publishes turn events, subscribes to responses)
  └── owns → Conversation Engine, Scheduler (RoundRobin/Adaptive), State Machine
  └── provides → Turn scheduling, context assembly, state transitions

Event Bus
  └── depends on → nothing (foundational layer)
  └── provides → Async pub/sub, event history (1000 events), structured logging
  └── events → AgentTurn, AgentResponse, ToolCall, ToolResult, SystemStop, HumanIntervention

Agents
  └── depends on → Event Bus (receive input, emit responses)
  └── uses → Infrastructure (tools, memory, evidence)
  └── provides → Role-specific reasoning (explorer/challenger), tool invocation

Infrastructure
  └── depends on → Event Bus (receives tool invocations, emits results)
  └── provides → ShellExecutor, FilesystemExecutor, WebFetcher
  └── provides → SQLiteStore (messages, memories, summaries), EvidenceManager
  └── provides → ResourceMonitor (memory, CPU, disk, turn budgets)`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Data Flow — Complete Trace</h2>
                <p className="section-subtitle">
                    Messages flow through the system as structured events, always following the same
                    auditable path. This makes the system fully observable and reproducible.
                </p>

                <h3 className="subsection-title">Inbound: User → Agent</h3>
                <CodeBlock title="Message Flow" language="text">
{`User types message in CLI
   │
   ▼
CLI wraps in UserMessageEvent { conversation_id, content, timestamp }
   │
   ▼
Control Plane: validate_permissions(event) → permitted
   │
   ▼
Orchestration: scheduler.next_agent() → "atlas"
   │
   ▼
ConversationEngine emits AgentTurnEvent {
    conversation_id,
    agent: "atlas",
    context: ContextManager.build_context(conversation_id),
    turn_number: 5,
    timeout: 180
}
   │
   ▼
ExplorerAgent.receive_turn(event)
   │
   ▼
Agent.think(context) → generates response with [TOOL:...] markers
   │
   ▼
Agent emits AgentResponseEvent { content, tools_used: [...] }`}
                </CodeBlock>

                <h3 className="subsection-title">Tool Execution: Agent → Infrastructure → Agent</h3>
                <CodeBlock title="Tool Call Flow" language="text">
{`Agent generates: "Let me check the config" + [TOOL:filesystem:{"operation":"read","path":"config.yaml"}]
   │
   ▼
ConversationEngine parses TOOL markers → emits ToolCallEvent {
    tool: "filesystem",
    args: {"operation": "read", "path": "config.yaml"},
    call_id: "tc_abc123",
    agent: "atlas",
    conversation_id: "conv_001"
}
   │
   ▼
ToolGateway.route(event) → FilesystemExecutor.read(path)
   │
   ▼
Executor runs in sandbox (timeout: 5s, cwd restriction)
   │
   ▼
Executor emits ToolResultEvent {
    call_id: "tc_abc123",
    tool: "filesystem",
    success: true,
    output: "model:\n  host: localhost...",
    error: null,
    execution_time_ms: 12
}
   │
   ▼
Agent receives ToolResultEvent → continues reasoning with result
   │
   ▼
Agent emits final AgentResponseEvent`}
                </CodeBlock>

                <h3 className="subsection-title">Outbound: Agent → User + Persistence</h3>
                <CodeBlock title="Response Flow" language="text">
{`Agent emits AgentResponseEvent {
    agent: "atlas",
    content: "The config shows...",
    tools_used: ["filesystem"],
    turn_number: 5
}
   │
   ▼
Event Bus broadcasts to ALL subscribers:
   ├── CLI Layer: renders with Rich.Panel, syntax highlighting
   ├── ConversationEngine: appends to message history
   ├── ContextManager: updates context for next turn
   ├── SQLiteStore: persists ConversationRecord
   ├── EvidenceManager: records tool usage as evidence
   └── ResourceMonitor: updates turn budgets, checks limits
   │
   ▼
ConversationEngine: turn_complete → scheduler.advance() → next AgentTurnEvent`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">State Machine</h2>
                <p className="section-subtitle">
                    The Conversation Engine operates as a deterministic state machine:
                </p>
                <div className="state-machine">
                    <div className="state-node active">IDLE</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">THINKING</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">GENERATING</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">SPEAKING</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">OBSERVING</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">NEXT_TURN</div>
                    <div className="state-arrow">→</div>
                    <div className="state-node">THINKING</div>
                </div>
                <table className="state-table">
                    <thead>
                        <tr><th>State</th><th>Description</th><th>Timeout</th><th>Transitions To</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><code>IDLE</code></td><td>Waiting for start signal or user input</td><td>∞</td><td>THINKING</td></tr>
                        <tr><td><code>THINKING</code></td><td>Agent assembling context, planning response</td><td>30s</td><td>GENERATING</td></tr>
                        <tr><td><code>GENERATING</code></td><td>LLM streaming response (may include tools)</td><td>180s</td><td>SPEAKING / THINKING (if tools)</td></tr>
                        <tr><td><code>SPEAKING</code></td><td>Final response emitted, rendering to CLI</td><td>5s</td><td>OBSERVING</td></tr>
                        <tr><td><code>OBSERVING</code></td><td>Human intervention window (user can type)</td><td>∞ (until /start)</td><td>NEXT_TURN</td></tr>
                        <tr><td><code>NEXT_TURN</code></td><td>Scheduler selects next agent, loop continues</td><td>1s</td><td>THINKING</td></tr>
                    </tbody>
                </table>
            </section>

            <section className="content-section">
                <h2 className="section-title">Concurrency Model</h2>
                <p className="section-subtitle">
                    Sequential inference on M4 Mac (16GB RAM constraint):
                </p>
                <ul className="concurrency-points">
                    <li><strong>Single Model Instance</strong> — Only one Ollama request at a time to fit in 16GB RAM</li>
                    <li><strong>Sequential Agent Turns</strong> — Atlas speaks, completes, then Argus speaks</li>
                    <li><strong>Async Event Bus</strong> — Non-blocking event dispatch; UI stays responsive</li>
                    <li><strong>Parallel Tool Execution</strong> — Multiple tool calls in one agent response run in parallel</li>
                    <li><strong>Background Persistence</strong> — SQLite writes happen on background thread</li>
                </ul>
            </section>
        </div>
    );
}