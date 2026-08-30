'use client';

import React from 'react';
import { useEventStream } from '../hooks/useEventStream';
import { Timeline } from '../components/Timeline';
import { SystemStatus } from '../components/SystemStatus';
import { PermissionModal } from '../components/PermissionModal';

export default function Home() {
  const { events, isConnected, clearEvents } = useEventStream('ws://localhost:8001/ws/events');

  return (
    <main style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '20px', gap: '20px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: 'var(--accent)' }}>AI Sandbox Mission Control</h1>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            WebSocket: {isConnected ? <span style={{ color: 'var(--success)' }}>Connected</span> : <span style={{ color: 'var(--danger)' }}>Disconnected</span>}
          </div>
        </div>
        <button className="btn" onClick={clearEvents}>Clear Events</button>
      </header>

      <div style={{ display: 'flex', flex: 1, gap: '20px', minHeight: 0 }}>
        {/* Left Column: Timeline */}
        <Timeline events={events} />

        {/* Right Column: Status & Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <SystemStatus />
          
          <div className="glass-panel" style={{ padding: '20px', flex: 1, width: '300px' }}>
            <h3 style={{ marginBottom: '16px' }}>Chat</h3>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              You can monitor the agents here. Chat input coming in a future update!
            </div>
          </div>
        </div>
      </div>

      <PermissionModal />
    </main>
  );
}
