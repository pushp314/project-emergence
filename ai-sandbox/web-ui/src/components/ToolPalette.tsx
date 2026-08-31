'use client';

import React, { useEffect, useState } from 'react';

interface ToolItem {
  name: string;
  description: string;
  input_schema: any;
  permission: string;
  risk: string;
  enabled: boolean;
}

const DEFAULT_TOOL_ARGS: Record<string, any> = {
  terminal: { command: 'ls -la' },
  filesystem: { operation: 'list', path: '.' },
  web: { url: 'https://example.com' },
  browser: { action: 'goto', url: 'https://news.ycombinator.com' },
  system: { action: 'get_metrics' },
  testing: { test_type: 'unit', path: './tests' },
  knowledge_search: { query: 'agent capabilities' },
  screenshot: { delay_seconds: 0 },
  create_tool: { name: 'echo_tool', code: 'async def execute(args): return args' },
  delegate_task: { target_agent: 'agent_b', task: 'Research optimization methods' },
  submit_task_result: { task_id: 'sample_task', result: 'Completed' },
};

export function ToolPalette() {
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState<ToolItem | null>(null);
  const [toolArgs, setToolArgs] = useState<string>('{}');
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchTools = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8001/api/tools');
      const data = await res.json();
      setTools(data.tools || []);
    } catch (err) {
      console.error('Failed to load tools', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const openExecuteModal = (tool: ToolItem) => {
    setSelectedTool(tool);
    const defaultArgs = DEFAULT_TOOL_ARGS[tool.name] || {};
    setToolArgs(JSON.stringify(defaultArgs, null, 2));
    setExecResult(null);
  };

  const handleExecute = async () => {
    if (!selectedTool) return;
    try {
      setExecuting(true);
      setExecResult(null);
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(toolArgs);
      } catch (err) {
        setExecResult({ success: false, error: 'Invalid JSON arguments format' });
        setExecuting(false);
        return;
      }

      const res = await fetch('http://localhost:8001/api/tools/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: selectedTool.name,
          arguments: parsedArgs,
          agent_id: 'dashboard_operator'
        })
      });
      const data = await res.json();
      setExecResult(data);
    } catch (err: any) {
      setExecResult({ success: false, error: err.message || 'Execution failed' });
    } finally {
      setExecuting(false);
    }
  };

  const filteredTools = tools.filter(t => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    t.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case 'low': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'high': return '#ef4444';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  return (
    <div className="glass-panel" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'hidden' }}>
      {/* Header & Search */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent)', margin: 0 }}>Tool Palette & Capabilities</h2>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
            {tools.length} Registered Autonomous Agent Tools & Direct Execution Gateways
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'rgba(0,0,0,0.3)',
              color: 'white',
              fontSize: '0.85rem'
            }}
          />
          <button className="btn" onClick={fetchTools} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>Loading tools...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px', overflowY: 'auto', paddingRight: '4px' }}>
          {filteredTools.map((t) => {
            const riskColor = getRiskColor(t.risk);
            return (
              <div 
                key={t.name}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '10px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontWeight: 600, fontSize: '1rem', color: '#fff', fontFamily: 'monospace' }}>
                    {t.name}
                  </span>
                  <span style={{
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: `${riskColor}20`,
                    color: riskColor,
                    fontWeight: 600,
                    textTransform: 'uppercase'
                  }}>
                    {t.risk}
                  </span>
                </div>

                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0, lineHeight: 1.4, flex: 1 }}>
                  {t.description}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    Scope: <code style={{ color: '#38bdf8' }}>{t.permission}</code>
                  </span>
                  <button 
                    className="btn btn-primary"
                    style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    onClick={() => openExecuteModal(t)}
                  >
                    ▶ Test Tool
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Manual Execution Modal */}
      {selectedTool && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ width: '600px', maxWidth: '100%', maxHeight: '90vh', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, color: '#fff', fontSize: '1.2rem' }}>
                Execute Tool: <code style={{ color: 'var(--accent)' }}>{selectedTool.name}</code>
              </h3>
              <button 
                onClick={() => setSelectedTool(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
              {selectedTool.description}
            </p>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>
                JSON Arguments:
              </label>
              <textarea
                value={toolArgs}
                onChange={(e) => setToolArgs(e.target.value)}
                rows={5}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '8px',
                  background: 'rgba(0,0,0,0.5)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#fff',
                  fontFamily: 'monospace',
                  fontSize: '0.85rem'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                className="btn btn-primary" 
                onClick={handleExecute}
                disabled={executing}
                style={{ flex: 1, padding: '8px' }}
              >
                {executing ? 'Executing...' : '⚡ Run Now'}
              </button>
              <button 
                className="btn" 
                onClick={() => setSelectedTool(null)}
                style={{ padding: '8px 16px' }}
              >
                Cancel
              </button>
            </div>

            {/* Execution Result Display */}
            {execResult && (
              <div style={{
                marginTop: '12px',
                padding: '12px',
                borderRadius: '8px',
                background: execResult.success ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                border: `1px solid ${execResult.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
              }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: execResult.success ? '#10b981' : '#ef4444', marginBottom: '6px' }}>
                  {execResult.success ? '✓ Output Received:' : '✗ Execution Failed:'}
                </div>
                <pre style={{
                  margin: 0,
                  fontSize: '0.8rem',
                  color: '#e2e8f0',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {execResult.success 
                    ? (typeof execResult.result === 'object' ? JSON.stringify(execResult.result, null, 2) : String(execResult.result))
                    : execResult.error
                  }
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
