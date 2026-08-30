import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Memory.css';

export default function Memory() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Memory System</h1>
                <p className="page-subtitle">
                    How agents remember and learn
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Overview</h2>
                <p className="section-subtitle">
                    The memory system gives agents continuity across turns. It stores recent messages,
                    persistent facts, and generated summaries so each agent can reason with full
                    context of the ongoing conversation.
                </p>
            </section>

            <section className="content-section">
                <h2 className="section-title">Short-Term Memory</h2>
                <p className="section-subtitle">
                    Short-term memory holds the recent messages from the current conversation. It
                    provides immediate context for each agent turn, allowing agents to reference
                    what was just said without querying long-term storage.
                </p>
                <div className="memory-tier-card">
                    <h3 className="tier-title">Characteristics</h3>
                    <ul className="tier-list">
                        <li>In-memory ring buffer with configurable size</li>
                        <li>Includes all messages from the current session</li>
                        <li>Zero-latency access during agent turns</li>
                        <li>Automatically pruned when conversation exceeds window</li>
                    </ul>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Long-Term Memory</h2>
                <p className="section-subtitle">
                    Long-term memory persists facts, decisions, and behavioral patterns extracted
                    from conversations. It survives across sessions and grows as agents interact.
                </p>
                <div className="memory-tier-card">
                    <h3 className="tier-title">Stored Data</h3>
                    <div className="data-type-grid">
                        <div className="data-type-card">
                            <h4 className="data-type-name">Facts</h4>
                            <p className="data-type-desc">
                                Concrete information extracted from dialogue — project details,
                                technical constraints, preferences.
                            </p>
                        </div>
                        <div className="data-type-card">
                            <h4 className="data-type-name">Decisions</h4>
                            <p className="data-type-desc">
                                Choices made during conversation — architecture decisions,
                                tool selections, problem-solving approaches.
                            </p>
                        </div>
                        <div className="data-type-card">
                            <h4 className="data-type-name">Patterns</h4>
                            <p className="data-type-desc">
                                Recurring behaviors and strategies that emerge over time —
                                what works, what doesn't, preferred workflows.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Summaries</h2>
                <p className="section-subtitle">
                    When conversations grow long, the memory system generates compressed summaries
                    that capture key points while freeing space for new messages. Summaries are
                    created periodically and replace older short-term entries.
                </p>
                <CodeBlock title="Summary Generation">
                    {`# Summaries are generated automatically when
# the short-term buffer exceeds the threshold.
# Each summary captures:
#   - Key topics discussed
#   - Decisions made
#   - Action items
#   - Open questions`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">SQLiteStore API</h2>
                <p className="section-subtitle">
                    The underlying storage layer uses SQLite for persistence. The store handles
                    all read/write operations and provides atomic transactions for data integrity.
                </p>
                <CodeBlock title="Python">
                    {`from app.memory.store import SQLiteStore

store = SQLiteStore("memory.db")

# Store a memory entry
store.save(
    agent="atlas",
    memory_type="fact",
    content="The project uses FastAPI for the backend",
    conversation_id="conv_123"
)

# Retrieve memories for an agent
facts = store.get_by_agent("atlas", memory_type="fact")

# Search memories by content
results = store.search("FastAPI", limit=5)

# Get memory count per agent
counts = store.get_memory_counts()`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Context Building</h2>
                <p className="section-subtitle">
                    Before each agent turn, the system assembles context from multiple memory
                    sources. This context window is carefully constructed to give the agent
                    maximum relevant information within token limits.
                </p>
                <div className="context-flow">
                    <div className="flow-step">
                        <div className="flow-label">1. System Prompt</div>
                        <p className="flow-desc">Agent role, personality, and base instructions</p>
                    </div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">
                        <div className="flow-label">2. Long-Term Facts</div>
                        <p className="flow-desc">Relevant stored knowledge for this conversation</p>
                    </div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">
                        <div className="flow-label">3. Summaries</div>
                        <p className="flow-desc">Compressed history of earlier conversation</p>
                    </div>
                    <div className="flow-arrow">→</div>
                    <div className="flow-step">
                        <div className="flow-label">4. Recent Messages</div>
                        <p className="flow-desc">Latest short-term memory entries</p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Memory Deduplication</h2>
                <p className="section-subtitle">
                    To prevent memory bloat, the system deduplicates entries using content
                    hashing. Similar or identical memories are merged rather than stored
                    separately.
                </p>
                <CodeBlock title="Deduplication Logic">
                    {`# Before storing a new memory, the system:
# 1. Generates a content hash
# 2. Checks for existing similar entries
# 3. If a match is found, updates the
#    existing entry's timestamp and frequency
# 4. If no match, stores as a new entry

# Similarity is checked via:
#   - Exact hash match (identical content)
#   - Semantic similarity (fuzzy matching)
#   - Type-aware comparison (same category)`}
                </CodeBlock>
                <div className="dedup-metrics">
                    <div className="metric-card">
                        <div className="metric-value">~30%</div>
                        <div className="metric-label">Reduction in Storage</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-value">&lt;1ms</div>
                        <div className="metric-label">Dedup Check Time</div>
                    </div>
                </div>
            </section>
        </div>
    );
}
