'use client';

import React, { useEffect, useState } from 'react';

export function SelfModificationsExplorer() {
  const [modData, setModData] = useState<any>(null);
  const [dbHealth, setDbHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [speechText, setSpeechText] = useState('Hello, I am your autonomous AI pair programmer.');
  const [speaking, setSpeaking] = useState(false);
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [modRes, dbRes] = await Promise.all([
        fetch('http://localhost:8001/api/modifications').then(r => r.json()).catch(() => null),
        fetch('http://localhost:8001/api/db/health').then(r => r.json()).catch(() => null)
      ]);
      if (modRes) setModData(modRes);
      if (dbRes) setDbHealth(dbRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRollback = async (modId: string) => {
    try {
      setActionStatus(`Rolling back ${modId}...`);
      const res = await fetch(`http://localhost:8001/api/modifications/${modId}/rollback`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setActionStatus(`✓ Successfully rolled back ${modId}`);
        fetchData();
      } else {
        setActionStatus(`✗ Failed to roll back: ${data.detail || data.error}`);
      }
    } catch (err: any) {
      setActionStatus(`✗ Error: ${err.message}`);
    }
  };

  const handleSpeak = async () => {
    if (!speechText.trim()) return;
    try {
      setSpeaking(true);
      await fetch('http://localhost:8001/api/audio/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: speechText })
      });
    } catch (err) {
      console.error(err);
    } finally {
      setSpeaking(false);
    }
  };

  const activeMods = modData?.active_modifications || [];
  const historyMods = modData?.history || [];

  return (
    <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent)', margin: 0 }}>🔄 Self-Modifications & System Diagnostics</h2>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
            Autonomous Code Evolution, Safety Rollbacks & Database Metrics
          </div>
        </div>
        <button className="btn" onClick={fetchData} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
          🔄 Refresh
        </button>
      </div>

      {actionStatus && (
        <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontSize: '0.85rem' }}>
          {actionStatus}
        </div>
      )}

      {/* Top Row: Database Health & Voice Synthesis */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {/* Database Health Card */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.95rem' }}>💾 SQLite DB Telemetry</span>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: dbHealth?.status === 'healthy' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: dbHealth?.status === 'healthy' ? '#10b981' : '#f59e0b' }}>
              {dbHealth?.status?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>

          <div style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'flex', gap: '16px' }}>
            <span>Size: <b style={{ color: '#fff' }}>{dbHealth?.file_size_kb || 0} KB</b></span>
            <span>Journal: <b style={{ color: '#38bdf8' }}>{dbHealth?.journal_mode || 'N/A'}</b></span>
            <span>Integrity: <b style={{ color: '#10b981' }}>{dbHealth?.integrity || 'N/A'}</b></span>
          </div>

          {dbHealth?.tables && (
            <div style={{ marginTop: '6px', fontSize: '0.78rem', color: '#cbd5e1', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {Object.entries(dbHealth.tables).map(([table, count]) => (
                <span key={table} style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 8px', borderRadius: '4px' }}>
                  {table}: <b style={{ color: '#38bdf8' }}>{String(count)}</b> rows
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Audio TTS Dispatcher Card */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.95rem' }}>🔊 Voice & Audio Engine</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={speechText}
              onChange={(e) => setSpeechText(e.target.value)}
              placeholder="Text for agent to speak..."
              style={{
                flex: 1,
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid rgba(255,255,255,0.1)',
                background: 'rgba(0,0,0,0.3)',
                color: 'white',
                fontSize: '0.85rem'
              }}
            />
            <button className="btn btn-primary" onClick={handleSpeak} disabled={speaking} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
              {speaking ? 'Speaking...' : '🎙️ Speak'}
            </button>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Powered by high-fidelity EdgeTTS / macOS Audio Subsystem
          </span>
        </div>
      </div>

      {/* Active Modifications List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h3 style={{ fontSize: '1.1rem', color: '#fff', margin: 0 }}>Active Code Modifications ({activeMods.length})</h3>
        {activeMods.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
            No autonomous code modifications currently applied to the codebase.
          </div>
        ) : (
          activeMods.map((mod: any) => (
            <div key={mod.id} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.9rem', fontFamily: 'monospace' }}>
                  {mod.file_path}
                </span>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8' }}>
                    {mod.status}
                  </span>
                  <button
                    className="btn"
                    onClick={() => handleRollback(mod.id)}
                    style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '3px 10px', fontSize: '0.75rem' }}
                  >
                    ↩️ Rollback
                  </button>
                </div>
              </div>
              <div style={{ fontSize: '0.82rem', color: '#e2e8f0' }}>Reason: {mod.reason}</div>
              {mod.diff && (
                <pre style={{ margin: 0, padding: '10px', borderRadius: '6px', background: 'rgba(0,0,0,0.5)', color: '#a7f3d0', fontSize: '0.78rem', fontFamily: 'monospace', overflowX: 'auto', maxHeight: '160px' }}>
                  {mod.diff}
                </pre>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
