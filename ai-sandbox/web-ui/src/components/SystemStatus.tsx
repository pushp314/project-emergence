'use client';

import React, { useEffect, useState } from 'react';

interface TierData {
  name: string;
  model_name: string;
  state: 'closed' | 'open' | 'half_open';
  cooldown_remaining: number;
  total_requests: number;
  total_fallbacks: number;
  last_error?: string;
  details?: any;
}

interface ModelRouteData {
  active_tier?: string;
  total_tiers?: number;
  tiers?: TierData[];
  key_pool?: {
    total_keys: number;
    active_keys: number;
    cooling_keys: number;
    keys: Array<{ masked: string; status: string; cooldown_remaining: number }>;
  };
}

export function SystemStatus() {
  const [status, setStatus] = useState<any>(null);
  const [modelStatus, setModelStatus] = useState<Record<string, ModelRouteData>>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('http://localhost:8001/api/status');
        const data = await res.json();
        setStatus(data);
      } catch (err) {
        // server might be starting or paused
      }

      try {
        const resModel = await fetch('http://localhost:8001/api/models/status');
        const modelData = await resModel.json();
        setModelStatus(modelData.routes || {});
      } catch (err) {
        // model status endpoint error
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!status) {
    return (
      <div className="glass-panel" style={{ padding: '20px', width: '320px' }}>
        <h2>System Status</h2>
        <div style={{ color: 'var(--text-muted)' }}>Connecting to Mission Control...</div>
      </div>
    );
  }

  const handleStart = async () => {
    try {
      await fetch('http://localhost:8001/api/start', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handlePause = async () => {
    try {
      await fetch('http://localhost:8001/api/pause', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const defaultRoute = modelStatus['default'];
  const activeTier = defaultRoute?.active_tier || 'gemini';
  const tiers = defaultRoute?.tiers || [];

  const getProviderBadge = (tierName: string) => {
    if (tierName.includes('gemini') || tierName === 'default') {
      return { label: 'Gemini 2.5 Flash', color: '#10b981', tag: 'Cloud' };
    }
    if (tierName.includes('openrouter')) {
      return { label: 'OpenRouter Gemma 4', color: '#3b82f6', tag: 'Cloud Fallback' };
    }
    if (tierName.includes('ollama') || tierName.includes('local')) {
      return { label: 'Ollama Local', color: '#f59e0b', tag: 'Local Offline' };
    }
    return { label: tierName, color: '#8b5cf6', tag: 'Model' };
  };

  const activeBadge = getProviderBadge(activeTier);

  return (
    <div className="glass-panel" style={{ padding: '20px', width: '320px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Mission Status</h2>
        <span style={{ 
          background: status.running ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: status.running ? '#10b981' : '#ef4444',
          fontSize: '0.75rem',
          padding: '2px 8px',
          borderRadius: '12px',
          fontWeight: 600
        }}>
          {status.state.toUpperCase()}
        </span>
      </div>

      {/* Model Router & Circuit Breaker Badge */}
      <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active LLM Provider</span>
          <span style={{ fontSize: '0.7rem', color: activeBadge.color, background: `${activeBadge.color}15`, padding: '1px 6px', borderRadius: '4px' }}>
            {activeBadge.tag}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: activeBadge.color, display: 'inline-block', boxShadow: `0 0 8px ${activeBadge.color}` }}></span>
          {activeBadge.label}
        </div>

        {/* Fallback Tiers Pipeline */}
        {tiers.length > 0 && (
          <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Failover Chain:</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {tiers.map((t, idx) => {
                const isSelected = t.name === activeTier;
                const isCooling = t.state === 'open' && t.cooldown_remaining > 0;
                return (
                  <div key={idx} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    fontSize: '0.75rem',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: isSelected ? 'rgba(255,255,255,0.08)' : 'transparent',
                    opacity: isCooling ? 0.6 : 1
                  }}>
                    <span style={{ color: isSelected ? '#fff' : 'var(--text-muted)' }}>
                      {idx + 1}. {t.name.replace('_route', '').replace('local_', '')}
                    </span>
                    <span>
                      {isCooling ? (
                        <span style={{ color: '#ef4444', fontSize: '0.7rem' }}>CD: {t.cooldown_remaining}s</span>
                      ) : isSelected ? (
                        <span style={{ color: '#10b981', fontWeight: 600 }}>Active</span>
                      ) : (
                        <span style={{ color: '#6b7280' }}>Ready</span>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Conversation ID</div>
        <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: '#9ca3af', wordBreak: 'break-all' }}>
          {status.conversation_id}
        </div>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Current Speaker</div>
          <div style={{ color: '#38bdf8', fontWeight: 600, fontSize: '0.9rem' }}>{status.current_speaker}</div>
        </div>
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Turn Count</div>
          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{status.turn_number}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
        <button className="btn btn-primary" style={{ flex: 1, padding: '8px' }} onClick={handleStart}>
          ▶ Start
        </button>
        <button className="btn" style={{ flex: 1, padding: '8px' }} onClick={handlePause}>
          ⏸ Pause
        </button>
      </div>
    </div>
  );
}
