import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './Config.css';

export default function Config() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Configuration</h1>
                <p className="page-subtitle">
                    Customize every aspect of AI Sandbox
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">config.yaml Reference</h2>
                <p className="section-text">
                    All configuration is defined in a single <code>config.yaml</code>
                    file at the project root. Here is the complete reference with
                    all available settings.
                </p>
                <CodeBlock title="config.yaml" language="yaml">
                    {`# ─── Model Configuration ───────────────────────────
model:
  host: "http://localhost:11434"    # Ollama API endpoint
  default: "qwen2.5-coder:7b"      # Default model for all agents
  context_window: 32768             # Max context tokens
  max_output_tokens: 4096           # Max tokens per response
  temperature: 0.7                  # Sampling temperature (0.0–2.0)
  timeout: 120                      # Request timeout in seconds

# ─── Conversation Engine ───────────────────────────
conversation:
  max_turns: 50                     # Max turns before auto-summarize
  turn_timeout_seconds: 60          # Max seconds per agent turn
  short_term_turns: 10              # Recent turns kept in full detail

# ─── Tools ─────────────────────────────────────────
tools:
  terminal:
    enabled: true                   # Allow terminal command execution
    allowed_commands:               # Whitelist of permitted commands
      - ls
      - cat
      - grep
      - python
      - git
      - pip
      - curl
  filesystem:
    enabled: true                   # Allow file read/write operations
    sandbox_path: "."               # Root directory for file access
  web:
    enabled: true                   # Allow web fetch and search
    max_fetch_size: 500000          # Max bytes per web fetch

# ─── Permissions ───────────────────────────────────
permissions:
  auto_approve:                     # Permission levels auto-approved
    - read
    - write
  require_approval:                 # Permission levels requiring user
    - execute
    - network
    - install
    - system

# ─── Audio ─────────────────────────────────────────
audio:
  tts_enabled: false                # Enable text-to-speech output
  stt_enabled: false                # Enable speech-to-text input

# ─── Resources ─────────────────────────────────────
resources:
  memory_warning_gb: 8              # Warn when RAM usage exceeds (GB)
  cpu_warning_percent: 90           # Warn when CPU usage exceeds (%)`}
                </CodeBlock>
            </section>

            <section className="content-section">
                <h2 className="section-title">Settings Breakdown</h2>

                <div className="config-group">
                    <h3 className="section-subtitle">model</h3>
                    <div className="settings-grid">
                        <div className="setting-card">
                            <code className="setting-key">host</code>
                            <span className="setting-type">string</span>
                            <p className="setting-desc">
                                URL of the Ollama API server. Defaults to localhost. Change
                                this when using a remote Ollama instance or alternative
                                provider.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">default</code>
                            <span className="setting-type">string</span>
                            <p className="setting-desc">
                                The default model name pulled via Ollama. All agents use this
                                unless overridden per-agent.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">context_window</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Maximum number of tokens the model can process in a single
                                request. Affects memory usage and conversation depth.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">max_output_tokens</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Maximum tokens the model can generate in a single response.
                                Lower values produce shorter, more focused outputs.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">temperature</code>
                            <span className="setting-type">float</span>
                            <p className="setting-desc">
                                Controls randomness. Lower values (0.1–0.3) produce more
                                deterministic output. Higher values (0.8–1.2) increase
                                creativity.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">timeout</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Seconds before a model request is abandoned. Increase for
                                larger models or slow hardware.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="config-group">
                    <h3 className="section-subtitle">conversation</h3>
                    <div className="settings-grid">
                        <div className="setting-card">
                            <code className="setting-key">max_turns</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Maximum conversation turns before automatic summarization
                                occurs. Prevents context overflow.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">turn_timeout_seconds</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Maximum time an agent has to produce a response. If exceeded,
                                the turn is skipped.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">short_term_turns</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Number of recent turns kept in full detail. Older turns are
                                summarized to save context.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="config-group">
                    <h3 className="section-subtitle">tools</h3>
                    <div className="settings-grid">
                        <div className="setting-card">
                            <code className="setting-key">terminal.enabled</code>
                            <span className="setting-type">boolean</span>
                            <p className="setting-desc">
                                Master switch for terminal tool execution. When false, no
                                shell commands can be run by agents.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">terminal.allowed_commands</code>
                            <span className="setting-type">list</span>
                            <p className="setting-desc">
                                Whitelist of shell commands agents are permitted to execute.
                                Commands not in this list are blocked.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">filesystem.sandbox_path</code>
                            <span className="setting-type">string</span>
                            <p className="setting-desc">
                                Root directory for all file operations. Agents cannot read or
                                write outside this path.
                            </p>
                        </div>
                        <div className="setting-card">
                            <code className="setting-key">web.max_fetch_size</code>
                            <span className="setting-type">integer</span>
                            <p className="setting-desc">
                                Maximum bytes returned per web fetch. Large pages are
                                truncated to this limit.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Environment Variables</h2>
                <p className="section-text">
                    Some settings can be overridden via environment variables.
                    These take precedence over config.yaml values.
                </p>
                <CodeBlock title="Shell" language="bash">
                    {`# Ollama host
export OLLAMA_HOST="http://localhost:11434"

# Default model override
export SANDBOX_MODEL="qwen2.5-coder:7b"

# Log level (debug, info, warning, error)
export SANDBOX_LOG_LEVEL="info"

# Data directory for conversations and memory
export SANDBOX_DATA_DIR="./data"`}
                </CodeBlock>
            </section>
        </div>
    );
}
