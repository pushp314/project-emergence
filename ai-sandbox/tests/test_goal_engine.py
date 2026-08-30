import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.orchestration.goal_loop import GoalEngine, GoalState, GoalContext
from app.events.bus import Event, EventType

@pytest.mark.asyncio
async def test_goal_engine_planning():
    engine = GoalEngine(conversation_engine=MagicMock())
    engine.start_goal("Test Objective")
    
    # Mock model registry
    import app.orchestration.goal_loop
    mock_registry = MagicMock()
    mock_model = AsyncMock()
    
    # Return a mocked plan
    mock_resp = MagicMock()
    mock_resp.text = '["Step 1", "Step 2"]'
    mock_model.generate.return_value = mock_resp
    
    mock_registry.get.return_value = mock_model
    app.orchestration.goal_loop.get_model_registry = MagicMock(return_value=mock_registry)
    
    await engine.step()
    
    assert engine.state == GoalState.ACTING
    assert len(engine.context.plan) == 2
    assert engine.context.plan[0] == "Step 1"

@pytest.mark.asyncio
async def test_goal_engine_critiquing_yes():
    engine = GoalEngine(conversation_engine=MagicMock())
    engine.start_goal("Test Objective")
    engine.context.plan = ["Step 1"]
    engine.state = GoalState.CRITIQUING
    engine.context.actions_taken.append({"step": 0, "result": "done"})
    
    import app.orchestration.goal_loop
    mock_registry = MagicMock()
    mock_model = AsyncMock()
    
    mock_resp = MagicMock()
    mock_resp.text = 'YES'
    mock_model.generate.return_value = mock_resp
    
    mock_registry.get.return_value = mock_model
    app.orchestration.goal_loop.get_model_registry = MagicMock(return_value=mock_registry)
    
    await engine.step()
    
    assert engine.state == GoalState.DONE
    assert engine.context.is_satisfied == True

@pytest.mark.asyncio
async def test_submit_task_result_event():
    engine = GoalEngine(conversation_engine=MagicMock())
    engine.start_goal("Test Objective")
    
    event = Event(
        type=EventType.TOOL_REQUEST,
        conversation_id="conv",
        payload={"tool_name": "submit_task_result", "arguments": {"result": "success"}}
    )
    
    await engine._on_tool_request(event)
    
    assert len(engine.context.actions_taken) == 1
    assert engine.context.actions_taken[0]["result"] == "success"
    assert engine._step_completed_event.is_set()
