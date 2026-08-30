import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './CLI.css';

export default function CLI() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">CLI Commands</h1>
                <p className="page-subtitle">
                    Interactive terminal interface with rich formatting and agent control
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Main Commands</h2>
                <div className="command-grid">
                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/start</span>
                        </div>
                        <p className="cmd-description">
                            Begin autonomous conversation between Atlas and Argus. Agents
                            will begin their first turn, typically exploring the project
                            structure and introducing themselves.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/stop</span>
                        </div>
                        <p className="cmd-description">
                            Immediately pause all agent activity. Conversation stops at
                            the current turn boundary. State is preserved — use
                            <code>/resume</code> to continue.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/status</span>
                        </div>
                        <p className="cmd-description">
                            Show comprehensive system status including: current agent,
                            turn number, conversation state, resource usage, evidence
                            count, and system health metrics.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/tts</span>
                        </div>
                        <p className="cmd-description">
                            Toggle text-to-speech on/off. When enabled, the system will
                            read agent responses aloud using pyttsx3 (macOS/Linux) or
                            edge-tts (cross-platform).
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/help</span>
                        </div>
                        <p className="cmd-description">
                            Display all available commands with descriptions.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/inject</span>
                        </div>
                        <p className="cmd-description">
                            Send a message to the current speaking agent. This jumps
                            the queue — your message is injected as the next input, and
                            the current agent responds to it before the normal rotation
                            resumes.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/exec</span>
                        </div>
                        <p className="cmd-description">
                            Execute a terminal command in the sandbox. The command is
                            checked against the allowed commands whitelist in config.yaml.
                        </p>
                    </div>

                    <div className="command-card">
                        <div className="cmd-header">
                            <span className="cmd-name">/read</span>
                        </div>
                        <p className="cmd-description">
                            Read a file from the sandbox filesystem and display its
                            contents in the terminal panel. File must be within the
                            sandbox path.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Agent Control Commands</h2>
                <div className="agent-commands">
                    <div className="agent-command">
                        <div className="ac-name">/pause</div>
                        <p className="ac-desc">Pause the current agent's turn. The agent
                            will finish whatever it's doing, then stop. Use <code>/resume</code>
                            to continue.</p>
                    </div>
                    <div className="agent-command">
                        <div className="ac-name">/resume</div>
                        <p className="ac-desc">Resume the conversation from a paused state.
                            Agents continue from where they left off.</p>
                    </div>
                    <div className="agent-command">
                        <div className="ac-name">/emergency-stop</div>
                        <p className="ac-desc">Hard emergency stop. Immediately halts all
                            agent activity, clears pending operations, and returns the system
                            to IDLE state. Conversation history is preserved in evidence.</p>
                    </div>
                    <div className="agent-command">
                        <div className="ac-name">/approve</div>
                        <p className="ac-desc">Explicitly approve a pending permission request.
                            The agent can proceed with tool execution that requires approval.</p>
                    </div>
                    <div className="agent-command">
                        <div className="ac-name">/deny</div>
                        <p className="ac-desc">Deny a pending permission request. The agent
                            will never be granted that permission level without a new request.</p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Conversation Flow</h2>
                <p className="section-subtitle">
                    The CLI manages the conversation state machine. Here's how commands
                    interact with the system:
                </p>
                <CodeBlock title="Conversation State Machine" language="text">
{`IDLE
  │
  └── /start → THINKING (Atlas Turn 1)
          │
          └── Atlas generates response → SPEAKING
                │
                └── Response rendered → OBSERVING (human can type)
                      │
                      ├── /inject "msg" → Agent responds to injection
                      │
                      ├── /pause → Stops at turn boundary
                      │
                      └── /resume → Continue from paused state

ACTIVE
  │
  └── Normal round-robin continues:
          Atlas → Argus → Atlas → Argus → ...
                │
                ├── /stop → Pauses at boundary
                │
                └── /resume → Continues rotation

EMERGENCY
  │
  └── /emergency-stop → IDLE
          │
          └── All operations halted, state preserved in SQLite`}
</CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Command Examples</h2>
                <div className="code-examples">
                    <div className="example-card">
                        <h4 className="example-title">Start the conversation</h4>
                        <pre><code>YOU > /start
Agents are standing by.
  /start      Begin autonomous conversation
  /stop       Pause agents
  /status     System status
  /help       Show all commands

YOU > /start

🧭 ATLAS  Turn 1
│ Let me explore the project structure...
│ [TOOL:terminal:{"command": "ls"}]</code></pre>
                    </div>
                    <div className="example-card">
                        <h4 className="example-title">Inject a message mid-conversation</h4>
                        <pre><code>YOU > /inject I want to know about the memory management strategy

🧭 ATLAS  Turn 3 (redirected)
│ Based on our conversation so far and your injection, let me check...
│ [TOOL:filesystem:{"operation": "read", "path": "app/memory/context_manager.py"}]
│
│ I can see the context budget is 8192 tokens...</code></pre>
                    </div>
                    <div className="example-card">
                        <h4 className="example-title">Check system status</h4>
                        <pre><code>YOU > /status

System Status:
• Current Agent: Argus
• Turn: 12
• Status: running
• Memory: 2.3 MB / 16 GB
• Evidence: 47 entries
• WAL Mode: enabled
• Permissions: read (auto), execute (pending)</code></pre>
                    </div>
                </div>
            </section>
        </div>
    );
}