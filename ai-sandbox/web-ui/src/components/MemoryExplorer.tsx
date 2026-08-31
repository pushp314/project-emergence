'use client';

import React, { useEffect, useState } from 'react';

export function MemoryExplorer() {
  const [memory, setMemory] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchMemoryData = async () => {
    try {
      setLoading(true);
      const [memRes, evRes] = await Promise.all([
        fetch('http://localhost:8001/api/memory').then(r => r.json()).catch(() => null),
        fetch('http://localhost:8001/api/evidence').then(r => r.json()).catch(() => null),
      ]);
      if (memRes) setMemory(memRes);
      if (evRes && evRes.evidence) setEvidence(evRes.evidence);
    } catch (err) {
      console.error('Failed to load memory data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemoryData();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      setSearching(true);
      const res = await fetch('http://localhost:8001/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 5 })
      });
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const context = memory?.context || {};
  const facts = context.important_facts || [];
  const openQuestions = context.open_questions || [];

  return (
    <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent)', margin: 0 }}>Memory & Knowledge Base</h2>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
            SQLite Long-Term Store & Semantic Vector Embeddings ({memory?.vector_store_entries || 0} items)
          </div>
        </div>
        <button className="btn" onClick={fetchMemoryData} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
          🔄 Refresh
        </button>
      </div>

      {/* Semantic Vector Search Box */}
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Semantic vector search across agent memory embeddings..."
          style={{
            flex: 1,
            padding: '10px 14px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(0,0,0,0.3)',
            color: 'white',
            fontSize: '0.9rem'
          }}
        />
        <button type="submit" className="btn btn-primary" style={{ padding: '10px 20px' }} disabled={searching}>
          {searching ? 'Searching...' : '🔍 Search'}
        </button>
      </form>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div style={{ background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '10px', padding: '14px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8', marginBottom: '8px' }}>
            Vector Search Matches for &quot;{searchQuery}&quot;:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {searchResults.map((r, i) => (
              <div key={i} style={{ fontSize: '0.82rem', color: '#e2e8f0', background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '6px' }}>
                {typeof r === 'object' ? (r.text || JSON.stringify(r)) : String(r)}
              </div>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>Loading memory state...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {/* Active Summary Card */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px' }}>
            <h3 style={{ fontSize: '1rem', color: '#fff', margin: '0 0 10px 0' }}>🧠 Conversation Summary</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.5, margin: 0 }}>
              {context.summary || 'No conversation summary recorded yet. Old turns are periodically condensed.'}
            </p>
          </div>

          {/* Important Facts Card */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px' }}>
            <h3 style={{ fontSize: '1rem', color: '#fff', margin: '0 0 10px 0' }}>📌 Extracted Facts & Context ({facts.length})</h3>
            {facts.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No facts extracted yet.</div>
            ) : (
              <ul style={{ paddingLeft: '18px', margin: 0, color: '#cbd5e1', fontSize: '0.85rem', lineHeight: 1.5 }}>
                {facts.map((f: string, idx: number) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{f}</li>
                ))}
              </ul>
            )}
          </div>

          {/* Open Questions Card */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px' }}>
            <h3 style={{ fontSize: '1rem', color: '#fff', margin: '0 0 10px 0' }}>❓ Open Questions ({openQuestions.length})</h3>
            {openQuestions.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No active questions.</div>
            ) : (
              <ul style={{ paddingLeft: '18px', margin: 0, color: '#f59e0b', fontSize: '0.85rem', lineHeight: 1.5 }}>
                {openQuestions.map((q: string, idx: number) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{q}</li>
                ))}
              </ul>
            )}
          </div>

          {/* Evidence Card */}
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px' }}>
            <h3 style={{ fontSize: '1rem', color: '#fff', margin: '0 0 10px 0' }}>🔬 Discovered Evidence ({evidence.length})</h3>
            {evidence.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No evidence logged in current session.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                {evidence.slice(0, 10).map((e: any, idx: number) => (
                  <div key={idx} style={{ fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', padding: '6px 10px', borderRadius: '6px' }}>
                    <span style={{ color: '#38bdf8', fontWeight: 600 }}>{e.agent_id || 'System'}:</span>{' '}
                    <span style={{ color: '#e2e8f0' }}>{e.intent || e.reason || JSON.stringify(e)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
