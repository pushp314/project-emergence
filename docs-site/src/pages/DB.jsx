import React from 'react';
import CodeBlock from '../components/CodeBlock';
import './DB.css';

export default function DB() {
    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Database Commands</h1>
                <p className="page-subtitle">
                    Inspect and manage the SQLite database
                </p>
            </div>

            <section className="content-section">
                <h2 className="section-title">Available Commands</h2>
                <div className="db-commands-grid">
                    <div className="db-command-card">
                        <div className="db-cmd-name">/db health</div>
                        <p className="db-cmd-desc">
                            Comprehensive database health check. Shows integrity status,
                            WAL mode setting, table counts, and row counts.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`┌─────────────────────────────┐
│ Database Health             │
├─────────────────────────────┤
│ Integrity:  ok              │
│ WAL Mode:   enabled         │
│ Tables:     18              │
│ Total Rows: 1,247           │
│ Last Backup:  2026-08-26   │
│ DB Size:    2.4 MB          │
└─────────────────────────────┘`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Uses <code>EvidenceManager.get_db_health()</code></li>
                            <li>Integrity check runs <code>PRAGMA integrity_check</code></li>
                            <li>Shows WAL mode status and all table row counts</li>
                        </ul>
                    </div>

                    <div className="db-command-card">
                        <div className="db-cmd-name">/db backup</div>
                        <p className="db-cmd-desc">
                            Create a backup of the SQLite database. Backups are stored
                            in <code>data/backups/</code> with timestamped filenames.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`Backup created: ./data/backups/sandbox_20260826_1430.db`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Automatically includes WAL mode checkpoint</li>
                            <li>Filename format: <code>sandbox_YYYYMMDD_HHMM.db</code></li>
                            <li>Backups can be restored with <code>/db restore <path></code></li>
                        </ul>
                    </div>

                    <div className="db-command-card">
                        <div className="db-cmd-name">/db sessions</div>
                        <p className="db-cmd-desc">
                            List all conversation sessions stored in the database.
                            Shows session IDs, turn counts, start times, and last
                            activity timestamps.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`Session ID          Turns    Started              Last Active
conv_001            47       2026-08-26 10:00     2026-08-26 14:23
conv_002            12       2026-08-26 11:15     2026-08-26 11:15
conv_003            3        2026-08-26 12:30     2026-08-26 12:33`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Uses SQLiteStore to query sessions table</li>
                            <li>Shows up to 20 most recent sessions</li>
                            <li>Session data is persisted across restarts</li>
                        </ul>
                    </div>

                    <div className="db-command-card">
                        <div className="db-cmd-name">/db events</div>
                        <p className="db-cmd-desc">
                            Show recent events from the evidence database. Events include
                            agent messages, tool calls, tool results, and system events.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`Time                  Type              Agent   Intent
2026-08-26 14:23:12   agent.message     atlas   Let me check the code...
2026-08-26 14:22:45   tool.call         atlas   [TOOL:terminal:{"command":"ls"}]
2026-08-26 14:22:40   tool.result       atlas   [terminal result: ...]
2026-08-26 14:22:35   agent.message     argus   That's interesting but..."`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Filters by event type using EventType enum</li>
                            <li>Shows last 20 events by default</li>
                            <li>Timestamped for precise audit trail</li>
                        </ul>
                    </div>

                    <div className="db-command-card">
                        <div className="db-cmd-name">/db tables</div>
                        <p className="db-cmd-desc">
                            Show all table names in the database and their row counts.
                            Useful for understanding what data is being persisted.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`Table          Rows
conversations   5
messages        234
evidence        189
memories        89
summaries       12
tool_calls      23`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Shows all persisted data tables</li>
                            <li>Row counts for each table</li>
                            <li>Helps debug data persistence issues</li>
                        </ul>
                    </div>

                    <div className="db-command-card">
                        <div className="db-cmd-name">/db size</div>
                        <p className="db-cmd-desc">
                            Show the SQLite database file size. Reports total size in
                            bytes, KB, and MB, plus WAL file size if applicable.
                        </p>
                        <CodeBlock title="Example Output" language="text">
{`Database: ./data/sandbox.db
Total Size:   2.4 MB
WAL File:     512 KB
Page Size:    4096 bytes`}
</CodeBlock>
                        <ul className="db-cmd-notes">
                            <li>Reports main DB file size</li>
                            <li>Optionally shows WAL file size</li>
                            <li>Helps monitor database growth over time</li>
                        </ul>
                    </div>
                </div>
            </section>

            <section className="content-section">
                <h2 className="section-title">Database Internals</h2>
                <h3 className="subsection-title">Schema Overview</h3>
                <CodeBlock title="Database Schema" language="text">
{`-- conversations table
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    topic TEXT,
    created_at TEXT,
    updated_at TEXT,
    turn_count INTEGER,
    status TEXT  -- 'running', 'paused', 'stopped'
);

-- messages table  
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    agent TEXT,  -- 'atlas' or 'argus'
    role TEXT,   -- 'user', 'assistant', 'system'
    content TEXT,
    turn_number INTEGER,
    timestamp TEXT,
    tool_calls TEXT  -- JSON array
);

-- evidence table
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    claim TEXT,
    source TEXT,
    agent TEXT,
    confidence REAL,
    verified INTEGER,  -- 0 or 1
    timestamp TEXT,
    tool_call_id TEXT
);

-- memories table
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    agent TEXT,
    memory_type TEXT,  -- 'fact', 'decision', 'pattern'
    content TEXT,
    importance REAL,
    timestamp TEXT
);

-- summaries table
CREATE TABLE summaries (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    summary_text TEXT,
    summary_type TEXT,  -- 'short', 'long', 'key_findings'
    token_count INTEGER,
    created_at TEXT
);

-- tool_calls table
CREATE TABLE tool_calls (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    agent TEXT,
    tool_name TEXT,
    tool_args TEXT,  -- JSON
    success INTEGER,   -- 0 or 1
    output TEXT,
    execution_time_ms INTEGER,
    timestamp TEXT
);`}
</CodeBlock>

                <h3 className="subsection-title">WAL Mode</h3>
                <p className="section-text">
                    The database operates in WAL (Write-Ahead Logging) mode by default.
                    This provides:
                </p>
                <ul className="resource-list">
                    <li>Better concurrent read performance</li>
                    <li>Crash recovery — database returns to last consistent state</li>
                    <li>No database locks during reads</li>
                    <li>Enabled by default in EvidenceManager</li>
                </ul>
                <CodeBlock title="Check WAL mode" language="text">
{`PRAGMA journal_mode;
-- returns: wal

PRAGMA wal_checkpoint(TRUNCATE);
-- Checkpoints and truncates the WAL file`}
</CodeBlock>

                <h3 className="subsection-title">Backup & Restore</h3>
                <CodeBlock title="Backup workflow" language="text">
{`# Create backup (via /db backup command or manually)
cp sandbox.db sandbox_backup.db

# Check integrity after backup
sqlite3 sandbox_backup.db "PRAGMA integrity_check;"

# Restore from backup
cp sandbox_backup.db sandbox.db

# Verify restoration
sqlite3 sandbox.db "PRAGMA integrity_check;"
PRAGMA journal_mode;  -- should return 'wal'`
</CodeBlock>
            </section>
        </div>
    );
}