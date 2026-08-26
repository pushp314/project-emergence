import pytest
import tempfile
from pathlib import Path


class TestMigrationManager:
    """Test database migration framework"""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test.db")
    
    def test_migration_manager_init(self, db_path):
        from app.db.migrations import MigrationManager
        
        manager = MigrationManager(db_path)
        assert manager.get_current_version() == 0
    
    def test_add_and_apply_migration(self, db_path):
        from app.db.migrations import MigrationManager, Migration
        
        manager = MigrationManager(db_path)
        
        # Add a simple migration
        migration = Migration(
            version=1,
            description="Test migration",
            up_sql="CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);",
            down_sql="DROP TABLE test_table;"
        )
        manager.add_migration(migration)
        
        # Apply migration
        result = manager.migrate()
        assert result is True
        assert manager.get_current_version() == 1
        
        # Verify table exists
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
        row = cursor.fetchone()
        assert row is not None
        conn.close()
    
    def test_migration_rollback(self, db_path):
        from app.db.migrations import MigrationManager, Migration
        
        manager = MigrationManager(db_path)
        
        migration = Migration(
            version=1,
            description="Test migration",
            up_sql="CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);",
            down_sql="DROP TABLE test_table;"
        )
        manager.add_migration(migration)
        
        # Apply
        result = manager.migrate()
        assert result is True
        assert manager.get_current_version() == 1
        
        # Rollback
        result = manager.rollback(0)
        assert result is True
        assert manager.get_current_version() == 0
        
        # Verify table is gone
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
        row = cursor.fetchone()
        assert row is None
        conn.close()
    
    def test_multiple_migrations(self, db_path):
        from app.db.migrations import MigrationManager, Migration
        
        manager = MigrationManager(db_path)
        
        # Add multiple migrations
        manager.add_migration(Migration(
            version=1,
            description="Create users table",
            up_sql="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
            down_sql="DROP TABLE users;"
        ))
        manager.add_migration(Migration(
            version=2,
            description="Create posts table",
            up_sql="CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT);",
            down_sql="DROP TABLE posts;"
        ))
        
        # Apply all
        result = manager.migrate()
        assert result is True
        assert manager.get_current_version() == 2
        
        # Verify both tables exist
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "users" in tables
        assert "posts" in tables
        conn.close()
    
    def test_partial_migration(self, db_path):
        from app.db.migrations import MigrationManager, Migration
        
        manager = MigrationManager(db_path)
        
        manager.add_migration(Migration(
            version=1,
            description="Migration 1",
            up_sql="CREATE TABLE t1 (id INTEGER);",
            down_sql="DROP TABLE t1;"
        ))
        manager.add_migration(Migration(
            version=2,
            description="Migration 2",
            up_sql="CREATE TABLE t2 (id INTEGER);",
            down_sql="DROP TABLE t2;"
        ))
        manager.add_migration(Migration(
            version=3,
            description="Migration 3",
            up_sql="CREATE TABLE t3 (id INTEGER);",
            down_sql="DROP TABLE t3;"
        ))
        
        # Migrate only to version 2
        result = manager.migrate(target_version=2)
        assert result is True
        assert manager.get_current_version() == 2
        
        # Verify only first two tables exist
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "t1" in tables
        assert "t2" in tables
        assert "t3" not in tables
        conn.close()


class TestBuiltInMigrations:
    """Test the built-in initial migration."""
    
    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test.db")
    
    def test_initial_migration(self, db_path):
        from app.db.migrations import get_migration_manager
        
        manager = get_migration_manager(db_path)
        
        # Apply initial migration
        result = manager.migrate()
        assert result is True
        assert manager.get_current_version() == 1
        
        # Verify all tables exist
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {
            "evidence", "sources", "claims", "research_sessions",
            "experiments", "decisions", "artifacts", "modifications",
            "sessions", "resource_metrics", "schema_migrations"
        }
        
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"
        
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])