from __future__ import annotations

import asyncio
import logging
import signal
import sys
import uuid
from pathlib import Path
from typing import Optional

import yaml

from app.events.bus import EventBus, EventType, get_event_bus, set_event_bus
from app.events.schemas import AgentRole, PermissionLevel, RiskLevel
from app.models.base import get_model_registry
from app.models.ollama import create_ollama_adapter, OllamaAdapter
from app.models.base import ModelConfig
from app.agents.explorer import create_explorer_agent
from app.agents.challenger import create_challenger_agent
from app.agents.observer import create_observer_agent
from app.orchestration.conversation import ConversationEngine, ConversationConfig
from app.orchestration.scheduler import create_scheduler
from app.audio import TTSConfig, STTConfig, create_tts_adapter, create_stt_adapter
from app.memory import SQLiteStore, MemorySummarizer, MemoryManager
from app.tools import ToolGateway, TerminalTool, FilesystemTool, WebTool
from app.permissions import PermissionManager
from app.resources import ResourceManager, ResourceThresholds, ResourceLevel
from app.autonomy import AutonomousEnvironment
from app.a2a import A2AProtocol, AgentCard, A2AMessageType
from app.evidence import EvidenceManager, get_evidence_manager
from app.sessions import SessionManager, SessionConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SandboxApp:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.event_bus = EventBus()
        set_event_bus(self.event_bus)
        self.model_registry = get_model_registry()
        self.conversation_engine: Optional[ConversationEngine] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.permission_manager: Optional[PermissionManager] = None
        self.resource_manager: Optional[ResourceManager] = None
        self.tool_gateway: Optional[ToolGateway] = None
        self.autonomous_env: Optional[AutonomousEnvironment] = None
        self.a2a_protocol: Optional[A2AProtocol] = None
        self.evidence_manager: Optional[EvidenceManager] = None
        self.session_manager: Optional[SessionManager] = None
        self._shutdown_event = asyncio.Event()
        self._tts = None
        self._stt = None
        self._stt_task: Optional[asyncio.Task] = None
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}
    
    async def initialize(self) -> None:
        logger.info("Initializing AI Sandbox...")
        
        model_config = self.config.get("model", {})
        host = model_config.get("host", "http://localhost:11434")
        default_model = model_config.get("default", "hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M")
        
        adapter = await create_ollama_adapter(
            ModelConfig(
                name=default_model,
                context_window=model_config.get("context_window", 4096),
                max_output_tokens=model_config.get("max_output_tokens", 1024),
                temperature=model_config.get("temperature", 0.7),
                timeout_seconds=model_config.get("timeout", 120)
            ),
            host
        )
        
        self.model_registry.register(default_model, adapter, is_default=True)
        
        observer_model = model_config.get("observer", default_model)
        if observer_model != default_model:
            obs_adapter = await create_ollama_adapter(
                ModelConfig(name=observer_model),
                host
            )
            self.model_registry.register(observer_model, obs_adapter)
        
        logger.info("Models initialized")
        
        memory_config = self.config.get("memory", {})
        db_path = memory_config.get("db_path", "./data/memory.db")
        max_entries = memory_config.get("max_entries", 1000)
        summarization_interval = memory_config.get("summarization_interval", 10)
        
        store = SQLiteStore(db_path)
        summarizer = MemorySummarizer(store, self.model_registry.get(default_model))
        summarizer.set_interval(summarization_interval)
        self.memory_manager = MemoryManager(store, summarizer, self.event_bus, max_entries)
        
        permissions_config = self.config.get("permissions", {})
        self.permission_manager = PermissionManager(
            self.event_bus,
            timeout_seconds=permissions_config.get("timeout_seconds", 30),
            auto_approve_low_risk=permissions_config.get("auto_approve_low_risk", False)
        )
        
        resources_config = self.config.get("resources", {})
        self.resource_manager = ResourceManager(
            self.event_bus,
            ResourceThresholds(
                memory_warning_gb=resources_config.get("memory_warning_gb", 12.0),
                memory_critical_gb=resources_config.get("memory_critical_gb", 14.0),
                cpu_warning_percent=resources_config.get("cpu_warning_percent", 80.0),
                cpu_critical_percent=resources_config.get("cpu_critical_percent", 95.0),
                latency_warning_ms=resources_config.get("generation_latency_warning_ms", 5000.0),
                check_interval_seconds=resources_config.get("check_interval_seconds", 5.0)
            )
        )
        
        self.resource_manager.add_callback(ResourceLevel.WARNING, self._on_resource_warning)
        self.resource_manager.add_callback(ResourceLevel.CRITICAL, self._on_resource_critical)
        
        autonomy_config = self.config.get("autonomy", {})
        self.autonomous_env = AutonomousEnvironment(
            self.event_bus,
            self.memory_manager,
            self.tool_gateway
        )
        
        async def proposal_handler(proposal):
            return autonomy_config.get("auto_accept_proposals", False)
        
        self.autonomous_env.set_proposal_handler(proposal_handler)
        
        if autonomy_config.get("enabled", False):
            self.autonomous_env.enable()
        
        a2a_config = self.config.get("a2a", {})
        self.a2a_protocol = A2AProtocol(self.event_bus)
        
        if a2a_config.get("enabled", False):
            self.agent_card = AgentCard(
                agent_id=a2a_config.get("agent_id", "sandbox-agent"),
                name=a2a_config.get("name", "AI Sandbox Agent"),
                description=a2a_config.get("description", "Autonomous multi-agent sandbox"),
                capabilities=a2a_config.get("capabilities", ["chat", "tools", "exploration"]),
                endpoint=a2a_config.get("endpoint", "http://localhost:8080")
            )
            self.a2a_protocol.agent_card = self.agent_card
            logger.info("A2A Protocol initialized")
        
        self.evidence_manager = EvidenceManager(
            db_path="./data/sandbox.db",
            event_bus=self.event_bus,
            artifacts_dir="./data/artifacts"
        )
        
        self.session_manager = SessionManager(
            db_path="./data/sandbox.db",
            event_bus=self.event_bus,
            evidence_manager=self.evidence_manager
        )
        
        audio_config = self.config.get("audio", {})
        tts_enabled = audio_config.get("tts_enabled", False)
        stt_enabled = audio_config.get("stt_enabled", False)
        
        if tts_enabled:
            tts_config = TTSConfig(
                model=audio_config.get("tts_model", "tts_models/en/ljspeech/tacotron2-DDC"),
                voice=audio_config.get("tts_voice", "default"),
                speed=audio_config.get("tts_speed", 1.0)
            )
            self._tts = create_tts_adapter(tts_config, enabled=True)
            logger.info("TTS initialized")
        
        if stt_enabled:
            stt_config = STTConfig(
                model=audio_config.get("stt_model", "base"),
                language=audio_config.get("stt_language", "en"),
                vad_threshold=audio_config.get("vad_threshold", 0.5)
            )
            self._stt = create_stt_adapter(stt_config, enabled=True)
            logger.info("STT initialized")
        
        tools_config = self.config.get("tools", {})
        
        self.tool_gateway = ToolGateway(self.event_bus)
        
        if tools_config.get("terminal", {}).get("enabled", True):
            terminal = TerminalTool(
                timeout=tools_config.get("terminal", {}).get("timeout", 30),
                working_dir=tools_config.get("terminal", {}).get("working_dir"),
                allowed_commands=tools_config.get("terminal", {}).get("allowed_commands"),
                blocked_commands=tools_config.get("terminal", {}).get("blocked_commands")
            )
            self.tool_gateway.register(terminal)
        
        if tools_config.get("filesystem", {}).get("enabled", True):
            fs = FilesystemTool(
                base_path=tools_config.get("filesystem", {}).get("base_path"),
                max_file_size=tools_config.get("filesystem", {}).get("max_file_size", 10 * 1024 * 1024),
                allowed_extensions=tools_config.get("filesystem", {}).get("allowed_extensions"),
                blocked_paths=tools_config.get("filesystem", {}).get("blocked_paths")
            )
            self.tool_gateway.register(fs)
        
        if tools_config.get("web", {}).get("enabled", True):
            web = WebTool(
                timeout=tools_config.get("web", {}).get("timeout", 30),
                max_response_size=tools_config.get("web", {}).get("max_response_size", 1024 * 1024),
                allowed_domains=tools_config.get("web", {}).get("allowed_domains"),
                blocked_domains=tools_config.get("web", {}).get("blocked_domains")
            )
            self.tool_gateway.register(web)
        
        async def permission_checker(agent_id: str, perm: PermissionLevel, risk: RiskLevel) -> bool:
            if risk == RiskLevel.LOW:
                return True
            
            return await self.permission_manager.request_permission(
                agent_id=agent_id,
                action=f"Use tool requiring {perm.value}",
                command=f"Tool permission: {perm.value} / {risk.value}",
                reason=f"Tool requires {perm.value} permission with {risk.value} risk",
                risk=risk,
                scope=perm
            )
        
        self.tool_gateway.set_permission_checker(permission_checker)
        
        agent_a = create_explorer_agent("agent_a", default_model)
        agent_b = create_challenger_agent("agent_b", default_model)
        agent_c = create_observer_agent("agent_c", observer_model)
        
        agents = {
            "agent_a": agent_a,
            "agent_b": agent_b,
            "agent_c": agent_c
        }
        
        conv_config = self.config.get("conversation", {})
        conversation_config = ConversationConfig(
            conversation_id=str(uuid.uuid4()),
            max_turns=conv_config.get("max_turns", 1000),
            turn_timeout_seconds=conv_config.get("turn_timeout_seconds", 120),
            short_term_turns=conv_config.get("short_term_turns", 8),
            initial_speaker=conv_config.get("initial_speaker", "agent_a"),
            scheduler_policy=conv_config.get("scheduler_policy", "round_robin")
        )
        
        self.memory_manager.set_conversation(conversation_config.conversation_id)
        
        self.conversation_engine = ConversationEngine(
            config=conversation_config,
            agents=agents,
            event_bus=self.event_bus,
            memory_manager=self.memory_manager
        )
        
        self.conversation_engine.add_turn_callback(self._on_turn)
        self.conversation_engine.add_interrupt_callback(self._on_interrupt)
        self.conversation_engine.add_turn_callback(self._on_turn_autonomy)
        
        self._setup_tool_integration()
        self._setup_event_logging()
        self._setup_audio_integration()
        
        logger.info("AI Sandbox initialized successfully")
    
    def _setup_audio_integration(self) -> None:
        if self._tts:
            async def on_agent_message(event):
                if event.type == EventType.AGENT_MESSAGE:
                    content = event.payload.get("content", "")
                    if content and not content.startswith("["):
                        await self._tts.speak(content)
            
            self.event_bus.subscribe(EventType.AGENT_MESSAGE, on_agent_message)
        
        if self._stt:
            async def on_transcription(result):
                if result.text.strip() and result.is_final:
                    print(f"\n[HUMAN] {result.text}")
                    await self.conversation_engine.interrupt()
                    await self.conversation_engine.inject_human_message(result.text)
            
            self._stt_task = asyncio.create_task(self._stt.start_listening(on_transcription))
    
    def _setup_tool_integration(self) -> None:
        async def on_tool_request(event):
            if event.type == EventType.TOOL_REQUEST:
                call_id = event.payload.get("call_id")
                tool_name = event.payload.get("tool_name")
                arguments = event.payload.get("arguments", {})
                agent_id = event.payload.get("agent_id")
                
                if not all([call_id, tool_name, agent_id]):
                    return
                
                from app.events.schemas import ToolCall
                call = ToolCall(
                    call_id=call_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    agent_id=agent_id
                )
                
                result = await self.tool_gateway.execute(call)
        
        self.event_bus.subscribe(EventType.TOOL_REQUEST, on_tool_request)
    
    async def _on_resource_warning(self, state) -> None:
        if not state.metrics:
            return
        print(f"\n⚠️  RESOURCE WARNING: RAM={state.metrics.ram_used_gb:.1f}GB CPU={state.metrics.cpu_percent:.1f}% Latency={state.metrics.generation_latency_ms:.0f}ms")
        for w in state.warnings:
            print(f"  - {w}")
    
    async def _on_resource_critical(self, state) -> None:
        if not state.metrics:
            return
        print(f"\n🚨 RESOURCE CRITICAL: RAM={state.metrics.ram_used_gb:.1f}GB CPU={state.metrics.cpu_percent:.1f}% Latency={state.metrics.generation_latency_ms:.0f}ms")
        for w in state.warnings:
            print(f"  - {w}")
        
        if self.conversation_engine and self.conversation_engine.is_running:
            await self.conversation_engine.pause()
            print("  -> Conversation PAUSED due to critical resource usage")
    
    def _on_turn_autonomy(self, message) -> None:
        if not self.autonomous_env or not self.autonomous_env.is_enabled:
            return
        
        turn = self.conversation_engine.turn_number
        
        asyncio.create_task(self._process_autonomy(turn))
    
    async def _process_autonomy(self, turn: int) -> None:
        if not self.autonomous_env or not self.autonomous_env.is_enabled:
            return
        
        if self.autonomous_env.active_session:
            if turn % 2 == 0:
                context = {
                    "topic": "Autonomous exploration",
                    "discoveries": self.autonomous_env.active_session.findings[-3:] if self.autonomous_env.active_session.findings else [],
                    "questions": [],
                    "tools": [t.name for t in self.tool_gateway.list_tools()] if self.tool_gateway else [],
                    "turns_remaining": max(1, self.autonomous_env.active_session.proposal.estimated_turns - self.autonomous_env.active_session.turns_spent)
                }
                result = await self.autonomous_env.execute_exploration_step(
                    "agent_a",
                    self.model_registry.get(),
                    context
                )
                if result and result.get("action") == "conclude":
                    print(f"\n🔍 Autonomous exploration completed: {result.get('conclusion')}")
        
        elif self.autonomous_env.should_propose(turn):
            context = {}
            if self.memory_manager:
                mem_context = await self.memory_manager.get_context(turn)
                context = {
                    "topic": "Autonomous exploration",
                    "discoveries": mem_context.get("important_facts", []),
                    "questions": mem_context.get("open_questions", []),
                    "tools": [t.name for t in self.tool_gateway.list_tools()] if self.tool_gateway else [],
                    "turns_remaining": 10
                }
            
            proposal = await self.autonomous_env.propose_exploration(
                "agent_a",
                self.model_registry.get(),
                context
            )
            if proposal:
                print(f"\n🔍 New autonomous proposal: {proposal.title}")
    
    def _setup_event_logging(self) -> None:
        async def log_event(event):
            logger.debug(f"Event: {event.type.value} - {event.payload}")
        
        self.event_bus.subscribe_all(log_event)
    
    def _on_turn(self, message) -> None:
        print(f"\n{'='*60}")
        print(f"[{message.role.value.upper()}] Turn {message.turn_number}")
        print(f"{'='*60}")
        print(message.content)
        print(f"{'='*60}\n")
    
    def _on_interrupt(self) -> None:
        print("\n>>> INTERRUPT RECEIVED <<<\n")
        if self._tts and self._tts.is_speaking():
            asyncio.create_task(self._tts.stop())
    
    async def run(self) -> None:
        if not self.conversation_engine:
            raise RuntimeError("Not initialized")
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
        
        print("\n" + "="*60)
        print("AI SANDBOX - Autonomous Multi-Agent Conversation")
        print("="*60)
        print(f"Conversation ID: {self.conversation_engine.conversation_id}")
        print(f"Agents: A (Explorer) <-> B (Challenger)")
        if self._tts:
            print(f"TTS: Enabled")
        if self._stt:
            print(f"STT: Enabled (speak to interrupt)")
        if self.resource_manager:
            print(f"Resource Monitoring: Enabled")
        print(f"Press Ctrl+C to stop\n")
        
        session_config = SessionConfig(
            session_id=self.conversation_engine.conversation_id,
            max_turns=self.config.get("conversation", {}).get("max_turns", 1000),
            turn_timeout_seconds=self.config.get("conversation", {}).get("turn_timeout_seconds", 120),
            short_term_turns=self.config.get("conversation", {}).get("short_term_turns", 8),
            initial_speaker=self.config.get("conversation", {}).get("initial_speaker", "agent_a"),
            scheduler_policy=self.config.get("conversation", {}).get("scheduler_policy", "round_robin"),
            model_config=self.config.get("model", {}),
            resource_config=self.config.get("resources", {}),
            permissions_config=self.config.get("permissions", {}),
            tools_config=self.config.get("tools", {}),
            autonomy_config=self.config.get("autonomy", {})
        )
        
        await self.session_manager.create_session(session_config)
        
        if self.resource_manager:
            await self.resource_manager.start()
        
        await self.conversation_engine.start()
        
        await self._shutdown_event.wait()
    
    async def shutdown(self) -> None:
        logger.info("Shutting down...")
        if self.session_manager:
            await self.session_manager.complete_session()
        if self.evidence_manager:
            await self.evidence_manager.stop()
        if self.resource_manager:
            await self.resource_manager.stop()
        if self._stt:
            await self._stt.stop_listening()
        if self._stt_task:
            self._stt_task.cancel()
            try:
                await self._stt_task
            except asyncio.CancelledError:
                pass
        if self._tts:
            await self._tts.stop()
        if hasattr(self, 'tool_gateway'):
            for tool in self.tool_gateway._tools.values():
                if hasattr(tool, 'close'):
                    await tool.close()
        if self.conversation_engine:
            await self.conversation_engine.stop()
        await self.model_registry.close_all()
        self._shutdown_event.set()


def main():
    from app.cli.main import cli
    cli()


if __name__ == "__main__":
    main()