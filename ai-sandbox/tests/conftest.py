import pytest
import pytest_asyncio
import sqlite3
import os
import tempfile
from unittest.mock import Mock

from app.events.bus import EventBus
from app.evidence.manager import EvidenceManager

@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def evidence_manager(temp_db_path, event_bus):
    manager = EvidenceManager(db_path=temp_db_path, event_bus=event_bus)
    await manager.start("test_session")
    yield manager
    await manager.stop()
