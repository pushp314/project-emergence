import pytest
import sqlite3
import asyncio
from app.events.bus import Event, EventType
from app.evidence.schemas import IntentActionStage, IntentActionRecord, EvidenceType

@pytest.mark.asyncio
async def test_intent_action_stage_recording(evidence_manager):
    record = IntentActionRecord(
        session_id="test_session",
        agent_id="atlas",
        correlation_id="test-corr",
        stage=IntentActionStage.PLAN,
        content="Testing plan stage"
    )
    
    evidence_manager.record_intent_action_stage(record)
    
    with sqlite3.connect(evidence_manager.db_path) as conn:
        cursor = conn.execute("SELECT stage, content FROM intent_action_stages WHERE record_id = ?", (record.record_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == IntentActionStage.PLAN.value
        assert row[1] == "Testing plan stage"

@pytest.mark.asyncio
async def test_emergence_event_recording(evidence_manager, event_bus):
    # Emit an emergence event
    event = Event(
        type=EventType.emergence_observed,
        conversation_id="conv-123",
        payload={
            "agent_id": "atlas",
            "behavior_type": "tool_creation",
            "details": "Agent created a new script"
        }
    )
    
    # Process event
    await evidence_manager._handle_event(event)
    
    # Verify it was saved
    with sqlite3.connect(evidence_manager.db_path) as conn:
        cursor = conn.execute("SELECT evidence_type, reason FROM evidence WHERE evidence_type = ?", (EvidenceType.emergence_observed.value,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == EvidenceType.emergence_observed.value
        assert "tool_creation" in row[1]

@pytest.mark.asyncio
async def test_self_assessment_event_recording(evidence_manager, event_bus):
    event = Event(
        type=EventType.agent_self_assessment,
        conversation_id="conv-123",
        payload={
            "agent_id": "argus",
            "assessment": "My challenge was not effective"
        }
    )
    
    await evidence_manager._handle_event(event)
    
    with sqlite3.connect(evidence_manager.db_path) as conn:
        cursor = conn.execute("SELECT evidence_type, reason FROM evidence WHERE evidence_type = ?", (EvidenceType.agent_self_assessment.value,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == EvidenceType.agent_self_assessment.value
        assert row[1] == "My challenge was not effective"
