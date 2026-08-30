import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './API.css';

export default function API() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">API Reference</h1>
                <p className="page-subtitle">
                    Programmatic access to all components
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">EventBus API</h2>
                <p className="section-subtitle">
                    The central event system for inter-component communication. All internal
                    messages flow through the EventBus.
                </p>
                <CodeBlock title="Python">
                    {`from app.core.events import EventBus

bus = EventBus()

# Subscribe to an event
def on_message(event):
    print(f"Received: {event.data}")

bus.subscribe("agent.message", on_message)

# Publish an event
bus.publish("agent.message", {
    "agent": "atlas",
    "content": "Hello, world!"
})

# Subscribe with a filter
bus.subscribe(
    "agent.message",
    lambda e: e.data.get("agent") == "atlas",
    handler=on_message
)

# Unsubscribe
bus.unsubscribe("agent.message", on_message)`}
                </CodeBlock>
                <div className="api-methods">
                    <div className="method-card">
                        <div className="method-signature">
                            <code className="method-name">subscribe</code>
                            <span className="method-params">(event_type, handler, filter=None)</span>
                        </div>
                        <p className="method-desc">Register a handler for an event type. Optional filter to selectively receive events.</p>
                    </div>
                    <div className="method-card">
                        <div className="method-signature">
                            <code className="method-name">publish</code>
                            <span className="method-params">(event_type, data)</span>
                        </div>
                        <p className="method-desc">Emit an event to all subscribed handlers. Executes synchronously in registration order.</p>
                    </div>
                    <div className="method-card">
                        <div className="method-signature">
                            <code className="method-name">unsubscribe</code>
                            <span className="method-params">(event_type, handler)</span>
                        </div>
                        <p className="method-desc">Remove a previously registered handler.</p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">EvidenceManager API</h2>
                <p className="section-subtitle">
                    Manages evidence collection, verification, and storage for agent claims
                    and tool outputs.
                </p>
                <CodeBlock title="Python">
                    {`from app.memory.evidence import EvidenceManager

em = EvidenceManager(db_path="evidence.db")

# Store evidence
em.add(
    claim="Python 3.12 adds pattern matching improvements",
    source="web_fetch",
    agent="atlas",
    confidence=0.92
)

# Query evidence by topic
results = em.search("python pattern matching")

# Verify a claim against stored evidence
verification = em.verify(
    claim="Python supports pattern matching",
    threshold=0.8
)

# Get evidence summary for a conversation
summary = em.get_summary("conv_123")`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">MemoryStore API</h2>
                <p className="section-subtitle">
                    Persistent storage for agent memories, facts, and conversation history.
                </p>
                <CodeBlock title="Python">
                    {`from app.memory.store import SQLiteStore

store = SQLiteStore("sandbox.db")

# Save a memory
store.save(
    agent="argus",
    memory_type="decision",
    content="Use async/await for I/O-bound operations",
    conversation_id="conv_123",
    metadata={"context": "architecture discussion"}
)

# Retrieve recent memories
recent = store.get_recent("atlas", limit=10)

# Get memories by type
facts = store.get_by_agent("atlas", memory_type="fact")

# Get all memory types for an agent
all_memories = store.get_by_agent("atlas")

# Delete a specific memory
store.delete(memory_id="mem_456")

# Get storage statistics
stats = store.get_stats()
print(stats)  # {"total": 234, "agents": {"atlas": 89, "argus": 145}}`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">ConversationEngine API</h2>
                <p className="section-subtitle">
                    Manages the autonomous conversation loop, turn scheduling, and agent
                    coordination.
                </p>
                <CodeBlock title="Python">
                    {`from app.conversation.engine import ConversationEngine

engine = ConversationEngine(
    agents=["atlas", "argus"],
    max_turns=50,
    timeout_per_turn=30
)

# Start a conversation
engine.start(topic="What are the tradeoffs of microservices?")

# Get current state
state = engine.get_state()
print(state)  # {"turn": 5, "current_agent": "atlas", "status": "running"}

# Pause the conversation
engine.pause()

# Resume
engine.resume()

# Stop
engine.stop()

# Get conversation history
history = engine.get_history()`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">ToolGateway API</h2>
                <p className="section-subtitle">
                    Provides agents access to external tools — terminal, filesystem, and web.
                    Handles permission checks and sandboxing.
                </p>
                <CodeBlock title="Python">
                    {`from app.tools.gateway import ToolGateway

gateway = ToolGateway(
    allowed_tools=["terminal", "read_file", "web_fetch"],
    blocked_commands=["rm -rf", "sudo"]
)

# Execute a tool call
result = gateway.execute(
    tool="terminal",
    args={"command": "ls -la /tmp"},
    agent="atlas"
)

# List available tools
tools = gateway.list_tools()
print(tools)  # ["terminal", "read_file", "write_file", "web_fetch", "search"]

# Check if a command is allowed
is_allowed = gateway.is_allowed("terminal", "python script.py")

# Get tool execution history
history = gateway.get_history(agent="atlas", limit=20)`}
                </CodeBlock>
            </section>
        </div>
    );
}
