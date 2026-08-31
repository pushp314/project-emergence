'use client';

import React, { useState } from 'react';
import { useEventStream } from '../hooks/useEventStream';
import { Timeline } from '../components/Timeline';
import { SystemStatus } from '../components/SystemStatus';
import { ToolPalette } from '../components/ToolPalette';
import { MemoryExplorer } from '../components/MemoryExplorer';
import { SelfModificationsExplorer } from '../components/SelfModificationsExplorer';
import { ReportsAndBenchmarks } from '../components/ReportsAndBenchmarks';
import { PermissionModal } from '../components/PermissionModal';

type TabView = 'timeline' | 'tools' | 'memory' | 'modifications' | 'benchmarks';

export default function Home() {
  const { events, isConnected, clearEvents } = useEventStream('ws://localhost:8001/ws/events');
  const [activeTab, setActiveTab] = useState<TabView>('timeline');
  const [chatMessage, setChatMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim() || sending) return;
    try {
      setSending(true);
      await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: chatMessage })
      });
      setChatMessage('');
    } catch (err) {
      console.error(err);
    } finally {
      setSending(false);
    }
  };

  return (
    <main style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '20px', gap: '16px' }}>
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.8rem', color: 'var(--accent)', fontWeight: 700, letterSpacing: '-0.5px' }}>
              🧠 AI Sandbox Mission Control
            </h1>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>WebSocket: {isConnected ? <b style={{ color: 'var(--success)' }}>🟢 Connected</b> : <b style={{ color: 'var(--danger)' }}>🔴 Disconnected</b>}</span>
              <span>•</span>
              <span>Autonomous Multi-Agent Runtime</span>
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)', gap: '4px', flexWrap: 'wrap' }}>
          <button
            className="btn"
            onClick={() => setActiveTab('timeline')}
            style={{
              background: activeTab === 'timeline' ? 'var(--accent)' : 'transparent',
              color: activeTab === 'timeline' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.82rem'
            }}
          >
            📡 Live Timeline
          </button>
          <button
            className="btn"
            onClick={() => setActiveTab('tools')}
            style={{
              background: activeTab === 'tools' ? 'var(--accent)' : 'transparent',
              color: activeTab === 'tools' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.82rem'
            }}
          >
            🛠️ Tools (11)
          </button>
          <button
            className="btn"
            onClick={() => setActiveTab('memory')}
            style={{
              background: activeTab === 'memory' ? 'var(--accent)' : 'transparent',
              color: activeTab === 'memory' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.82rem'
            }}
          >
            🧠 Memory & Vectors
          </button>
          <button
            className="btn"
            onClick={() => setActiveTab('modifications')}
            style={{
              background: activeTab === 'modifications' ? 'var(--accent)' : 'transparent',
              color: activeTab === 'modifications' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.82rem'
            }}
          >
            🔄 Self-Mod & DB
          </button>
          <button
            className="btn"
            onClick={() => setActiveTab('benchmarks')}
            style={{
              background: activeTab === 'benchmarks' ? 'var(--accent)' : 'transparent',
              color: activeTab === 'benchmarks' ? '#fff' : 'var(--text-muted)',
              border: 'none',
              padding: '6px 12px',
              fontSize: '0.82rem'
            }}
          >
            📊 Benchmarks & Reports
          </button>
        </div>

        <button className="btn" onClick={clearEvents} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
          Clear Feed
        </button>
      </header>

      {/* Main Content Area */}
      <div style={{ display: 'flex', flex: 1, gap: '16px', minHeight: 0 }}>
        {/* Active Tab View */}
        {activeTab === 'timeline' && <Timeline events={events} />}
        {activeTab === 'tools' && <ToolPalette />}
        {activeTab === 'memory' && <MemoryExplorer />}
        {activeTab === 'modifications' && <SelfModificationsExplorer />}
        {activeTab === 'benchmarks' && <ReportsAndBenchmarks />}

        {/* Right Sidebar: System Status & Chat Controller */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '320px', minWidth: '320px' }}>
          <SystemStatus />
          
          <div className="glass-panel" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#fff' }}>🎯 Goal & Agent Dispatch</h3>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.4 }}>
              Inject tasks, code requests, or exploration objectives to the multi-agent bus:
            </div>
            
            <form onSubmit={handleChatSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'auto' }}>
              <textarea
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Type instructions (e.g., 'Build a snake game in Python')..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: 'rgba(0,0,0,0.3)',
                  color: 'white',
                  fontSize: '0.85rem',
                  resize: 'none'
                }}
              />
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={sending || !chatMessage.trim()}
                style={{ padding: '8px 16px', width: '100%' }}
              >
                {sending ? 'Sending...' : '🚀 Dispatch Goal'}
              </button>
            </form>
          </div>
        </div>
      </div>

      <PermissionModal />
    </main>
  );
}
