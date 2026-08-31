'use client';

import React, { useEffect, useRef, useState } from 'react';
import { SandboxEvent } from '../hooks/useEventStream';

interface TimelineProps {
  events: SandboxEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const filteredEvents = events.filter(evt => {
    if (filterType === 'all') return true;
    if (filterType === 'tools') return evt.type?.startsWith('tool.');
    if (filterType === 'messages') return evt.type === 'agent.message' || evt.type === 'human.message';
    if (filterType === 'models') return evt.type?.startsWith('model.');
    return true;
  });

  const renderEventCard = (evt: SandboxEvent, i: number) => {
    const payload = evt.payload || {};
    const type = evt.type || '';

    // Model Provider Switch Event Card
    if (type === 'model.provider_switch') {
      return (
        <div key={i} className="fade-in" style={{
          padding: '12px 16px',
          borderRadius: '8px',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#f59e0b', fontWeight: 600, fontSize: '0.85rem' }}>
              ⚡ LLM Failover Triggered
            </span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{type}</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#fff' }}>
            Route <code style={{ color: '#38bdf8' }}>{payload.route}</code> switched: <b>{payload.previous_provider}</b> ➔ <b style={{ color: '#10b981' }}>{payload.active_provider}</b>
          </div>
          {payload.reason && (
            <div style={{ fontSize: '0.75rem', color: '#cbd5e1', opacity: 0.8 }}>
              Reason: {payload.reason}
            </div>
          )}
        </div>
      );
    }

    // Tool Execution Event Card
    if (type.startsWith('tool.')) {
      const isComplete = type === 'tool.completed';
      const isFailed = type === 'tool.failed';
      const statusColor = isComplete ? '#10b981' : isFailed ? '#ef4444' : '#38bdf8';

      return (
        <div key={i} className="fade-in" style={{
          padding: '12px 16px',
          borderRadius: '8px',
          background: 'rgba(15, 23, 42, 0.6)',
          border: `1px solid ${statusColor}40`,
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: statusColor, fontSize: '0.9rem' }}>🔧</span>
              <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem', fontFamily: 'monospace' }}>
                {payload.tool_name}
              </span>
              <span style={{
                fontSize: '0.7rem',
                padding: '1px 6px',
                borderRadius: '4px',
                background: `${statusColor}20`,
                color: statusColor,
                fontWeight: 600
              }}>
                {type.replace('tool.', '').toUpperCase()}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{payload.agent_id || 'System'}</span>
          </div>

          {payload.arguments && (
            <div style={{ fontSize: '0.8rem', color: '#cbd5e1', background: 'rgba(0,0,0,0.3)', padding: '6px 10px', borderRadius: '4px', fontFamily: 'monospace' }}>
              {JSON.stringify(payload.arguments)}
            </div>
          )}

          {payload.result && (
            <div style={{ fontSize: '0.8rem', color: '#a7f3d0', background: 'rgba(0,0,0,0.4)', padding: '8px 10px', borderRadius: '4px', fontFamily: 'monospace', whiteSpace: 'pre-wrap', maxHeight: '150px', overflowY: 'auto' }}>
              {typeof payload.result === 'object' ? JSON.stringify(payload.result, null, 2) : String(payload.result)}
            </div>
          )}

          {payload.error && (
            <div style={{ fontSize: '0.8rem', color: '#fca5a5', background: 'rgba(239, 68, 68, 0.1)', padding: '6px 10px', borderRadius: '4px', fontFamily: 'monospace' }}>
              {String(payload.error)}
            </div>
          )}
        </div>
      );
    }

    // Default Agent Message / Event Card
    const isHuman = type === 'human.message' || payload.agent_id === 'human';
    const isObserver = payload.agent_id === 'agent_c' || type?.includes('observer');
    const agentColor = isHuman ? '#ec4899' : isObserver ? '#a855f7' : 'var(--accent)';

    return (
      <div key={i} className="fade-in" style={{
        padding: '14px 16px',
        border: '1px solid var(--glass-border)',
        borderRadius: '8px',
        background: isHuman ? 'rgba(236, 72, 153, 0.05)' : 'rgba(0,0,0,0.25)',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: agentColor, fontWeight: 600, fontSize: '0.95rem' }}>
            {payload.identity || payload.agent_id || 'System'}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{type}</span>
        </div>

        {payload.content && (
          <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.5, color: '#f1f5f9' }}>
            {payload.content}
          </div>
        )}
        {payload.message && !payload.content && (
          <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.5, color: '#f1f5f9' }}>
            {payload.message}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Live Event Timeline</h2>
        <div style={{ display: 'flex', gap: '6px' }}>
          {['all', 'messages', 'tools', 'models'].map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterType(tab)}
              style={{
                background: filterType === tab ? 'var(--accent)' : 'rgba(255,255,255,0.05)',
                color: filterType === tab ? '#fff' : 'var(--text-muted)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '3px 10px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
          Waiting for events from message bus...
        </div>
      ) : (
        filteredEvents.map((evt, i) => renderEventCard(evt, i))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
