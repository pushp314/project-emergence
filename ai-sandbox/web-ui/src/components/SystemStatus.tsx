'use client';

import React, { useEffect, useState } from 'react';

export function SystemStatus() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8001/api/status');
        const data = await res.json();
        setStatus(data);
      } catch (err) {
        console.error('Failed to fetch status', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!status) {
    return (
      <div className="glass-panel" style={{ padding: '20px', width: '300px' }}>
        <h2>System Status</h2>
        <div style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '20px', width: '300px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h2>System Status</h2>
      
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Conversation ID</div>
        <div style={{ fontSize: '0.9rem', wordBreak: 'break-all' }}>{status.conversation_id}</div>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>State</div>
          <div style={{ color: status.state === 'running' ? 'var(--success)' : 'var(--warning)' }}>
            {status.state.toUpperCase()}
          </div>
        </div>
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Turn</div>
          <div>{status.turn_number}</div>
        </div>
      </div>

      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Current Speaker</div>
        <div style={{ color: 'var(--accent)' }}>{status.current_speaker}</div>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
        <button className="btn btn-primary" style={{ flex: 1 }}>Start</button>
        <button className="btn" style={{ flex: 1 }}>Pause</button>
      </div>
    </div>
  );
}
