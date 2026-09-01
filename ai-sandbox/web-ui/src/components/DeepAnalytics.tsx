'use client';

import React, { useState, useEffect, useCallback } from 'react';

type Section = 'overview' | 'models' | 'tools' | 'memory' | 'peers';

const riskTag = (r: string) => {
  if (r === 'high')   return 'tag tag-red';
  if (r === 'medium') return 'tag tag-amber';
  return 'tag tag-green';
};

export function DeepAnalytics() {
  const [section, setSection] = useState<Section>('overview');
  const [models,  setModels]  = useState<Record<string, any>>({});
  const [tools,   setTools]   = useState<any[]>([]);
  const [memory,  setMemory]  = useState<any>(null);
  const [db,      setDb]      = useState<any>(null);
  const [peers,   setPeers]   = useState<any[]>([]);
  const [sessions,setSessions]= useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = useCallback(async () => {
    try {
      const r = await fetch('http://localhost:8001/api/analytics/metrics');
      const d = await r.json();
      if (d.success) setMetrics(d);
    } catch (e) {}
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const results = await Promise.allSettled([
      fetch('http://localhost:8001/api/models/status').then(r => r.json()),
      fetch('http://localhost:8001/api/tools').then(r => r.json()),
      fetch('http://localhost:8001/api/memory').then(r => r.json()),
      fetch('http://localhost:8001/api/db/health').then(r => r.json()),
      fetch('http://localhost:8001/api/a2a/peers').then(r => r.json()),
      fetch('http://localhost:8001/api/sessions').then(r => r.json()),
    ]);
    if (results[0].status === 'fulfilled') setModels(results[0].value.routes || {});
    if (results[1].status === 'fulfilled') setTools(results[1].value.tools || []);
    if (results[2].status === 'fulfilled') setMemory(results[2].value);
    if (results[3].status === 'fulfilled') setDb(results[3].value);
    if (results[4].status === 'fulfilled') setPeers(results[4].value.peers || []);
    if (results[5].status === 'fulfilled') setSessions(results[5].value.sessions || []);
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 2000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  const tabs: { id: Section; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'models',   label: 'Models'   },
    { id: 'tools',    label: 'Tools'    },
    { id: 'memory',   label: 'Memory'   },
    { id: 'peers',    label: 'Peers'    },
  ];

  const overview_stats = [
    { label: 'Active Tools',    value: tools.filter(t => t.enabled).length, total: tools.length,   accent: 'var(--blue-400)' },
    { label: 'Vector Memories', value: metrics?.database?.total_vector_memories ?? (memory?.vector_store_entries ?? '—'),  total: null,           accent: 'var(--violet-light)' },
    { label: 'Autonomous Sessions', value: metrics?.database?.total_sessions ?? sessions.length, total: null,           accent: 'var(--text-secondary)' },
    { label: 'A2A Peers',       value: peers.length,                         total: null,           accent: 'var(--blue-400)' },
    { label: 'Model Routes',    value: Object.keys(models).length,           total: null,           accent: 'var(--text-secondary)' },
    { label: 'DB Size',         value: db?.file_size_kb ? `${db.file_size_kb}kb` : '—', total: null, accent: 'var(--text-secondary)' },
  ];

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Header */}
      <div style={{
        padding: '14px 24px 0',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-base)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
          <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Analytics
          </span>
          <button
            onClick={fetchAll}
            className="btn"
            style={{ marginLeft: 'auto', fontSize: '0.75rem', padding: '3px 10px' }}
          >
            {loading ? <span className="anim-spin" style={{ display: 'inline-block' }}>◌</span> : '↻'} Refresh
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-faint)', marginBottom: -1 }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setSection(t.id)}
              style={{
                padding: '7px 14px',
                background: 'none', border: 'none',
                borderBottom: section === t.id ? '2px solid var(--blue-600)' : '2px solid transparent',
                color: section === t.id ? 'var(--text-primary)' : 'var(--text-muted)',
                fontWeight: section === t.id ? 600 : 400,
                fontSize: '0.8125rem', cursor: 'pointer', transition: 'color 0.12s',
                fontFamily: 'inherit', letterSpacing: '-0.005em',
                marginBottom: -1,
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '22px 24px' }} className="anim-fade-in">

        {/* OVERVIEW */}
        {section === 'overview' && (
          <div>
            {metrics?.system && (
              <div style={{ marginBottom: 24, display: 'flex', gap: 16 }}>
                <div className="card" style={{ flex: 1, padding: 16, borderRadius: 'var(--r-lg)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    CPU Usage
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--blue-400)', lineHeight: 1 }}>
                      {metrics.system.cpu_percent.toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ marginTop: 12, height: 6, background: 'var(--bg-root)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'var(--blue-500)', width: `${metrics.system.cpu_percent}%`, transition: 'width 0.3s' }} />
                  </div>
                </div>
                
                <div className="card" style={{ flex: 1, padding: 16, borderRadius: 'var(--r-lg)' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    RAM Usage
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--violet-light)', lineHeight: 1 }}>
                      {metrics.system.ram_percent.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', paddingBottom: 4 }}>
                      {metrics.system.ram_used_gb} / {metrics.system.ram_total_gb} GB
                    </div>
                  </div>
                  <div style={{ marginTop: 12, height: 6, background: 'var(--bg-root)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'var(--violet-500)', width: `${metrics.system.ram_percent}%`, transition: 'width 0.3s' }} />
                  </div>
                </div>
              </div>
            )}
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 24 }}>
              {overview_stats.map(s => (
                <div key={s.label} className="stat-card">
                  <div className="stat-value" style={{ color: s.accent }}>
                    {loading ? <span className="skeleton" style={{ width: 40, height: 24, display: 'inline-block' }} /> : s.value}
                  </div>
                  <div className="stat-label">{s.label}</div>
                  {s.total !== null && (
                    <div className="stat-sub">{s.total} registered</div>
                  )}
                </div>
              ))}
            </div>

            {/* DB tables */}
            {db?.tables && (
              <div style={{ marginBottom: 22 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>
                  Database Tables
                </div>
                <div className="card" style={{ borderRadius: 'var(--r-lg)', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                    <thead>
                      <tr>
                        <th style={{ padding: '8px 14px', textAlign: 'left', fontWeight: 600, fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>Table</th>
                        <th style={{ padding: '8px 14px', textAlign: 'right', fontWeight: 600, fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>Rows</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(db.tables).map(([t, c]) => (
                        <tr key={t} style={{ borderBottom: '1px solid var(--border-faint)' }}>
                          <td style={{ padding: '8px 14px', color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem' }}>{t}</td>
                          <td style={{ padding: '8px 14px', color: 'var(--blue-400)', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem', textAlign: 'right', fontWeight: 600 }}>{String(c)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Sessions */}
            {sessions.length > 0 && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>
                  Recent Sessions
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {sessions.slice(0, 6).map((s: any, i) => (
                    <div key={i} className="card" style={{ padding: '9px 14px', borderRadius: 'var(--r-md)', display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', color: 'var(--text-faint)' }}>
                        {(s.session_id || String(i)).slice(0, 8)}
                      </span>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', flex: 1 }}>
                        Session #{s.session_number || i + 1}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)' }}>
                        {s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* MODELS */}
        {section === 'models' && (
          <div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: 18 }}>
              Active model routes with resilient multi-provider routing and automatic fallback.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.entries(models).map(([route, info]) => (
                <div key={route} className="card" style={{ padding: '14px 16px', borderRadius: 'var(--r-lg)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{route}</span>
                    {info.name && (
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {info.name}
                      </span>
                    )}
                    <span className="tag tag-blue" style={{ marginLeft: 'auto' }}>
                      {info.backend || 'active'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 14, fontSize: '0.75rem', color: 'var(--text-faint)', flexWrap: 'wrap' }}>
                    {info.context_window && (
                      <span>{(info.context_window / 1000).toFixed(0)}K ctx</span>
                    )}
                    {info.type && <span>{info.type}</span>}
                    {info.key_pool?.total_keys && <span>{info.key_pool.total_keys} keys</span>}
                  </div>
                </div>
              ))}
              {Object.keys(models).length === 0 && (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-faint)', fontSize: '0.875rem' }}>
                  No model routes found
                </div>
              )}
            </div>
          </div>
        )}

        {/* TOOLS */}
        {section === 'tools' && (
          <div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: 18 }}>
              {tools.filter(t => t.enabled).length} of {tools.length} tools are enabled in the ToolGateway.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {tools.map((t, i) => (
                <div key={i} className="tool-row" style={{ opacity: t.enabled ? 1 : 0.45, borderRadius: 'var(--r-md)' }}>
                  <span className={`dot ${t.enabled ? 'dot-green' : 'dot-muted'}`} />
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500, width: 160, flexShrink: 0 }}>
                    {t.name}
                  </span>
                  <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--text-faint)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {t.description?.slice(0, 60)}
                  </span>
                  <span className={riskTag(t.risk)}>{t.risk}</span>
                  <span className="tag tag-muted" style={{ marginLeft: 4 }}>{t.permission}</span>
                </div>
              ))}
              {tools.length === 0 && (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-faint)', fontSize: '0.875rem' }}>
                  No tools registered
                </div>
              )}
            </div>
          </div>
        )}

        {/* MEMORY */}
        {section === 'memory' && (
          <div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: 18 }}>
              Short-term conversation context and long-term vector memory (RAG).
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 20 }}>
              {[
                { label: 'Current Turn',   value: memory?.turn ?? '—',                    accent: 'var(--blue-400)' },
                { label: 'Vector Entries', value: memory?.vector_store_entries ?? '—',    accent: 'var(--violet-light)' },
                { label: 'Context Keys',   value: memory?.context ? Object.keys(memory.context).length : '—', accent: 'var(--text-secondary)' },
              ].map(s => (
                <div key={s.label} className="stat-card" style={{ textAlign: 'center' }}>
                  <div className="stat-value" style={{ color: s.accent }}>{s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              ))}
            </div>

            {memory?.context && Object.keys(memory.context).length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>
                  Raw Context
                </div>
                <div style={{
                  background: '#0a0a0c', border: '1px solid var(--border-base)',
                  borderRadius: 'var(--r-md)', padding: '13px 16px',
                  maxHeight: 300, overflowY: 'auto',
                }}>
                  <pre style={{
                    fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem',
                    color: 'var(--zinc-500)', lineHeight: 1.7, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>
                    {JSON.stringify(memory.context, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {memory?.context?.summary && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>
                  Memory Summary
                </div>
                <div className="card" style={{ padding: '12px 16px', borderRadius: 'var(--r-md)', fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  {memory.context.summary}
                </div>
              </div>
            )}

            {!memory && (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-faint)', fontSize: '0.875rem' }}>
                No memory data available
              </div>
            )}
          </div>
        )}

        {/* PEERS */}
        {section === 'peers' && (
          <div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.7, marginBottom: 18 }}>
              Agent-to-Agent (A2A) network. Peer agents can collaborate on complex tasks.
            </p>
            {peers.length === 0 ? (
              <div className="card" style={{ padding: '28px 20px', textAlign: 'center', borderRadius: 'var(--r-lg)' }}>
                <div style={{ color: 'var(--text-faint)', fontSize: '0.875rem' }}>
                  No A2A peers registered
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {peers.map((p: any) => (
                  <div key={p.agent_id} className="card" style={{ padding: '14px 16px', borderRadius: 'var(--r-lg)' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{
                        width: 34, height: 34, borderRadius: 'var(--r-md)', flexShrink: 0,
                        background: 'var(--bg-overlay)', border: '1px solid var(--border-base)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.9rem', color: 'var(--text-muted)',
                      }}>⚡</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{p.name}</span>
                          <span className="tag tag-muted" style={{ marginLeft: 'auto' }}>v{p.version}</span>
                        </div>
                        {p.description && (
                          <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 8 }}>
                            {p.description}
                          </div>
                        )}
                        {p.capabilities?.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {p.capabilities.slice(0, 5).map((c: string) => (
                              <span key={c} className="tag tag-muted">{c}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
