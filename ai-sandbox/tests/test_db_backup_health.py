import pytest
import sqlite3
import os
import tempfile
from pathlib import Path

from app.events.bus import EventBus, EventType
from app.evidence.manager import EvidenceManager


class TestDatabaseBackup:
    """Test database backup functionality."""

    @pytest.fixture
    def temp_db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def backup_dir(self):
        d = tempfile.mkdtemp()
        yield d
        import shutil
        shutil.rmtree(d, ignore_errors=True)

    @pytest.fixture
    def manager(self, temp_db_path, event_bus):
        return EvidenceManager(db_path=temp_db_path, event_bus=event_bus)

    @pytest.mark.asyncio
    async def test_backup_creates_file(self, manager, backup_dir):
        await manager.start("backup_test")
        
        backup_path = manager.backup(backup_dir)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".db")
        await manager.stop()

    @pytest.mark.asyncio
    async def test_backup_contains_data(self, manager, backup_dir):
        await manager.start("backup_data_test")
        
        from app.evidence.schemas import Evidence, EvidenceType
        evidence = Evidence(
            session_id="backup_data_test",
            agent_id="atlas",
            evidence_type=EvidenceType.AGENT_ACTION,
            intent="test backup",
            reason="testing backup preserves data"
        )
        await manager._save_evidence(evidence)
        
        backup_path = manager.backup(backup_dir)
        assert backup_path is not None
        
        conn = sqlite3.connect(backup_path)
        cursor = conn.execute("SELECT COUNT(*) FROM evidence")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count >= 1
        await manager.stop()

    @pytest.mark.asyncio
    async def test_backup_increments(self, manager, backup_dir):
        await manager.start("backup_incr_test")
        
        path1 = manager.backup(backup_dir)
        path2 = manager.backup(backup_dir)
        
        assert path1 is not None
        assert path2 is not None
        assert path1 != path2
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        await manager.stop()

    @pytest.mark.asyncio
    async def test_restore_from_backup(self, manager, temp_db_path, backup_dir):
        await manager.start("restore_test")
        
        from app.evidence.schemas import Evidence, EvidenceType
        evidence = Evidence(
            session_id="restore_test",
            agent_id="argus",
            evidence_type=EvidenceType.TOOL_CALL,
            intent="test restore",
            reason="testing restore recovers data"
        )
        await manager._save_evidence(evidence)
        
        backup_path = manager.backup(backup_dir)
        assert backup_path is not None
        
        await manager.stop()
        
        manager2 = EvidenceManager(db_path=temp_db_path, event_bus=EventBus())
        result = manager2.restore(backup_path)
        assert result is True
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM evidence WHERE agent_id = 'argus'")
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count >= 1

    @pytest.mark.asyncio
    async def test_restore_nonexistent_fails(self, manager):
        result = manager.restore("/nonexistent/path/backup.db")
        assert result is False


class TestDatabaseHealth:
    """Test database health inspection."""

    @pytest.fixture
    def manager(self, temp_db_path, event_bus):
        return EvidenceManager(db_path=temp_db_path, event_bus=event_bus)

    @pytest.fixture
    def temp_db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, manager):
        health = manager.get_db_health()
        
        assert health["healthy"] is True
        assert health["exists"] is True
        assert health["table_count"] > 0
        assert health["integrity"] == "ok"
        assert health["wal_mode"] is True
        assert health["schema_version"] >= 0

    @pytest.mark.asyncio
    async def test_health_check_tables(self, manager):
        health = manager.get_db_health()
        
        expected_tables = {
            "evidence", "sources", "claims", "research_sessions",
            "experiments", "decisions", "artifacts", "modifications",
            "sessions", "resource_metrics", "intent_action_stages"
        }
        
        for table in expected_tables:
            assert table in health["tables"], f"Missing table: {table}"

    @pytest.mark.asyncio
    async def test_health_check_row_counts(self, manager):
        await manager.start("health_test")
        
        from app.evidence.schemas import Evidence, EvidenceType
        evidence = Evidence(
            session_id="health_test",
            agent_id="atlas",
            evidence_type=EvidenceType.AGENT_ACTION,
            intent="health check",
            reason="testing row counts"
        )
        await manager._save_evidence(evidence)
        
        health = manager.get_db_health()
        
        assert "evidence" in health["row_counts"]
        assert health["row_counts"]["evidence"] >= 1
        await manager.stop()

    @pytest.mark.asyncio
    async def test_health_check_after_init(self, event_bus):
        db_path = "/tmp/nonexistent_test_db_99999.db"
        manager = EvidenceManager(db_path=db_path, event_bus=event_bus)
        health = manager.get_db_health()
        
        assert health["exists"] is True
        assert health["healthy"] is True
        assert health["table_count"] > 0
        
        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_list_backups_empty(self, manager, tmp_path):
        backups = manager.list_backups(str(tmp_path / "empty_backups"))
        assert backups == []

    @pytest.mark.asyncio
    async def test_list_backups(self, manager, tmp_path):
        await manager.start("list_test")
        
        backup_dir = str(tmp_path / "backups")
        manager.backup(backup_dir)
        manager.backup(backup_dir)
        
        backups = manager.list_backups(backup_dir)
        
        assert len(backups) == 2
        for b in backups:
            assert "path" in b
            assert "size_bytes" in b
            assert "created" in b
        await manager.stop()


class TestResourceMetricsPersistence:
    """Test that resource metrics get persisted to the database."""

    @pytest.fixture
    def temp_db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def manager(self, temp_db_path, event_bus):
        return EvidenceManager(db_path=temp_db_path, event_bus=event_bus)

    @pytest.mark.asyncio
    async def test_resource_metrics_recorded(self, manager):
        await manager.start("metrics_test")
        
        manager.record_resource_metrics({
            "ram_used_gb": 8.5,
            "ram_total_gb": 16.0,
            "cpu_percent": 45.0,
            "gpu_percent": 0.0,
            "inference_latency_ms": 250.0,
            "tokens_per_second": 15.0,
            "context_tokens": 4096,
            "active_agents": 2,
            "active_model": "qwen3-8b",
            "queue_depth": 0
        })
        
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.execute("SELECT ram_used_gb, cpu_percent, active_model FROM resource_metrics")
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == 8.5
            assert row[1] == 45.0
            assert row[2] == "qwen3-8b"
        await manager.stop()

    @pytest.mark.asyncio
    async def test_resource_metrics_no_session(self, manager):
        manager.record_resource_metrics({
            "ram_used_gb": 8.0,
            "ram_total_gb": 16.0,
            "cpu_percent": 50.0,
        })
        
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM resource_metrics")
            count = cursor.fetchone()[0]
            assert count == 0
