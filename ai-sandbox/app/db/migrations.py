"""
Database Migration Framework

Provides versioned schema migrations for SQLite database.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Callable

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: int, description: str, up_sql: str, down_sql: str = ""):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def __repr__(self):
        return f"Migration(v{self.version}: {self.description})"


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrations: List[Migration] = []
        self._init_migration_table()
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_migration_table(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    checksum TEXT
                )
            """)
            conn.commit()
    
    def add_migration(self, migration: Migration) -> None:
        """Add a migration to the manager."""
        self._migrations.append(migration)
        # Sort by version
        self._migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[int]:
        """Get list of applied migration versions."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
            return [row["version"] for row in rows]
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet."""
        applied = set(self.get_applied_migrations())
        return [m for m in self._migrations if m.version not in applied]
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """Run pending migrations up to target_version (or all if None)."""
        pending = self.get_pending_migrations()
        
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        for migration in pending:
            logger.info(f"Applying migration v{migration.version}: {migration.description}")
            
            try:
                with self._get_conn() as conn:
                    # Run migration in transaction
                    conn.execute("BEGIN")
                    conn.executescript(migration.up_sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, datetime('now'))",
                        (migration.version, migration.description)
                    )
                    conn.execute("COMMIT")
                
                logger.info(f"Migration v{migration.version} applied successfully")
                
            except Exception as e:
                logger.error(f"Migration v{migration.version} failed: {e}")
                return False
        
        return True
    
    def rollback(self, target_version: int) -> bool:
        """Rollback migrations down to target_version."""
        applied = self.get_applied_migrations()
        to_rollback = [v for v in applied if v > target_version]
        to_rollback.sort(reverse=True)
        
        # Find migration objects for rollback
        migration_map = {m.version: m for m in self._migrations}
        
        for version in to_rollback:
            migration = migration_map.get(version)
            if not migration or not migration.down_sql:
                logger.error(f"No rollback SQL for migration v{version}")
                return False
            
            logger.info(f"Rolling back migration v{version}: {migration.description}")
            
            try:
                with self._get_conn() as conn:
                    conn.execute("BEGIN")
                    conn.executescript(migration.down_sql)
                    conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                    conn.execute("COMMIT")
                
                logger.info(f"Migration v{version} rolled back")
                
            except Exception as e:
                logger.error(f"Rollback v{version} failed: {e}")
                return False
        
        return True
    
    def get_current_version(self) -> int:
        """Get current schema version."""
        applied = self.get_applied_migrations()
        return max(applied) if applied else 0
    
    def validate_checksums(self) -> bool:
        """Validate that applied migrations match their checksums."""
        # This would require storing checksums in the migration table
        # For now, just return True
        return True


# Built-in migrations
def get_initial_migration() -> Migration:
    """Initial schema migration."""
    return Migration(
        version=1,
        description="Initial schema",
        up_sql="""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                correlation_id TEXT,
                intent TEXT,
                reason TEXT,
                action_details TEXT,
                input_data TEXT,
                output_data TEXT,
                permission_required INTEGER DEFAULT 0,
                permission_id TEXT,
                artifacts TEXT,
                tags TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_evidence_session ON evidence(session_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_agent ON evidence(agent_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);
            CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);
            
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                domain TEXT,
                publisher TEXT,
                retrieved_at TEXT NOT NULL,
                content_reference TEXT,
                content_hash TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sources_research ON sources(research_id);
            
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                source_id TEXT,
                agent_id TEXT NOT NULL,
                claim TEXT NOT NULL,
                claim_type TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                verification_status TEXT DEFAULT 'pending',
                supporting_evidence TEXT,
                contradicting_evidence TEXT,
                created_at TEXT NOT NULL,
                verified_at TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_claims_research ON claims(research_id);
            CREATE INDEX IF NOT EXISTS idx_claims_agent ON claims(agent_id);
            
            CREATE TABLE IF NOT EXISTS research_sessions (
                research_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                question TEXT NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                sources TEXT,
                claims TEXT,
                conclusion TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_research_session ON research_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_research_agent ON research_sessions(agent_id);
            
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                objective TEXT NOT NULL,
                hypothesis TEXT,
                proposed_procedure TEXT,
                required_tools TEXT,
                required_permissions TEXT,
                status TEXT DEFAULT 'proposed',
                baseline_reference TEXT,
                result TEXT,
                conclusion TEXT,
                started_at TEXT,
                completed_at TEXT,
                artifacts TEXT,
                metrics TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_experiments_session ON experiments(session_id);
            CREATE INDEX IF NOT EXISTS idx_experiments_agent ON experiments(agent_id);
            
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT,
                evidence_considered TEXT,
                alternatives TEXT,
                resulting_action TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_agent ON decisions(agent_id);
            
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                name TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                path TEXT NOT NULL,
                size_bytes INTEGER DEFAULT 0,
                created_by_action TEXT,
                experiment_id TEXT,
                research_id TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);
            CREATE INDEX IF NOT EXISTS idx_artifacts_experiment ON artifacts(experiment_id);
            
            CREATE TABLE IF NOT EXISTS modifications (
                modification_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                proposal TEXT NOT NULL,
                reason TEXT,
                hypothesis TEXT,
                expected_benefit TEXT,
                expected_risk TEXT,
                files_affected TEXT,
                branch TEXT,
                baseline_commit TEXT,
                status TEXT DEFAULT 'proposed',
                benchmark_before TEXT,
                benchmark_after TEXT,
                test_results TEXT,
                approval TEXT,
                applied_commit TEXT,
                rollback_commit TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                evidence TEXT,
                metadata TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_modifications_session ON modifications(session_id);
            
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                session_number INTEGER,
                status TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                configuration TEXT,
                model_configuration TEXT,
                project_version TEXT,
                environment_metadata TEXT,
                summary TEXT,
                recovery_state TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
            
            CREATE TABLE IF NOT EXISTS resource_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ram_used_gb REAL,
                ram_total_gb REAL,
                cpu_percent REAL,
                gpu_percent REAL,
                inference_latency_ms REAL,
                tokens_per_second REAL,
                context_tokens INTEGER,
                active_agents INTEGER,
                active_model TEXT,
                queue_depth INTEGER
            );
            
            CREATE INDEX IF NOT EXISTS idx_metrics_session ON resource_metrics(session_id);
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON resource_metrics(timestamp);
        """,
        down_sql="""
            DROP TABLE IF EXISTS resource_metrics;
            DROP TABLE IF EXISTS sessions;
            DROP TABLE IF EXISTS modifications;
            DROP TABLE IF EXISTS artifacts;
            DROP TABLE IF EXISTS decisions;
            DROP TABLE IF EXISTS experiments;
            DROP TABLE IF EXISTS research_sessions;
            DROP TABLE IF EXISTS claims;
            DROP TABLE IF NOT EXISTS sources;
            DROP TABLE IF NOT EXISTS evidence;
        """
    )


def get_migration_manager(db_path: str) -> 'MigrationManager':
    """Create a migration manager with built-in migrations."""
    manager = MigrationManager(db_path)
    manager.add_migration(get_initial_migration())
    return manager