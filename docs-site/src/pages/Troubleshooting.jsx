import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Troubleshooting.css';

export default function Troubleshooting() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Troubleshooting</h1>
                <p className="page-subtitle">
                    Common issues and solutions
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Ollama Not Responding</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        Agents fail to generate responses. Logs show connection refused errors
                        to localhost:11434.
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="Terminal">
                            {`# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Verify the model is available
ollama list

# Pull the model if missing
ollama pull qwen2.5-coder:7b`}
                        </CodeBlock>
                        <p className="solution-note">
                            Ensure Ollama is running before starting AI Sandbox. The system
                            polls Ollama on startup and will wait up to 10 seconds.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Agent Timeout</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        An agent stops responding mid-conversation. Logs show "Turn timeout
                        after 30s".
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="config.json">
                            {`{
  "agent_timeout": 60,
  "max_tokens_per_turn": 2048
}`}
                        </CodeBlock>
                        <p className="solution-note">
                            Increase the timeout for complex tasks, or reduce max_tokens to
                            generate shorter responses. Large models on CPU may need 60-120s.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Terminal Commands Blocked</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        Agent tries to run a terminal command but receives "Command blocked
                        by policy" error.
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="config.json">
                            {`{
  "tool_permissions": {
    "terminal": {
      "enabled": true,
      "blocked_commands": ["rm -rf /", "sudo", "shutdown"],
      "allowed_patterns": ["ls", "cat", "python", "pip"]
    }
  }
}`}
                        </CodeBlock>
                        <p className="solution-note">
                            Commands are filtered against blocked_patterns before execution.
                            Review your security config to allow needed commands.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">TTS Not Working</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        Text-to-speech output is silent. No error messages appear.
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="Terminal">
                            {`# Check system audio
# macOS: System Preferences > Sound > Output
# Linux: pactl list sinks short

# Test TTS directly
python -c "from app.tts import speak; speak('test')"

# Install dependencies if missing
pip install pyttsx3

# For macOS, ensure 'say' command works
say "hello"`}
                        </CodeBlock>
                        <p className="solution-note">
                            TTS requires a working audio output device. On headless systems,
                            TTS is automatically disabled.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Database Locked</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        Errors containing "database is locked" or "SQLITE_BUSY" during
                        conversation.
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="Terminal">
                            {`# Check for stale database connections
lsof sandbox.db

# Remove stale lock files
rm -f sandbox.db-wal sandbox.db-shm

# Verify WAL mode is enabled
python -c "
import sqlite3
conn = sqlite3.connect('sandbox.db')
print(conn.execute('PRAGMA journal_mode').fetchone())
conn.close()
"`}
                        </CodeBlock>
                        <p className="solution-note">
                            This usually happens after an improper shutdown. The WAL journal
                            file needs to be cleaned up. Restarting Ollama and the sandbox
                            resolves most cases.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Memory Issues</h2>
                <div className="issue-card">
                    <div className="issue-symptom">
                        <span className="issue-label">Symptom</span>
                        System becomes sluggish or runs out of memory during long conversations.
                    </div>
                    <div className="issue-solution">
                        <span className="solution-label">Solution</span>
                        <CodeBlock title="config.json">
                            {`{
  "memory": {
    "short_term_window": 20,
    "max_long_term_per_agent": 500,
    "summary_interval": 10,
    "dedup_enabled": true
  }
}`}
                        </CodeBlock>
                        <p className="solution-note">
                            Reduce short_term_window and summary_interval for long conversations.
                            Enable deduplication to prevent memory bloat.
                        </p>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Error Codes Reference</h2>
                <div className="error-table-wrapper">
                    <table className="error-table">
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Meaning</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>E_OLLAMA_CONN</code></td>
                                <td>Cannot connect to Ollama</td>
                                <td>Start Ollama with <code>ollama serve</code></td>
                            </tr>
                            <tr>
                                <td><code>E_AGENT_TIMEOUT</code></td>
                                <td>Agent exceeded time limit</td>
                                <td>Increase timeout or reduce context size</td>
                            </tr>
                            <tr>
                                <td><code>E_TOOL_DENIED</code></td>
                                <td>Tool call blocked by policy</td>
                                <td>Update tool_permissions in config</td>
                            </tr>
                            <tr>
                                <td><code>E_DB_LOCKED</code></td>
                                <td>SQLite database is locked</td>
                                <td>Remove WAL files and restart</td>
                            </tr>
                            <tr>
                                <td><code>E_MEMORY_FULL</code></td>
                                <td>Memory limit exceeded</td>
                                <td>Increase limit or enable dedup</td>
                            </tr>
                            <tr>
                                <td><code>E_CONTEXT_OVERFLOW</code></td>
                                <td>Context exceeds token limit</td>
                                <td>Reduce context window or trim history</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
}
