import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Overview.css';

export default function Overview() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">
                    <span className="gradient-title">AI Sandbox</span>
                </h1>
                <p className="page-subtitle">
                    Autonomous Multi-Agent AI Laboratory for Emergent Intelligence Research
                </p>
                <p className="page-description">
                    A local autonomous AI sandbox where agents converse, use tools, and exhibit
                    emergent behaviors. Built for researchers studying multi-agent systems, tool
                    use, and AI collaboration.
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">What Is AI Sandbox?</h2>
                <p className="section-subtitle">
                    AI Sandbox is a research platform for studying how autonomous AI agents interact,
                    collaborate, and exhibit emergent behaviors when given access to real tools
                    (terminal, filesystem, web) in a controlled, observable environment. Unlike
                    single-agent benchmarks or simulated environments, AI Sandbox provides:
                </p>
                <ul style={{ paddingLeft: '24px', marginTop: '12px', lineHeight: '1.8' }}>
                    <li><strong>Real tool execution</strong> — Agents run actual shell commands, read/write real files, fetch live web pages</li>
                    <li><strong>Full observability</strong> — Every decision, tool call, and response is logged to SQLite with complete audit trail</li>
                    <li><strong>Local-first inference</strong> — Runs on your hardware via Ollama, no API costs, no network dependency</li>
                    <li><strong>Role-based agents</strong> — Distinct personalities (explorer, challenger) create observable dynamics</li>
                    <li><strong>Human-in-the-loop</strong> — You can observe, pause, inject messages, or take control at any time</li>
                </ul>
            </section>

            <section className="content-section">
                <h2 className="section-title">Core Features</h2>
                <div className="feature-grid">
                    <div className="feature-card">
                        <div className="feature-icon">🧭</div>
                        <h3 className="feature-title">Atlas (Explorer)</h3>
                        <p className="feature-description">
                            Autonomous explorer agent that investigates ideas, runs tools, reads
                            code, browses the web, and drives the conversation forward with
                            genuine curiosity.
                        </p>
                        <ul className="feature-details">
                            <li>Generates hypotheses and research directions</li>
                            <li>Uses tools proactively for exploration</li>
                            <li>Builds on Argus's challenges to refine ideas</li>
                        </ul>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">🔍</div>
                        <h3 className="feature-title">Argus (Challenger)</h3>
                        <p className="feature-description">
                            Critical thinker agent that questions assumptions, verifies claims,
                            identifies gaps in reasoning, and pushes for deeper analysis.
                        </p>
                        <ul className="feature-details">
                            <li>Verifies claims with independent tool use</li>
                            <li>Identifies logical gaps and weak methodology</li>
                            <li>Offers alternative perspectives and counter-arguments</li>
                        </ul>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">⚡</div>
                        <h3 className="feature-title">Tool Ecosystem</h3>
                        <p className="feature-description">
                            Full terminal, filesystem, and web access. Agents can execute code,
                            read/write files, fetch web pages, and interact with the real system.
                        </p>
                        <ul className="feature-details">
                            <li>Terminal: whitelisted commands only</li>
                            <li>Filesystem: read/write/list/search operations</li>
                            <li>Web: fetch pages, search, extract content</li>
                        </ul>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">🛡</div>
                        <h3 className="feature-title">Safety & Control</h3>
                        <p className="feature-description">
                            Emergency stop, permission gating, resource monitoring, and human
                            intervention. You stay in control of the autonomous loop.
                        </p>
                        <ul className="feature-details">
                            <li>6-level permission system</li>
                            <li>Real-time resource monitoring</li>
                            <li>Emergency stop halts all agents instantly</li>
                        </ul>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Why AI Sandbox?</h2>
                <div className="why-grid">
                    <div className="why-card">
                        <div className="why-icon">📊</div>
                        <h3 className="why-title">Beyond Static Benchmarks</h3>
                        <p className="why-desc">
                            Standard benchmarks test single-turn accuracy on fixed datasets.
                            Intelligence emerges from interaction. AI Sandbox lets you observe
                            how agents reason over many turns, use tools adaptively, and
                            develop strategies through dialogue.
                        </p>
                    </div>
                    <div className="why-card">
                        <div className="why-icon">🔬</div>
                        <h3 className="why-title">Controlled & Reproducible</h3>
                        <p className="why-desc">
                            Local inference eliminates API variability. SQLite logging provides
                            complete audit trails. Configuration is version-controlled. Every
                            experiment is reproducible on identical hardware.
                        </p>
                    </div>
                    <div className="why-card">
                        <div className="why-icon">🤝</div>
                        <h3 className="why-title">Human-AI Collaboration</h3>
                        <p className="why-desc">
                            The CLI isn't just for observation — you can inject messages,
                            redirect the conversation, provide hints, or take over entirely.
                            Study how human guidance shapes agent trajectories.
                        </p>
                    </div>
                    <div className="why-card">
                        <div className="why-icon">📈</div>
                        <h3 className="why-title">Emergent Behavior Research</h3>
                        <p className="why-desc">
                            Specialization, trust, disagreement, teaching, strategy evolution —
                            these emerge from the system, not from explicit programming.
                            AI Sandbox provides the Petri dish for these dynamics.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Quick Demo</h2>
                <p className="section-subtitle">
                    See the system in action — agents autonomously exploring a codebase:
                </p>
                <CodeBlock title="Terminal Session">
{`$ python -m app start
🧭  Atlas and Argus are standing by.
   Type /help for commands, or just start typing to join.

YOU > /start

🧭 ATLAS  Turn 1
│ Let me explore this codebase to understand its structure.
│
│ [TOOL:terminal:{"command": "find src/ -name '*.py' | head -20"}]

[terminal result: src/main.py
src/agents/base.py
src/agents/explorer.py
src/agents/challenger.py
src/orchestration/conversation.py
src/memory/store.py
src/memory/context_manager.py
src/events/bus.py
src/tools/gateway.py]

🧭 ATLAS  Turn 1 (continued)
│ I can see a modular architecture with separate agents, orchestration,
│ memory, events, and tools. Let me look at the base agent to understand
│ the core interface.

│ [TOOL:filesystem:{"operation": "read", "path": "src/agents/base.py"}]

[filesystem result: class BaseAgent:
    def __init__(self, name, model, tools):
        self.name = name
        self.model = model
        self.tools = tools

    async def think(self, context):
        # Agent reasoning logic
        pass]

🔍 ARGUS  Turn 2
│ Good start, but you're just listing files. The architecture diagram in
│ the docs shows 6 layers — let me check if the code actually matches.

│ [TOOL:filesystem:{"operation": "read", "path": "docs/architecture.md"}]

[filesystem result: # Architecture
Layers: CLI → Control → Orchestration → EventBus → Agents → Infrastructure...]

🔍 ARGUS  Turn 2 (continued)
│ The code structure roughly matches, but there's no explicit "Control"
│ layer module — that logic seems embedded in the orchestration. This
│ could be a design debt. Also, I notice the event bus is synchronous
│ in the code but the docs say async. Let me verify...

│ [TOOL:filesystem:{"operation": "read", "path": "src/events/bus.py"}]

[filesystem result: class EventBus:
    def publish(self, event_type, data):
        for handler in self.subscribers[event_type]:
            handler(data)  # Synchronous!]

🔍 ARGUS  Turn 2 (continued)
│ Confirmed — the event bus is synchronous despite the docs claiming
│ async. This means tool execution blocks the entire system. That's a
│ significant limitation for scaling. Atlas, did you consider this?`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Key Metrics</h2>
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-value">58</div>
                        <div className="metric-label">Tests Passing</div>
                        <div className="metric-sub">Unit + integration</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">6</div>
                        <div className="metric-label">Benchmarks Passed</div>
                        <div className="metric-sub">All under threshold</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">48µs</div>
                        <div className="metric-label">Event Latency</div>
                        <div className="metric-sub">Pub/sub round-trip</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">1.5µs</div>
                        <div className="metric-label">SQLite Writes</div>
                        <div className="metric-sub">WAL mode enabled</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">0.44 KB</div>
                        <div className="metric-label">Memory/Agent</div>
                        <div className="metric-sub">In-memory overhead</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">0.1µs</div>
                        <div className="metric-label">Scheduler</div>
                        <div className="metric-sub">Round-robin dispatch</div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">System Requirements</h2>
                <div className="requirements-grid">
                    <div className="requirement-card">
                        <h3 className="requirement-title">Minimum</h3>
                        <ul className="requirement-list">
                            <li>Python 3.10+</li>
                            <li>8 GB RAM</li>
                            <li>4 GB disk space</li>
                            <li>Ollama with 4B model</li>
                        </ul>
                    </div>
                    <div className="requirement-card recommended">
                        <h3 className="requirement-title">Recommended</h3>
                        <ul className="requirement-list">
                            <li>Python 3.12+</li>
                            <li>16+ GB RAM (M4 Mac ideal)</li>
                            <li>20 GB disk space</li>
                            <li>Ollama with 7B-14B model</li>
                        </ul>
                    </div>
                    <div className="requirement-card">
                        <h3 className="requirement-title">For Research</h3>
                        <ul className="requirement-list">
                            <li>32+ GB RAM</li>
                            <li>14B+ parameter model</li>
                            <li>NVMe SSD</li>
                            <li>Multiple model variants</li>
                        </ul>
                    </div>
                </div>
            </section>
        </div>
    );
}