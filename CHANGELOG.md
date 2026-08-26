# Changelog

## 2026-08-26

### Added
- Complete 9-phase core architecture implementation
- Event Bus with 20+ event types
- Model Plane with Ollama adapter (streaming, health checks)
- Agent Plane: Explorer, Challenger, Observer agents
- Control Plane: Conversation Engine, RoundRobin/Adaptive schedulers, State Machine
- Audio Plane: TTS (pyttsx3, edge-tts) and STT (faster-whisper with VAD)
- Memory Plane: SQLite store, summarization, context builder
- Tool Plane: Terminal, Filesystem, Web with permission gating
- Permission System: 6 levels (READ, WRITE, EXECUTE, NETWORK, INSTALL, SYSTEM)
- Resource Manager: RAM/CPU/latency monitoring with warning/critical callbacks
- Autonomous Environment: Proposal-driven exploration sessions
- A2A Protocol: Agent cards, task requests, peer discovery

### Evidence Plane Addon
- Evidence Manager: Centralized event-to-evidence recording
- Session Manager: Lifecycle, recovery, metadata persistence
- Research Manager: Browser research with caching, provenance, duplicate detection
- Decision Manager: Structured decision recording with evidence linkage
- Artifact Manager: File artifacts with session/experiment/research linkage
- Report Generator: Final session reports with timeline

### CLI-First Interface Addon
- CLI commands: start, watch, interactive, status, sessions, session, memory, research, evidence, experiments, permissions, approve, deny, tools, resources, logs, timeline, report, modifications, rollback, inject, help
- Interactive mode with live agent conversation display
- Rich terminal UI with tables, panels, colors
- Session recovery command support

### Self-Modification Addon
- SelfModificationEngine with Git worktree isolation
- Modification lifecycle: PROPOSED → ISOLATED → TESTING → BENCHMARKING → EVALUATING → APPROVED → APPLIED
- Automatic baseline benchmarks and A/B comparison
- Human approval required for HIGH/CRITICAL risk modifications
- Automatic rollback on failure
- Core safety file protection

### SQLite Database Addon
- Unified schema with 18+ tables
- Migrations support
- WAL mode for concurrent access
- Backup/restore support
- CLI database inspection commands

### Agent-Driven Orchestration Addon
- CapabilityRegistry with model/tool/agent capabilities
- Agent-driven capability requests
- Permission and resource gates
- Routing history and performance stats
- Default capabilities for Qwen3, DeepSeek, Dolphin models

### GitHub Engineering Addon
- Structured commit messages
- Branch naming conventions
- Protected operations
- PR templates for self-modification

## Changed
- Unified SQLite schema replaces separate memory/evidence databases
- Evidence Manager now central persistence layer
- Session Manager handles lifecycle and recovery
- CLI is primary interface (web UI deferred to future)

## Fixed
- Ollama streaming timeout handling
- State machine transition validation
- SQL binding parameter counts
- Resource manager shutdown ordering

## Performance
- Sequential inference for M4 16GB optimization
- Resource monitoring <1% CPU overhead
- SQLite write latency <5ms
- Session recovery <2 seconds

## Documentation
- Created PROJECT_STATE.md, CHANGELOG.md, DECISIONS.md, KNOWN_ISSUES.md, IMPLEMENTATION_LOG.md