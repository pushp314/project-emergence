import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock

from app.memory.context_manager import ContextManager, ContextSnapshot, ContextState
from app.events.bus import EventBus

@pytest_asyncio.fixture
async def context_manager():
    store = Mock()
    store.save_message = AsyncMock()
    store.get_messages = Mock(return_value=[])
    store.get_latest_summary = Mock(return_value=None)
    store.get_all_summaries = Mock(return_value=[])
    store.get_memory = Mock(return_value=[])
    
    summarizer = Mock()
    summarizer.build_context = AsyncMock(return_value={"recent_messages": [], "summary": "Test Summary"})
    
    summary_mock = Mock()
    summary_mock.id = "1"
    summary_mock.topic = "Test Topic"
    summary_mock.important_facts = []
    summary_mock.unresolved_questions = []
    summary_mock.turn_start = 0
    summary_mock.turn_end = 10
    summary_mock.key_points = []
    
    summarizer.summarize = AsyncMock(return_value=summary_mock)
    
    event_bus = EventBus()
    
    manager = ContextManager(
        store=store, 
        summarizer=summarizer, 
        event_bus=event_bus, 
        summarization_interval=2
    )
    manager.set_conversation("test_conversation_123")
    return manager

@pytest.mark.asyncio
async def test_context_manager_update_from_message(context_manager):
    class DummyMessage:
        agent_id = "agent_1"
        agent_identity = "tester"
        content = "Hello world"
        timestamp = "2023-01-01T00:00:00"
        metadata = {}
    
    snapshot = await context_manager.update_from_message(DummyMessage(), current_turn=1)
    
    assert snapshot.conversation_id == "test_conversation_123"
    assert snapshot.turn_number == 1
    assert snapshot.summary == "Test Summary"
    assert context_manager.state.total_turns == 1
    assert context_manager.state.role_distribution["tester"] == 1

@pytest.mark.asyncio
async def test_context_manager_summarization(context_manager):
    class DummyMessage:
        agent_id = "agent_1"
        agent_identity = "tester"
        content = "Hello world"
        timestamp = "2023-01-01T00:00:00"
        metadata = {}
    
    # summarize_interval is 2. Turn 1 should not trigger summary.
    await context_manager.update_from_message(DummyMessage(), current_turn=1)
    assert context_manager.state.summarized_turns == 0
    
    # Turn 2 should trigger summary.
    await context_manager.update_from_message(DummyMessage(), current_turn=2)
    assert context_manager.state.summarized_turns == 2
    assert context_manager.state.current_topic == "Test Topic"

@pytest.mark.asyncio
async def test_context_budget_adjustment(context_manager):
    budget_green = context_manager._budget_adjusted("GREEN")
    assert budget_green == context_manager.max_context_tokens
    
    budget_yellow = context_manager._budget_adjusted("YELLOW")
    assert budget_yellow == int(context_manager.max_context_tokens * 0.85)
    
    budget_orange = context_manager._budget_adjusted("ORANGE")
    assert budget_orange == int(context_manager.max_context_tokens * 0.70)
    
    budget_red = context_manager._budget_adjusted("RED")
    assert budget_red == 0
