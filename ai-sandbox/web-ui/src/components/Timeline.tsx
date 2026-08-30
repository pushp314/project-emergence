'use client';

import React, { useEffect, useRef } from 'react';
import { SandboxEvent } from '../hooks/useEventStream';

interface TimelineProps {
  events: SandboxEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  return (
    <div className="glass-panel" style={{ padding: '20px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h2 style={{ marginBottom: '10px' }}>Event Timeline</h2>
      {events.length === 0 ? (
        <div style={{ color: 'var(--text-muted)' }}>Waiting for events...</div>
      ) : (
        events.map((evt, i) => (
          <div key={i} className="fade-in" style={{ padding: '12px', border: '1px solid var(--glass-border)', borderRadius: '8px', background: 'rgba(0,0,0,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>{evt.agent_id || 'System'}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{evt.type}</span>
            </div>
            {evt.intent && <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: '4px' }}>{evt.intent}</div>}
            {evt.content && <div style={{ whiteSpace: 'pre-wrap' }}>{evt.content}</div>}
            {evt.tool_name && <div style={{ color: 'var(--warning)', marginTop: '8px' }}>🔧 {evt.tool_name}({JSON.stringify(evt.tool_args || {})})</div>}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
