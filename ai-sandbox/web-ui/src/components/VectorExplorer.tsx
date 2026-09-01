'use client';

import React, { useState, useEffect } from 'react';

interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
  distance?: number;
}

export function VectorExplorer() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const r = await fetch('http://localhost:8001/api/memory/vectors');
      const d = await r.json();
      setMemories(d.memories || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) {
      return fetchAll();
    }
    setSearching(true);
    try {
      const r = await fetch('http://localhost:8001/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 20 })
      });
      const d = await r.json();
      setMemories(d.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this memory forever?')) return;
    try {
      const r = await fetch(`http://localhost:8001/api/memory/vectors/${id}`, { method: 'DELETE' });
      const d = await r.json();
      if (d.success) {
        setMemories(prev => prev.filter(m => m.id !== id));
      } else {
        alert('Failed to delete memory.');
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-root)' }}>
      <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.02em', marginBottom: 8 }}>
          Vector Memory Brain
        </h2>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 20 }}>
          Direct semantic access to what the agents have memorized.
        </div>
        
        <div style={{ display: 'flex', gap: 12 }}>
          <input 
            className="input" 
            placeholder="Search the vector store semantically..." 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            style={{ flex: 1, maxWidth: 400 }}
          />
          <button className="btn" onClick={handleSearch} disabled={searching || loading}>
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
        {loading ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Loading memories...</div>
        ) : memories.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No memories found.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {memories.map(m => (
              <div key={m.id} style={{ 
                background: 'var(--bg-surface)', 
                border: '1px solid var(--border-base)', 
                borderRadius: 'var(--r-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 12
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--blue-400)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                    Memory ID: {m.id.split('-')[0]}...
                  </div>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    {m.distance !== undefined && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--green-light)', background: 'rgba(34,197,94,0.1)', padding: '2px 6px', borderRadius: 4 }}>
                        Relevance: {m.distance.toFixed(3)}
                      </span>
                    )}
                    <button 
                      onClick={() => handleDelete(m.id)}
                      style={{ background: 'none', border: 'none', color: 'var(--text-faint)', cursor: 'pointer', fontSize: '0.8rem' }}
                      onMouseEnter={e => e.currentTarget.style.color = 'var(--red-light)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'var(--text-faint)'}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {m.content}
                </div>

                {Object.keys(m.metadata).length > 0 && (
                  <div style={{ 
                    marginTop: 4, padding: '8px 12px', background: 'var(--bg-root)', 
                    borderRadius: 'var(--r-sm)', fontSize: '0.75rem', color: 'var(--text-muted)' 
                  }}>
                    <pre style={{ margin: 0, fontFamily: 'var(--font-mono)' }}>
                      {JSON.stringify(m.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
