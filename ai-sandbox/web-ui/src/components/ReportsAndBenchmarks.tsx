'use client';

import React, { useEffect, useState } from 'react';

export function ReportsAndBenchmarks() {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [benchmarking, setBenchmarking] = useState(false);
  const [capabilities, setCapabilities] = useState<any>(null);
  const [reportContent, setReportContent] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [a2aPeers, setA2aPeers] = useState<any[]>([]);
  const [researchQuery, setResearchQuery] = useState('');
  const [researchResult, setResearchResult] = useState<any>(null);
  const [researching, setResearching] = useState(false);

  const fetchCapabilitiesAndReports = async () => {
    try {
      const [capRes, peerRes] = await Promise.all([
        fetch('http://localhost:8001/api/capabilities').then(r => r.json()).catch(() => null),
        fetch('http://localhost:8001/api/a2a/peers').then(r => r.json()).catch(() => null),
      ]);
      if (capRes) setCapabilities(capRes);
      if (peerRes && peerRes.peers) setA2aPeers(peerRes.peers);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchCapabilitiesAndReports();
  }, []);

  const handleRunBenchmarks = async () => {
    try {
      setBenchmarking(true);
      const res = await fetch('http://localhost:8001/api/benchmarks/run');
      const data = await res.json();
      if (data.success) {
        setBenchmarks(data.benchmarks);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setBenchmarking(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      const res = await fetch('http://localhost:8001/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.success) {
        setReportContent(data.content);
        fetchCapabilitiesAndReports();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleTriggerResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!researchQuery.trim()) return;
    try {
      setResearching(true);
      setResearchResult(null);
      const res = await fetch('http://localhost:8001/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: researchQuery, max_sources: 5 })
      });
      const data = await res.json();
      setResearchResult(data);
    } catch (err: any) {
      setResearchResult({ success: false, error: err.message });
    } finally {
      setResearching(false);
    }
  };

  return (
    <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent)', margin: 0 }}>📊 Benchmarks, Deep Research & Reports</h2>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
            In-Memory Core Throughput, Autonomous Multi-Source Research & A2A Agent Cards
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-primary" onClick={handleRunBenchmarks} disabled={benchmarking} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
            {benchmarking ? '⚡ Benchmarking...' : '⚡ Run System Benchmark'}
          </button>
          <button className="btn" onClick={handleGenerateReport} disabled={generatingReport} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
            {generatingReport ? '📄 Generating...' : '📄 Generate Session Report'}
          </button>
        </div>
      </div>

      {/* Deep Research Mission Dispatcher */}
      <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '16px' }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '1rem', color: '#fff' }}>🔬 Trigger Autonomous Deep Research Mission</h3>
        <form onSubmit={handleTriggerResearch} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={researchQuery}
            onChange={(e) => setResearchQuery(e.target.value)}
            placeholder="Research topic (e.g. 'Latest developments in small LLM reasoning')..."
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(0,0,0,0.3)',
              color: 'white',
              fontSize: '0.85rem'
            }}
          />
          <button type="submit" className="btn btn-primary" disabled={researching || !researchQuery.trim()} style={{ padding: '10px 18px' }}>
            {researching ? 'Researching...' : '🚀 Start Research'}
          </button>
        </form>

        {researchResult && (
          <div style={{ marginTop: '12px', padding: '12px', borderRadius: '8px', background: researchResult.success ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)', border: `1px solid ${researchResult.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
            <div style={{ fontWeight: 600, color: researchResult.success ? '#10b981' : '#ef4444', fontSize: '0.85rem', marginBottom: '6px' }}>
              {researchResult.success ? `✓ Research Completed: ${researchResult.question}` : '✗ Research Failed:'}
            </div>
            {researchResult.success ? (
              <div style={{ fontSize: '0.8rem', color: '#e2e8f0', display: 'flex', gap: '16px' }}>
                <span>Status: <b style={{ color: '#38bdf8' }}>{researchResult.status}</b></span>
                <span>Sources: <b style={{ color: '#38bdf8' }}>{researchResult.sources_count}</b></span>
                <span>Claims Verified: <b style={{ color: '#10b981' }}>{researchResult.claims_count}</b></span>
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: '#fca5a5' }}>{researchResult.error}</div>
            )}
          </div>
        )}
      </div>

      {/* Benchmark Results Display */}
      {benchmarks && (
        <div style={{ background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '12px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#38bdf8' }}>⚡ System Throughput & Latency Benchmarks</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {Object.entries(benchmarks).map(([key, b]: [string, any]) => (
              <div key={key} style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'capitalize', fontWeight: 600 }}>{b.name || key}</div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#10b981', margin: '4px 0' }}>
                  {Math.round(b.ops_per_second).toLocaleString()} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#94a3b8' }}>ops/s</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                  Avg Latency: <b style={{ color: '#38bdf8' }}>{b.avg_latency_us.toFixed(1)} µs</b> ({b.iterations} iters)
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generated Report Viewer */}
      {reportContent && (
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '12px', padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff' }}>📄 Generated Session Audit Report</h3>
            <button className="btn" onClick={() => setReportContent(null)} style={{ padding: '2px 8px', fontSize: '0.75rem' }}>✕ Close</button>
          </div>
          <pre style={{ margin: 0, padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.4)', color: '#f1f5f9', fontSize: '0.8rem', fontFamily: 'monospace', whiteSpace: 'pre-wrap', maxHeight: '250px', overflowY: 'auto' }}>
            {reportContent}
          </pre>
        </div>
      )}

      {/* A2A Peers and Capabilities Matrix */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* A2A Agent Cards */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px' }}>
          <div style={{ fontWeight: 600, color: '#a855f7', fontSize: '0.9rem', marginBottom: '8px' }}>🤝 A2A Protocol Agent Cards ({a2aPeers.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {a2aPeers.map((p) => (
              <div key={p.agent_id} style={{ fontSize: '0.8rem', color: '#cbd5e1', background: 'rgba(0,0,0,0.25)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, color: '#fff' }}>{p.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{p.description}</div>
                <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '4px' }}>Capabilities: {p.capabilities?.join(', ')}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Models */}
        {capabilities && (
          <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px' }}>
            <div style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.9rem', marginBottom: '8px' }}>🤖 Model Capabilities ({capabilities.models?.length || 0})</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {capabilities.models?.map((m: any) => (
                <div key={m.id} style={{ fontSize: '0.8rem', color: '#cbd5e1', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'monospace' }}>{m.name}</span>
                  <span style={{ color: '#94a3b8' }}>{m.max_context} ctx • {m.specialization}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
