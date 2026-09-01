'use client';

import React, { useState, useEffect } from 'react';

export function ReportsAndBenchmarks() {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [benchmarking, setBenchmarking] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [peers, setPeers] = useState<any[]>([]);

  // Deep Research State
  const [researchQuery, setResearchQuery] = useState('');
  const [researchResult, setResearchResult] = useState<any>(null);
  const [researching, setResearching] = useState(false);
  const [exportDesktop, setExportDesktop] = useState(true);

  // Unexplored Research Gap Discovery State
  const [gaps, setGaps] = useState<any[]>([]);
  const [discoveringGaps, setDiscoveringGaps] = useState(false);

  useEffect(() => {
    fetchPeers();
  }, []);

  const fetchPeers = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/a2a/peers');
      const data = await res.json();
      if (data.peers) {
        setPeers(data.peers);
      }
    } catch (e) {
      console.warn('Failed to load A2A peers', e);
    }
  };

  const handleRunBenchmarks = async () => {
    try {
      setBenchmarking(true);
      const res = await fetch('http://localhost:8001/api/benchmarks/run');
      const data = await res.json();
      setBenchmarks(data.benchmarks);
    } catch (err: any) {
      alert('Failed to run benchmarks: ' + err.message);
    } finally {
      setBenchmarking(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      setReportResult(null);
      const res = await fetch('http://localhost:8001/api/reports/generate', { method: 'POST' });
      const data = await res.json();
      setReportResult(data);
    } catch (err: any) {
      alert('Failed to generate report: ' + err.message);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleTriggerResearch = async (topicToResearch?: string) => {
    const query = topicToResearch || researchQuery;
    if (!query.trim()) return;
    try {
      setResearching(true);
      setResearchResult(null);
      const res = await fetch('http://localhost:8001/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, max_sources: 5, export_desktop: exportDesktop })
      });
      const data = await res.json();
      setResearchResult(data);
    } catch (err: any) {
      setResearchResult({ success: false, error: err.message });
    } finally {
      setResearching(false);
    }
  };

  const handleDiscoverGaps = async () => {
    try {
      setDiscoveringGaps(true);
      const res = await fetch('http://localhost:8001/api/research/gaps');
      const data = await res.json();
      if (data.recommended_gaps) {
        setGaps(data.recommended_gaps);
      }
    } catch (err: any) {
      alert('Failed to discover research gaps: ' + err.message);
    } finally {
      setDiscoveringGaps(false);
    }
  };

  return (
    <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent)', margin: 0 }}>📊 Benchmarks, Deep Research & Discovery Hub</h2>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
            Autonomous Multi-Source Investigation, Desktop Documentation Publishing & Novel Gap Discovery
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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: '#fff' }}>🔬 Trigger Autonomous Deep Research Mission</h3>
          <label style={{ fontSize: '0.8rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input type="checkbox" checked={exportDesktop} onChange={(e) => setExportDesktop(e.target.checked)} />
            📁 Auto-publish documentation to Mac Desktop
          </label>
        </div>
        <form onSubmit={(e) => { e.preventDefault(); handleTriggerResearch(); }} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={researchQuery}
            onChange={(e) => setResearchQuery(e.target.value)}
            placeholder="Assign topic (e.g. 'Emergent consensus protocols in distributed autonomous swarms')..."
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
            {researching ? '🔬 Researching & Synthesizing...' : '🚀 Start Research'}
          </button>
        </form>

        {researchResult && (
          <div style={{ marginTop: '12px', padding: '14px', borderRadius: '8px', background: researchResult.success ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)', border: `1px solid ${researchResult.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
            <div style={{ fontWeight: 600, color: researchResult.success ? '#10b981' : '#ef4444', fontSize: '0.9rem', marginBottom: '6px' }}>
              {researchResult.success ? `✓ Research Completed: ${researchResult.question}` : '✗ Research Failed:'}
            </div>
            {researchResult.success ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem', color: '#e2e8f0' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <span>Status: <b style={{ color: '#38bdf8' }}>{researchResult.status}</b></span>
                  <span>Sources: <b style={{ color: '#38bdf8' }}>{researchResult.sources_count}</b></span>
                  <span>Claims Verified: <b style={{ color: '#10b981' }}>{researchResult.claims_count}</b></span>
                </div>
                {researchResult.desktop_path && (
                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 12px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    📁 <b>Published Documentation:</b> <span style={{ color: '#6ee7b7', fontFamily: 'monospace' }}>{researchResult.desktop_path}</span>
                  </div>
                )}
                {researchResult.summary && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
                    "{researchResult.summary}"
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: '#fca5a5' }}>{researchResult.error}</div>
            )}
          </div>
        )}
      </div>

      {/* Novelty & Unexplored Research Gap Discovery Hub */}
      <div style={{ background: 'rgba(168, 85, 247, 0.04)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '12px', padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1rem', color: '#c084fc' }}>🔭 Unexplored Research Gap Discovery Engine</h3>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Scans historical research sessions, identifies missing comparative domains, and recommends novel unexplored frontiers.
            </div>
          </div>
          <button className="btn" onClick={handleDiscoverGaps} disabled={discoveringGaps} style={{ padding: '8px 14px', fontSize: '0.85rem', background: 'rgba(168, 85, 247, 0.2)', borderColor: 'rgba(168, 85, 247, 0.4)', color: '#d8b4fe' }}>
            {discoveringGaps ? '🔍 Analyzing Knowledge Gaps...' : '🔭 Discover Unexplored Research'}
          </button>
        </div>

        {gaps.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {gaps.map((gap, idx) => (
              <div key={idx} style={{ background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '8px', padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(168, 85, 247, 0.2)', color: '#e9d5ff', fontWeight: 600 }}>{gap.category || 'Novel Frontier'}</span>
                    <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: gap.impact === 'HIGH' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: gap.impact === 'HIGH' ? '#6ee7b7' : '#fcd34d', fontWeight: 600 }}>{gap.impact} Impact</span>
                    <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>{gap.topic}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {gap.rationale} <span style={{ color: '#a78bfa', fontStyle: 'italic' }}>({gap.unexplored_aspect})</span>
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => { setResearchQuery(gap.topic); handleTriggerResearch(gap.topic); }}
                  disabled={researching}
                  style={{ padding: '8px 12px', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                >
                  🚀 Research This
                </button>
              </div>
            ))}
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
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  Latency: <span style={{ color: '#38bdf8' }}>{b.latency_per_op_us?.toFixed(2)} µs</span> ({b.total_operations} ops in {(b.duration_seconds * 1000).toFixed(1)}ms)
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session Report Card */}
      {reportResult && (
        <div style={{ background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px', padding: '16px' }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '1rem', color: '#10b981' }}>📄 Session Audit Report Generated</h3>
          <div style={{ fontSize: '0.85rem', color: '#e2e8f0', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div><b>Report Path:</b> <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{reportResult.report_path}</span></div>
            <div><b>Evidence Logged:</b> {reportResult.evidence_count} items</div>
            <div><b>Generated At:</b> {reportResult.generated_at}</div>
          </div>
        </div>
      )}

      {/* A2A Agent Cards */}
      <div>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '1.1rem', color: '#fff' }}>🤝 A2A Protocol Registered Agent Cards</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {peers.map((peer) => (
            <div key={peer.agent_id} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: 'var(--accent)', fontSize: '1rem' }}>{peer.name}</span>
                <span style={{ fontSize: '0.75rem', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', fontFamily: 'monospace' }}>
                  {peer.agent_id}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {peer.description}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                {(peer.capabilities || []).map((cap: string, i: number) => (
                  <span key={i} style={{ fontSize: '0.7rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', color: '#cbd5e1' }}>
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
