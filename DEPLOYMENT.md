# AI Sandbox - Deployment Guide

## 1. Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.14+ | 3.14+ |
| Ollama | Latest | Latest |
| RAM | 16 GB | 32 GB |
| Disk | 5 GB free | 10 GB free (for models) |
| OS | Linux / macOS | macOS |

Install Ollama: https://ollama.com

```bash
# Verify Ollama is running
ollama --version
curl http://localhost:11434/api/tags
```

## 2. Quick Start

```bash
cd ai-sandbox

python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt

ollama pull qwen2.5-coder:7b

python -m app start
```

## 3. Configuration

All settings are in `config.yaml`. Key sections:

```yaml
model:
  host: "http://localhost:11434"    # Ollama endpoint
  default: "qwen2.5-coder:7b"      # Primary model
  context_window: 4096              # Max context tokens
  max_output_tokens: 512            # Max response length
  temperature: 0.7                  # Creativity (0.0-1.0)
  timeout: 300                      # Request timeout (seconds)

conversation:
  max_turns: 1000                   # Max conversation turns
  turn_timeout_seconds: 180         # Per-turn timeout
  short_term_turns: 8               # Recent messages to keep
  summarization_interval: 10        # Summarize every N turns

resources:
  memory_warning_gb: 12             # RAM warning threshold
  memory_critical_gb: 14            # RAM critical (pauses conversation)
  cpu_warning_percent: 80
  cpu_critical_percent: 95

audio:
  tts_enabled: false                # Enable text-to-speech
  stt_enabled: false                # Enable speech-to-text

autonomy:
  enabled: false                    # Enable autonomous exploration
  auto_accept_proposals: false      # Auto-accept exploration proposals
```

## 4. Running

### Start (interactive mode)

```bash
python -m app start
```

### Start (watch mode - no input)

```bash
python -m app watch
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/start` | Begin autonomous conversation |
| `/stop` | Pause agents |
| `/resume` | Resume agents |
| `/status` | System status and metrics |
| `/memory` | View memory state |
| `/tools` | List available tools |
| `/resources` | RAM/CPU/latency usage |
| `/evidence` | View evidence trail |
| `/sessions` | List past sessions |
| `/report` | Generate session report |
| `/logs` | View recent logs |
| `/tts` | Toggle text-to-speech |
| `/help` | Show all commands |
| `<text>` | Send message to agents (no prefix) |

### Run Benchmarks

```bash
python -m app.benchmarks
```

## 5. Tools Setup

### Terminal

Edit `config.yaml` under `tools.terminal`:

```yaml
tools:
  terminal:
    enabled: true
    permission: "execute"
    risk: "high"
    allowed_commands:
      - "ls"
      - "cat"
      - "pwd"
      - "echo"
      - "python"
      - "pip"
      - "git"
      - "node"
      - "npm"
      - "curl"
      - "mkdir"
      - "cp"
      - "mv"
      - "touch"
```

Blocked by default: `rm -rf /`, `sudo`, `shutdown`, `reboot`, `mkfs`, `chmod 777`, etc.

### Filesystem

```yaml
  filesystem:
    enabled: true
    permission: "write"
    risk: "medium"
    # base_path defaults to cwd
    # max_file_size: 10MB
    # Allowed: .txt, .md, .py, .js, .ts, .json, .yaml, etc.
    # Blocked: /etc, /var, /usr, /bin, /boot, /sys, /proc, ~/.ssh
```

### Web Access

```yaml
  web:
    enabled: true
    permission: "network"
    risk: "medium"
    # timeout: 30s
    # max_response_size: 1MB
    # Blocked: localhost, 127.0.0.1, cloud metadata endpoints
```

## 6. TTS Setup

TTS is optional. Two backends are supported:

### Option A: pyttsx3 (offline, local)

```bash
pip install pyttsx3
```

On macOS, uses the built-in speech synthesizer. On Linux, requires `espeak`:

```bash
# Ubuntu/Debian
sudo apt install espeak
```

### Option B: edge-tts (Microsoft Edge voices, requires network)

```bash
pip install edge-tts
```

### Enable in config

```yaml
audio:
  tts_enabled: true
  tts_voice: "en-US-AriaNeural"   # for edge-tts
  stt_enabled: false               # requires faster-whisper, pyaudio
```

## 7. Database

### Locations

| Database | Path | Purpose |
|----------|------|---------|
| Memory | `./data/memory.db` | Conversations, summaries, memory entries |
| Evidence | `./data/sandbox.db` | Evidence, sessions, experiments, modifications |

### SQLite WAL Mode

WAL mode is enabled for concurrent reads. Benchmarks confirm 1000 writes complete in <10s.

