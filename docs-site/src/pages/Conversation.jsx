import React from 'react';
import CodeBlock from '../components/CodeBlock';

export default function Conversation() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Conversation Engine</h1>
                <p className="page-subtitle">
                    Managing autonomous multi-agent dialogue
                </p>
            </div>

            <section className="doc-section">
                <h2>State Machine</h2>
                <p>
                    The conversation engine is driven by a state machine that enforces valid
                    transitions between phases of each turn. Only one state is active at a time,
                    and transitions follow a strict flow.
                </p>

                <div className="state-flow">
                    <div className="state-node">IDLE</div>
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
                    <div className="state-arrow">↻</div>
                    <div className="state-node">THINKING</div>
                </div>

                <h3>State Descriptions</h3>
                <ul>
                    <li><strong>IDLE</strong> — No conversation is active. Entry point before start or after shutdown.</li>
                    <li><strong>THINKING</strong> — Building context for the current speaker. Gathering recent messages, memory summary, and available tools.</li>
                    <li><strong>GENERATING</strong> — The agent's model is producing a response. Tool calls in the response are parsed and executed here.</li>
                    <li><strong>SPEAKING</strong> — The response is recorded, emitted to the event bus, and appended to message history.</li>
                    <li><strong>OBSERVING</strong> — Post-turn observation. The system records evidence and checks for emergence patterns.</li>
                    <li><strong>NEXT_TURN</strong> — The scheduler selects the next speaker and the cycle loops back to THINKING.</li>
                </ul>

                <h3>Additional States</h3>
                <ul>
                    <li><strong>PAUSED</strong> — Conversation is suspended. Resumes from the state it was in before pausing.</li>
                    <li><strong>PROCESS_HUMAN_INPUT</strong> — An interrupt has occurred and the engine is waiting for human input before resuming.</li>
                    <li><strong>GRACEFUL_SHUTDOWN</strong> — Terminal state. No transitions out. The engine finishes the current turn and stops.</li>
                </ul>

                <h3>Allowed Transitions</h3>
                <CodeBlock title="State transition rules" language="text">
{`IDLE          → THINKING, GRACEFUL_SHUTDOWN
THINKING      → GENERATING, PAUSED, GRACEFUL_SHUTDOWN
GENERATING    → SPEAKING, PAUSED, GRACEFUL_SHUTDOWN
SPEAKING      → OBSERVING, PAUSED, GRACEFUL_SHUTDOWN
OBSERVING     → NEXT_TURN, PAUSED, GRACEFUL_SHUTDOWN
NEXT_TURN     → THINKING, IDLE, PAUSED, GRACEFUL_SHUTDOWN
PAUSED        → PROCESS_HUMAN_INPUT, THINKING, GRACEFUL_SHUTDOWN
PROCESS_HUMAN_INPUT → THINKING, IDLE, GRACEFUL_SHUTDOWN`}
                </CodeBlock>
            </section>

            <section className="doc-section">
                <h2>Sequential Inference</h2>
                <p>
                    Only <strong>one agent speaks at a time</strong>. This is a deliberate
                    design choice driven by M4 hardware constraints — running two concurrent
                    LLM inferences on 16 GB of unified memory is not practical.
                </p>

                <h3>Why Sequential?</h3>
                <ul>
                    <li>Each agent inference uses ~800 MB of memory for the model weights</li>
                    <li>Concurrent inference would risk memory pressure and swap thrashing</li>
                    <li>Sequential execution allows the context manager to summarize between turns</li>
                    <li>Tool execution (terminal, filesystem, web) happens during the GENERATING state and is also serial</li>
                </ul>

                <h3>Turn Flow</h3>
                <CodeBlock title="Sequential turn execution" language="text">
{`Turn 1:  Atlas thinks → generates → speaks → observe → schedule next
Turn 2:  Argus thinks → generates → speaks → observe → schedule next
Turn 3:  Atlas thinks → generates → speaks → observe → schedule next
...`}
                </CodeBlock>

                <p>
                    The scheduler determines the order. With round-robin (default), agents alternate
                    strictly. With adaptive policy, the agent with fewer turns gets priority.
                </p>
            </section>

            <section className="doc-section">
                <h2>Human Intervention</h2>
                <p>
                    A human can interrupt the conversation at any time. The engine transitions
                    to <code>PROCESS_HUMAN_INPUT</code>, pauses the agent loop, and waits for
                    the human message.
                </p>

                <h3>How It Works</h3>
                <ul>
                    <li><strong>Interrupt</strong> — The engine saves the current state and transitions to PROCESS_HUMAN_INPUT</li>
                    <li><strong>Inject message</strong> — The human's message is added to the message history with <code>agent_id: "human"</code></li>
                    <li><strong>Resume</strong> — The engine transitions back to THINKING and the next agent sees the human message in context</li>
                </ul>

                <CodeBlock title="Human intervention API" language="python">
{`# Pause the conversation
await engine.pause()

# Inject a human message
await engine.inject_human_message("Can you focus on the memory issue?")

# Resume
await engine.resume()`}
                </CodeBlock>

                <p>
                    The human message appears in the next agent's context just like any other message,
                    prefixed with <code>[human]</code>. Agents see it and can respond to it.
                </p>
            </section>

            <section className="doc-section">
                <h2>Context Management</h2>
                <p>
                    Each agent needs context to generate a meaningful response. The context is
                    built by the <strong>ContextManager</strong>, which assembles recent messages,
                    conversation summaries, important facts, and open questions into a structured
                    prompt.
                </p>

                <h3>Context Components</h3>
                <ul>
                    <li><strong>Recent messages</strong> — The last N turns (default: 8), giving the agent immediate conversational context</li>
                    <li><strong>Memory summary</strong> — A compressed summary of earlier turns, generated every 10 turns by the summarizer</li>
                    <li><strong>Important facts</strong> — Key facts extracted and stored as memory entries</li>
                    <li><strong>Open questions</strong> — Unresolved questions tracked across the conversation</li>
                    <li><strong>Current topic</strong> — The topic extracted from the latest summary</li>
                </ul>

                <h3>Context Budget</h3>
                <p>
                    Context is constrained by a token budget (default: 8192 tokens). This budget
                    adjusts based on system resource state:
                </p>

                <CodeBlock title="Budget adjustments by resource state" language="text">
{`GREEN  → 8192 tokens (full budget)
YELLOW → 6963 tokens (85% — moderate pressure)
ORANGE → 5734 tokens (70% — high pressure)
RED    → 0 tokens    (critical — context generation paused)`}
                </CodeBlock>

                <h3>Message Construction</h3>
                <p>
                    The agent receives messages in this order:
                </p>
                <ol>
                    <li>System prompt (agent identity, tools, rules)</li>
                    <li>Memory summary (compressed history)</li>
                    <li>Available tools list</li>
                    <li>Recent messages as <code>[identity] content</code> pairs</li>
                    <li>If no history: a seed message prompting the agent to start</li>
                </ol>

                <CodeBlock title="Context assembly" language="python">
{`def _build_context(self, speaker_id: str) -> AgentContext:
    recent = self._message_history[-self.config.short_term_turns:]
    memory_summary = self.context_manager.get_context_for_llm()

    return AgentContext(
        conversation_id=self.conversation_id,
        turn_number=self.turn_number,
        recent_messages=recent,
        memory_summary=memory_summary,
        available_tools=[],
        pending_permissions=[]
    )`}
                </CodeBlock>
            </section>

            <section className="doc-section">
                <h2>Turn Management</h2>
                <p>
                    The <strong>Scheduler</strong> controls which agent speaks and when. It supports
                    two policies and tracks turn numbers.
                </p>

                <h3>Scheduling Policies</h3>

                <CodeBlock title="Round Robin (default)" language="text">
{`Agents: [atlas, argus]
Turn 1: atlas
Turn 2: argus
Turn 3: atlas
Turn 4: argus
...`}
                </CodeBlock>

                <CodeBlock title="Adaptive" language="text">
{`Agents: [atlas, argus]
Turn 1: atlas  (atlas: 1, argus: 0)
Turn 2: argus  (atlas: 1, argus: 1 — tied, pick non-current)
Turn 3: atlas  (atlas: 1, argus: 1 — tied, pick non-current)
...`}
                </CodeBlock>

                <h3>Lifecycle</h3>
                <ul>
                    <li><strong>start(initial_speaker)</strong> — Sets turn 1 and the first speaker</li>
                    <li><strong>next_turn()</strong> — Increments turn counter, selects next speaker via policy</li>
                    <li><strong>get_next_speaker()</strong> — Preview who would speak next without advancing</li>
                    <li><strong>reset()</strong> — Returns scheduler to initial state</li>
                </ul>

                <h3>Configuration</h3>
                <CodeBlock title="Conversation config" language="python">
{`ConversationConfig(
    max_turns=1000,            # Stop after this many turns
    turn_timeout_seconds=120,  # Agent has 120s to respond
    short_term_turns=8,        # Recent messages in context
    initial_speaker="agent_a", # Who speaks first
    scheduler_policy="round_robin"
)`}
                </CodeBlock>
            </section>
        </div>
    );
}
