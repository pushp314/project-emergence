import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone


class TestEventBus:
    """Test EventBus functionality"""
    
    @pytest.fixture
    def event_bus(self):
        from app.events.bus import EventBus
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus):
        """Test basic subscribe and publish"""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        from app.events.bus import EventType
        event_bus.subscribe(EventType.AGENT_MESSAGE, handler)
        
        from app.events.bus import Event
        event = Event(type=EventType.AGENT_MESSAGE, conversation_id="test-123", payload={"data": "test"})
        await event_bus.publish(event)
        
        await asyncio.sleep(0.01)  # Allow async processing
        
        assert len(received_events) == 1
        assert received_events[0].type == EventType.AGENT_MESSAGE
        assert received_events[0].payload["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_wildcard_subscriber(self, event_bus):
        """Test wildcard subscriber receives all events"""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        event_bus.subscribe_all(handler)
        
        from app.events.bus import Event, EventType
        event1 = Event(type=EventType.AGENT_MESSAGE, conversation_id="test", payload={})
        event2 = Event(type=EventType.TOOL_REQUEST, conversation_id="test", payload={})
        
        await event_bus.publish(event1)
        await event_bus.publish(event2)
        
        await asyncio.sleep(0.01)
        
        assert len(received_events) == 2
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribe removes handler"""
        received_events = []
        
        async def handler(event):
            received_events.append(event)
        
        from app.events.bus import EventType
        event_bus.subscribe(EventType.AGENT_MESSAGE, handler)
        event_bus.unsubscribe(EventType.AGENT_MESSAGE, handler)
        
        from app.events.bus import Event
        event = Event(type=EventType.AGENT_MESSAGE, conversation_id="test", payload={})
        await event_bus.publish(event)
        
        await asyncio.sleep(0.01)
        
        assert len(received_events) == 0
    
    @pytest.mark.asyncio
    async def test_event_history(self, event_bus):
        """Test event history retrieval"""
        from app.events.bus import Event, EventType
        
        for i in range(5):
            event = Event(type=EventType.AGENT_MESSAGE, conversation_id="test", payload={"index": i})
            await event_bus.publish(event)
        
        await asyncio.sleep(0.01)
        
        history = event_bus.get_history(limit=3)
        assert len(history) == 3
        
        all_history = event_bus.get_history()
        assert len(all_history) == 5


class TestStateMachine:
    """Test StateMachine functionality"""
    
    @pytest.fixture
    def state_machine(self):
        from app.orchestration.state_machine import StateMachine, ConversationState
        return StateMachine()
    
    def test_initial_state(self, state_machine):
        from app.orchestration.state_machine import ConversationState
        assert state_machine.state == ConversationState.IDLE
    
    def test_valid_transition(self, state_machine):
        from app.orchestration.state_machine import ConversationState
        result = state_machine.transition(ConversationState.THINKING)
        assert result is True
        assert state_machine.state == ConversationState.THINKING
    
    def test_invalid_transition(self, state_machine):
        from app.orchestration.state_machine import ConversationState
        # IDLE -> SPEAKING is not allowed
        result = state_machine.transition(ConversationState.SPEAKING)
        assert result is False
        assert state_machine.state == ConversationState.IDLE
    
    def test_shutdown_transition(self, state_machine):
        from app.orchestration.state_machine import ConversationState
        result = state_machine.transition(ConversationState.GRACEFUL_SHUTDOWN)
        assert result is True
        assert state_machine.state == ConversationState.GRACEFUL_SHUTDOWN
        
        # Second shutdown should be idempotent (returns True but doesn't change state)
        result = state_machine.shutdown()
        assert result is True
        assert state_machine.state == ConversationState.GRACEFUL_SHUTDOWN
    
    def test_pause_resume(self, state_machine):
        from app.orchestration.state_machine import ConversationState
        
        state_machine.transition(ConversationState.THINKING)
        assert state_machine.pause() is True
        assert state_machine.state == ConversationState.PAUSED
        
        assert state_machine.resume() is True
        assert state_machine.state == ConversationState.THINKING


class TestScheduler:
    """Test Scheduler functionality"""
    
    def test_round_robin_scheduler(self):
        from app.orchestration.scheduler import create_scheduler
        
        scheduler = create_scheduler(
            agents=["agent_a", "agent_b", "agent_c"],
            policy_name="round_robin",
            initial_speaker="agent_a"
        )
        
        # Before start, current_speaker is None
        assert scheduler.current_speaker is None
        assert scheduler.turn_number == 0
        
        # Start the scheduler
        scheduler.start("agent_a")
        assert scheduler.current_speaker == "agent_a"
        assert scheduler.turn_number == 1
        
        next_speaker = scheduler.next_turn()
        assert next_speaker == "agent_b"
        assert scheduler.turn_number == 2
        
        next_speaker = scheduler.next_turn()
        assert next_speaker == "agent_c"
        
        next_speaker = scheduler.next_turn()
        assert next_speaker == "agent_a"
        assert scheduler.turn_number == 4
    
    def test_adaptive_scheduler(self):
        from app.orchestration.scheduler import create_scheduler
        
        scheduler = create_scheduler(
            agents=["agent_a", "agent_b"],
            policy_name="adaptive"
        )
        
        assert scheduler.turn_number == 0
        first = scheduler.start("agent_a")
        assert first == "agent_a"
        assert scheduler.turn_number == 1
        
        # agent_a has 1 turn, agent_b has 0, so next should be agent_b
        next_speaker = scheduler.next_turn()
        assert next_speaker == "agent_b"


class TestEventSchemas:
    """Test event schemas and data structures"""
    
    def test_event_creation(self):
        from app.events.schemas import AgentMessage
        from app.events.bus import Event, EventType
        
        message = AgentMessage(
            agent_id="agent_a",
            agent_identity="explorer",
            content="Hello world",
            turn_number=1
        )
        
        assert message.agent_id == "agent_a"
        assert message.agent_identity == "explorer"
        assert message.content == "Hello world"
        assert message.turn_number == 1
    
    def test_tool_call_schema(self):
        from app.events.schemas import ToolCall
        
        call = ToolCall(
            tool_name="terminal",
            arguments={"command": "ls"},
            agent_id="agent_a"
        )
        
        assert call.tool_name == "terminal"
        assert call.arguments["command"] == "ls"
        assert call.agent_id == "agent_a"
        assert call.call_id is not None
    
    def test_permission_request_schema(self):
        from app.events.schemas import PermissionRequest, RiskLevel, PermissionLevel
        
        request = PermissionRequest(
            agent_id="agent_a",
            action="install_package",
            command="brew install nmap",
            reason="Need for network scanning",
            risk=RiskLevel.HIGH,
            scope=PermissionLevel.INSTALL
        )
        
        assert request.agent_id == "agent_a"
        assert request.risk == RiskLevel.HIGH
        assert request.scope == PermissionLevel.INSTALL
        assert request.request_id is not None


class TestMemoryStore:
    """Test SQLite memory store"""
    
    @pytest.fixture
    def store(self, tmp_path):
        from app.memory.store import SQLiteStore
        db_path = tmp_path / "test.db"
        return SQLiteStore(str(db_path))
    
    def test_save_and_get_messages(self, store):
        from app.memory.store import ConversationRecord
        
        record = ConversationRecord(
            id="test-1",
            conversation_id="conv-1",
            turn_number=1,
            agent_id="agent_a",
            role="explorer",
            content="Test message",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"key": "value"}
        )
        
        store.save_message(record)
        
        messages = store.get_messages("conv-1", limit=10)
        assert len(messages) == 1
        assert messages[0].content == "Test message"
        assert messages[0].agent_id == "agent_a"
        assert messages[0].metadata["key"] == "value"
    
    def test_memory_operations(self, store):
        from app.memory.store import MemoryRecord
        
        record = MemoryRecord(
            id="mem-1",
            conversation_id="conv-1",
            type="fact",
            content="Important fact",
            importance=0.9,
            metadata={"source": "agent_a"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        store.save_memory(record)
        
        memories = store.get_memory("conv-1", type_filter="fact")
        assert len(memories) == 1
        assert memories[0].content == "Important fact"
        assert memories[0].importance == 0.9


class TestEvidenceManager:
    """Test Evidence Manager"""
    
    @pytest.fixture
    def evidence_manager(self, tmp_path):
        from app.events.bus import EventBus
        from app.evidence.manager import EvidenceManager
        
        db_path = tmp_path / "evidence.db"
        event_bus = EventBus()
        manager = EvidenceManager(db_path=str(db_path), event_bus=event_bus)
        return manager
    
    @pytest.mark.asyncio
    async def test_start_stop(self, evidence_manager):
        await evidence_manager.start("session-1")
        assert evidence_manager._running is True
        
        await evidence_manager.stop()
        assert evidence_manager._running is False
    
    @pytest.mark.asyncio
    async def test_record_evidence(self, evidence_manager):
        await evidence_manager.start("session-1")
        
        from app.events.bus import Event, EventType
        event = Event(
            type=EventType.AGENT_MESSAGE,
            conversation_id="session-1",
            payload={"agent_id": "agent_a", "content": "Test message", "turn_number": 1}
        )
        
        await evidence_manager._on_event(event)
        
        # Wait for event to be processed
        await asyncio.sleep(0.1)
        
        evidence = evidence_manager.get_session_evidence("session-1")
        assert len(evidence) > 0
        
        await evidence_manager.stop()


class TestTools:
    """Test Tool implementations"""
    
    @pytest.mark.asyncio
    async def test_terminal_tool(self):
        from app.tools.terminal import TerminalTool
        
        tool = TerminalTool(timeout=5)
        
        # Test simple command
        result = await tool.execute({"command": "echo hello"})
        assert result["exit_code"] == 0
        assert "hello" in result["stdout"]
        
        # Test command with arguments
        result = await tool.execute({"command": "echo hello world"})
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]
    

    
    @pytest.mark.asyncio
    async def test_filesystem_tool(self, tmp_path):
        from app.tools.filesystem import FilesystemTool
        
        tool = FilesystemTool(base_path=str(tmp_path))
        
        # Write file
        result = await tool.execute({
            "operation": "write",
            "path": "test.txt",
            "content": "Hello world"
        })
        assert result["success"] is True
        
        # Read file
        result = await tool.execute({
            "operation": "read",
            "path": "test.txt"
        })
        assert result["content"] == "Hello world"
        
        # List directory
        result = await tool.execute({
            "operation": "list",
            "path": "."
        })
        assert len(result["entries"]) >= 1
    
    @pytest.mark.asyncio
    async def test_filesystem_tool_symlink_protection(self, tmp_path):
        from app.tools.filesystem import FilesystemTool
        import os
        
        tool = FilesystemTool(base_path=str(tmp_path))
        
        # Create a file outside the base path
        outside_file = tmp_path.parent / "outside.txt"
        outside_file.write_text("secret")
        
        # Create symlink inside base path pointing outside
        link_path = tmp_path / "link.txt"
        os.symlink(outside_file, link_path)
        
        # Try to read through symlink - should be blocked
        result = await tool.execute({
            "operation": "read",
            "path": "link.txt"
        })
        assert "error" in result or result.get("content") != "secret"


class TestPermissionManager:
    """Test Permission Manager"""
    
    @pytest.fixture
    def perm_manager(self):
        from app.events.bus import EventBus
        from app.permissions.manager import PermissionManager
        
        event_bus = EventBus()
        return PermissionManager(event_bus, timeout_seconds=5)
    
    @pytest.mark.asyncio
    async def test_request_permission_auto_approve_low_risk(self):
        from app.events.bus import EventBus
        from app.permissions.manager import PermissionManager
        from app.events.schemas import RiskLevel, PermissionLevel
        
        event_bus = EventBus()
        manager = PermissionManager(event_bus, timeout_seconds=1, auto_approve_low_risk=True)
        
        # Low risk should be auto-approved
        result = await manager.request_permission(
            agent_id="agent_a",
            action="read_file",
            command="cat file.txt",
            reason="Need to read config",
            risk=RiskLevel.LOW,
            scope=PermissionLevel.READ
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_permission_denied_on_timeout(self):
        from app.events.bus import EventBus
        from app.permissions.manager import PermissionManager
        from app.events.schemas import RiskLevel, PermissionLevel
        
        event_bus = EventBus()
        manager = PermissionManager(event_bus, timeout_seconds=1, auto_approve_low_risk=False)
        
        # Start a request but don't approve - should timeout
        import asyncio
        task = asyncio.create_task(manager.request_permission(
            agent_id="agent_a",
            action="delete_file",
            command="rm file.txt",
            reason="Cleanup",
            risk=RiskLevel.HIGH,
            scope=PermissionLevel.WRITE
        ))
        
        # Wait for timeout
        result = await asyncio.wait_for(task, timeout=2.0)
        assert result is False


class TestResourceManager:
    """Test Resource Manager"""
    
    @pytest.fixture
    def resource_manager(self):
        from app.events.bus import EventBus
        from app.resources.monitor import ResourceManager, ResourceThresholds
        
        event_bus = EventBus()
        thresholds = ResourceThresholds(
            memory_warning_gb=10.0,  # Low threshold for testing
            memory_critical_gb=12.0,
            cpu_warning_percent=50.0,
            cpu_critical_percent=80.0,
            check_interval_seconds=1.0
        )
        return ResourceManager(EventBus(), thresholds)
    
    @pytest.mark.asyncio
    async def test_resource_monitoring(self, resource_manager):
        await resource_manager.start()
        
        # Wait for at least one check
        await asyncio.sleep(1.5)
        
        state = resource_manager.get_state()
        assert state.metrics is not None
        assert state.metrics.ram_used_gb > 0
        assert state.metrics.cpu_percent >= 0
        
        await resource_manager.stop()
    
    def test_threshold_evaluation(self, resource_manager):
        from app.resources.monitor import ResourceMetrics, ResourceLevel
        
        # Normal metrics
        metrics = ResourceMetrics(
            ram_used_gb=5.0, ram_total_gb=16.0, ram_percent=31.25,
            cpu_percent=20.0
        )
        level = resource_manager._evaluate_level(metrics)
        assert level == ResourceLevel.NORMAL
        
        # High memory
        metrics = ResourceMetrics(
            ram_used_gb=11.0, ram_total_gb=16.0, ram_percent=68.75,
            cpu_percent=20.0
        )
        level = resource_manager._evaluate_level(metrics)
        assert level == ResourceLevel.WARNING
        
        # Critical memory
        metrics = ResourceMetrics(
            ram_used_gb=13.0, ram_total_gb=16.0, ram_percent=81.25,
            cpu_percent=20.0
        )
        level = resource_manager._evaluate_level(metrics)
        assert level == ResourceLevel.CRITICAL


class TestConversationEngine:
    """Test Conversation Engine"""
    
    @pytest.mark.asyncio
    async def test_conversation_start_stop(self):
        from app.events.bus import EventBus
        from app.orchestration.conversation import ConversationEngine, ConversationConfig
        from app.agents.explorer import create_explorer_agent
        from app.models.base import ModelAdapter, GenerationRequest, GenerationResponse, get_model_registry
        
        event_bus = EventBus()
        model_registry = get_model_registry()
        
        # Create a mock model adapter
        class MockModelAdapter(ModelAdapter):
            def __init__(self):
                self._config = None
            
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(
                    text="Mock response",
                    tokens_generated=10,
                    finish_reason="stop",
                    latency_ms=100,
                    model="test-model"
                )
            
            async def generate_stream(self, request: GenerationRequest):
                yield "Mock response"
            
            async def count_tokens(self, text: str) -> int:
                return len(text) // 4
            
            async def health_check(self) -> bool:
                return True
            
            def get_model_info(self) -> dict:
                return {"name": "test-model"}
            
            async def close(self) -> None:
                pass
        
        mock_adapter = MockModelAdapter()
        model_registry.register("test-model", mock_adapter, is_default=True)
        
        agent_a = create_explorer_agent("agent_a", "test-model")
        agent_b = create_explorer_agent("agent_b", "test-model")
        
        agents = {"agent_a": agent_a, "agent_b": agent_b}
        
        config = ConversationConfig(
            conversation_id="test-conv",
            max_turns=5,
            turn_timeout_seconds=10,
            short_term_turns=4,
            initial_speaker="agent_a",
            scheduler_policy="round_robin"
        )
    
        import os
        os.environ["MASTER_PIN"] = "0000"
        engine = ConversationEngine(config, agents, event_bus)
        
        # Test that engine initializes correctly
        assert engine.conversation_id == "test-conv"
        assert engine.turn_number == 0
        assert engine.is_running is False
        
        # Test state
        state = engine.get_state()
        assert state["conversation_id"] == "test-conv"
        assert state["running"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])