### Backup

```bash
cp ./data/memory.db ./data/memory.db.backup
cp ./data/sandbox.db ./data/sandbox.db.backup
```

For live backups:

```bash
sqlite3 ./data/memory.db ".backup './data/memory-backup.db'"
```

### Schema Migrations

The app runs migrations automatically on startup via `app.db.migrations`. Current schema version: 1 (evidence, sources, claims, research, experiments, decisions, artifacts, modifications, sessions, resource_metrics).

## 8. Performance

Run benchmarks to verify your setup:

```bash
python -m app.benchmarks
```

Expected results (1000 iterations):

| Benchmark | Threshold |
|-----------|-----------|
| EventBus pub/sub | < 30s |
| SQLite writes | < 10s |
| ContextManager update | < 30s |
| Scheduler (round_robin) | < 1s |
| Scheduler (adaptive) | < 1s |
| Memory per agent (100 agents) | < 50 KB/agent |

### Resource Limits

The `ResourceManager` monitors RAM/CPU every 5 seconds. When critical thresholds are hit, the conversation is automatically paused. Adjust in `config.yaml` under `resources`.

## 9. Troubleshooting

### Ollama not responding

```
Error: Ollama API error 404
```

Fix: Ensure Ollama is running and the model is pulled:

```bash
ollama pull qwen2.5-coder:7b
curl http://localhost:11434/api/tags
```

### Out of memory

```
Resource CRITICAL: RAM=14.2GB
```

Fix: Use a smaller model (`qwen2.5-coder:3b`), reduce `context_window` in config, or increase `memory_critical_gb`.

### No TTS output

Fix: Install a TTS backend and enable in config:

```bash
pip install pyttsx3   # or: pip install edge-tts
```

Then set `audio.tts_enabled: true` in `config.yaml`.

### Permission denied on terminal commands

Fix: Add the command to `tools.terminal.allowed_commands` in `config.yaml`. The tool denies by default if the list is empty.

### Database locked

Fix: Ensure no other process is writing to the same `.db` file. WAL mode handles concurrent reads, but only one writer at a time.

### Import errors

```
ModuleNotFoundError: No module named 'app'
```

Fix: Run from the `ai-sandbox` directory with the venv activated:

```bash
cd ai-sandbox
source .venv/bin/activate
python -m app start
```

### PyAudio install fails

PyAudio is only needed for STT. Install system deps first:

```bash
# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt install portaudio19-dev python3-pyaudio
```

## 10. Architecture

```
ai-sandbox/
├── app/
│   ├── __main__.py              # Entry point
│   ├── main.py                  # SandboxApp - orchestrator
│   ├── cli/main.py              # CLI (click + rich)
│   ├── models/                  # LLM adapters (Ollama)
│   │   ├── base.py              # ModelAdapter interface
│   │   └── ollama.py            # Ollama HTTP client
│   ├── agents/                  # Agent definitions
│   │   ├── explorer.py          # Agent A - explores ideas
│   │   ├── challenger.py        # Agent B - challenges reasoning
│   │   └── observer.py          # Agent C - monitors conversation
│   ├── orchestration/           # Turn management
│   │   ├── conversation.py      # ConversationEngine
│   │   └── scheduler.py         # Round-robin / adaptive scheduling
│   ├── events/bus.py            # Async event bus (pub/sub)
│   ├── memory/                  # Context and memory
│   │   ├── store.py             # SQLite persistence
│   │   ├── context_manager.py   # Context window management
│   │   └── summarizer.py        # LLM-powered summarization
│   ├── tools/                   # Tool integrations
│   │   ├── gateway.py           # Tool registry + execution
│   │   ├── terminal.py          # Shell command execution
│   │   ├── filesystem.py        # File read/write/list
│   │   └── web.py               # HTTP fetch, search, extract
│   ├── permissions/             # Permission system
│   ├── resources/               # RAM/CPU/latency monitoring
│   ├── evidence/                # Action audit trail
│   ├── sessions/                # Session lifecycle
│   ├── autonomy/                # Autonomous exploration
│   ├── a2a/                     # Agent-to-Agent protocol
│   ├── self_modification/       # Code self-modification
│   ├── db/migrations.py         # Schema versioning
│   └── audio/                   # TTS/STT adapters
├── tests/                       # Test suite
├── data/                        # Databases (auto-created)
├── logs/                        # Application logs
└── config.yaml                  # Configuration
```

**Data flow:** CLI -> SandboxApp -> ConversationEngine -> Scheduler -> Agent (via EventBus) -> ToolGateway -> Tools. Memory and evidence are persisted to SQLite after each turn.
