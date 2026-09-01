'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { SandboxEvent } from '../hooks/useEventStream';
import { DeepAnalytics } from './DeepAnalytics';
import { MarkdownRenderer } from './MarkdownRenderer';

// ─────────────── Types ───────────────────────────────────────
interface ToolStep {
  action: string;
  status: 'running' | 'success' | 'failed';
  result?: any;
  error?: string;
}

interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  thought?: string;
  steps?: ToolStep[];
  timestamp: string;
  model?: string;
  streaming?: boolean;
}

interface SessionHistory {
  session_id: string;
  session_number: number;
  status: string;
  start_time: string;
}

interface StandingJob {
  job_id: string;
  name: string;
  task_prompt: string;
  interval_seconds: number;
  is_active: boolean;
  last_run_at?: string;
  run_count: number;
  last_status: string;
  last_result_summary?: string;
}

interface CommandCenterProps {
  events: SandboxEvent[];
  isConnected: boolean;
  clearEvents: () => void;
}

const STORAGE_KEY = 'ai_sandbox_enterprise_v3';

function relativeTime(iso: string) {
  const d = (Date.now() - new Date(iso).getTime()) / 1000;
  if (d < 60) return `${Math.floor(d)}s ago`;
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  return `${Math.floor(d / 3600)}h ago`;
}

function statusColor(s: string) {
  if (s === 'completed') return 'var(--green-light)';
  if (s === 'running')   return 'var(--blue-400)';
  if (s === 'failed' || s === 'error') return 'var(--red-light)';
  return 'var(--amber-light)';
}

// ─────────────── Nav Item ────────────────────────────────────
function NavItem({ icon, label, active, badge, onClick }: {
  icon: string; label: string; active?: boolean; badge?: number; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`nav-item${active ? ' active' : ''}`}
    >
      <span className="nav-icon">{icon}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="tag tag-red" style={{ padding: '0 5px', minWidth: 18, justifyContent: 'center' }}>
          {badge}
        </span>
      )}
    </button>
  );
}

// ─────────────── Security Modal ──────────────────────────────
function SecurityModal({ permission, onApprove, onDeny, loading }: {
  permission: any; onApprove: () => void; onDeny: () => void; loading: boolean;
}) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9000,
      background: 'rgba(9,9,11,0.8)',
      backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 16,
    }} className="anim-fade-in">
      <div style={{
        width: '100%', maxWidth: 520,
        background: 'var(--bg-surface)',
        border: '1px solid var(--red-border)',
        borderRadius: 'var(--r-xl)',
        padding: 24,
        animation: 'pulse-red-border 2s ease infinite',
        boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 18 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 'var(--r-md)', flexShrink: 0,
            background: 'var(--red-bg)', border: '1px solid var(--red-border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem',
          }}>
            ⚠
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', marginBottom: 2 }}>
              High-Risk Execution Intercepted
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Safe Mode requires approval before this action executes on your system
            </div>
          </div>
          <span className="tag tag-red">{permission.risk || 'HIGH'}</span>
        </div>

        {/* Command */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
            Command
          </div>
          <div style={{
            background: 'var(--bg-input)', border: '1px solid var(--red-border)',
            borderRadius: 'var(--r-md)', padding: '9px 13px',
            fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8125rem',
            color: 'var(--red-light)', wordBreak: 'break-all',
          }}>
            {permission.command || permission.action}
          </div>
        </div>

        {/* Reason */}
        {permission.reason && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              Agent Rationale
            </div>
            <div style={{
              background: 'var(--bg-input)', border: '1px solid var(--border-base)',
              borderRadius: 'var(--r-md)', padding: '9px 13px',
              fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.6,
              maxHeight: 110, overflowY: 'auto',
            }}>
              {permission.reason}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="btn btn-danger" onClick={onDeny} disabled={loading}>
            Deny
          </button>
          <button
            className="btn btn-primary"
            onClick={onApprove}
            disabled={loading}
          >
            {loading ? 'Processing…' : 'Approve & Execute'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────── Message ─────────────────────────────────────
function MessageBubble({ msg }: { msg: Message }) {
  const [thoughtOpen, setThoughtOpen] = useState(false);
  const [stepsOpen, setStepsOpen] = useState(false);
  const isUser = msg.sender === 'user';

  return (
    <div className="anim-slide-up" style={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start', marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, maxWidth: '82%', flexDirection: isUser ? 'row-reverse' : 'row' }}>
        {/* Avatar */}
        <div style={{
          width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
          background: isUser ? 'var(--bg-overlay)' : 'var(--blue-bg)',
          border: `1px solid ${isUser ? 'var(--border-base)' : 'var(--blue-border)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.7rem', fontWeight: 700, color: isUser ? 'var(--text-secondary)' : 'var(--blue-400)',
        }}>
          {isUser ? 'U' : '⚡'}
        </div>

        {/* Bubble */}
        <div style={{
          maxWidth: '100%',
          background: isUser ? 'var(--bg-overlay)' : 'var(--bg-surface)',
          border: isUser ? '1px solid var(--border-base)' : '1px solid var(--border-subtle)',
          borderRadius: isUser ? '12px 3px 12px 12px' : '3px 12px 12px 12px',
          padding: '10px 14px',
        }}>
          {isUser ? (
            <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
              {msg.content}
            </div>
          ) : msg.streaming ? (
            <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
              {msg.content}
              <span style={{ animation: 'pulse-dot 0.8s ease infinite', display: 'inline-block', marginLeft: 2, color: 'var(--blue-400)' }}>▋</span>
            </div>
          ) : (
            <MarkdownRenderer content={msg.content} />
          )}

          {/* Thought */}
          {msg.thought && (
            <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border-faint)' }}>
              <button onClick={() => setThoughtOpen(o => !o)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 5,
                color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 500, padding: 0,
              }}>
                <span style={{ transition: 'transform 0.15s', transform: thoughtOpen ? 'rotate(90deg)' : 'rotate(0)', display: 'inline-block', fontSize: '0.6rem' }}>▶</span>
                Reasoning
              </button>
              {thoughtOpen && (
                <div style={{
                  marginTop: 7, padding: '8px 12px',
                  background: 'var(--bg-input)', borderRadius: 'var(--r-md)',
                  border: '1px solid var(--border-faint)',
                  fontSize: '0.8125rem', color: 'var(--text-muted)',
                  fontStyle: 'italic', lineHeight: 1.65,
                }}>
                  {msg.thought}
                </div>
              )}
            </div>
          )}

          {/* Tool steps */}
          {msg.steps && msg.steps.length > 0 && (
            <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--border-faint)' }}>
              <button onClick={() => setStepsOpen(o => !o)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 5,
                color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 500, padding: 0,
              }}>
                <span style={{ transition: 'transform 0.15s', transform: stepsOpen ? 'rotate(90deg)' : 'rotate(0)', display: 'inline-block', fontSize: '0.6rem' }}>▶</span>
                {msg.steps.length} tool call{msg.steps.length > 1 ? 's' : ''}
              </button>
              {stepsOpen && (
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {msg.steps.map((step, i) => (
                    <div key={i} className="tool-row">
                      <span style={{ color: step.status === 'failed' ? 'var(--red-light)' : step.status === 'running' ? 'var(--blue-400)' : 'var(--green-light)', fontSize: '0.7rem' }}>
                        {step.status === 'failed' ? '✕' : step.status === 'running' ? '◌' : '✓'}
                      </span>
                      <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem', color: 'var(--text-secondary)', flex: 1 }}>
                        {step.action}
                      </span>
                      {step.result && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {typeof step.result === 'string' ? step.result.slice(0, 80) : ''}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Meta */}
      <div style={{
        fontSize: '0.6875rem', color: 'var(--text-faint)', marginTop: 3,
        paddingLeft: isUser ? 0 : 34, paddingRight: isUser ? 34 : 0,
      }}>
        {msg.timestamp}{msg.model ? ` · ${msg.model}` : ''}
      </div>
    </div>
  );
}

// ─────────────── Right Telemetry ─────────────────────────────
function TelemetryPanel({ isConnected, events, pendingCount }: {
  isConnected: boolean; events: SandboxEvent[]; pendingCount: number;
}) {
  const [jobs, setJobs] = useState<StandingJob[]>([]);
  const [sysHealth, setSysHealth] = useState<any>(null);
  const [memInfo, setMemInfo] = useState<any>(null);

  useEffect(() => {
    const fetch_ = async () => {
      try {
        const [h, m, j] = await Promise.allSettled([
          fetch('http://localhost:8001/api/db/health').then(r => r.json()),
          fetch('http://localhost:8001/api/memory').then(r => r.json()),
          fetch('http://localhost:8001/api/scheduler/jobs').then(r => r.json()),
        ]);
        if (h.status === 'fulfilled') setSysHealth(h.value);
        if (m.status === 'fulfilled') setMemInfo(m.value);
        if (j.status === 'fulfilled') setJobs(j.value.jobs || []);
      } catch {}
    };
    fetch_();
    const id = setInterval(fetch_, 15000);
    return () => clearInterval(id);
  }, []);

  const activeJobs = jobs.filter(j => j.is_active);

  return (
    <aside className="right-panel">
      {/* Connection */}
      <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span className={`dot ${isConnected ? 'dot-green' : 'dot-red'}`} />
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: isConnected ? 'var(--text-secondary)' : 'var(--text-muted)' }}>
            {isConnected ? 'Stream active' : 'Disconnected'}
          </span>
          {pendingCount > 0 && (
            <span className="tag tag-red" style={{ marginLeft: 'auto' }}>{pendingCount} pending</span>
          )}
        </div>
      </div>

      {/* Daemon Jobs */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-faint)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Daemon Missions
          </span>
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{activeJobs.length} active</span>
        </div>
        {jobs.slice(0, 5).map(j => (
          <div key={j.job_id} style={{
            display: 'flex', alignItems: 'center', gap: 7, marginBottom: 6, padding: '5px 0',
          }}>
            <span className={`dot ${j.is_active ? 'dot-green' : 'dot-muted'}`} />
            <span style={{ flex: 1, fontSize: '0.8125rem', color: j.is_active ? 'var(--text-secondary)' : 'var(--text-faint)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {j.name}
            </span>
            <span style={{ fontSize: '0.6875rem', color: statusColor(j.last_status), fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
              #{j.run_count}
            </span>
          </div>
        ))}
        {jobs.length === 0 && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-faint)', padding: '2px 0' }}>No missions configured</div>
        )}
      </div>

      {/* Memory */}
      {memInfo && (
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-faint)' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Agent Memory
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Turn', value: memInfo.turn ?? '—', color: 'var(--blue-400)' },
              { label: 'Vectors', value: memInfo.vector_store_entries ?? '—', color: 'var(--violet-light)' },
            ].map(s => (
              <div key={s.label} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-faint)',
                borderRadius: 'var(--r-md)', padding: '8px 10px', textAlign: 'center',
              }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: s.color, letterSpacing: '-0.02em' }}>{s.value}</div>
                <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DB Health */}
      {sysHealth && (
        <div style={{ padding: '10px 14px' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            System
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>Database</span>
            <span className={`tag ${sysHealth.status === 'healthy' ? 'tag-green' : 'tag-amber'}`}>{sysHealth.status}</span>
          </div>
          {sysHealth.file_size_kb && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sysHealth.file_size_kb} KB on disk</div>
          )}
        </div>
      )}
    </aside>
  );
}

// ─────────────── Missions Panel ──────────────────────────────
function MissionsPanel() {
  const [jobs, setJobs] = useState<StandingJob[]>([]);
  const [name, setName] = useState('');
  const [prompt, setPrompt] = useState('');
  const [interval, setInterval_] = useState(900);

  const fetchJobs = async () => {
    try { const r = await fetch('http://localhost:8001/api/scheduler/jobs'); const d = await r.json(); setJobs(d.jobs || []); } catch {}
  };
  useEffect(() => { fetchJobs(); }, []);

  const createJob = async () => {
    if (!prompt.trim()) return;
    await fetch('http://localhost:8001/api/scheduler/jobs', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name || 'Unnamed Mission', task_prompt: prompt, interval_seconds: interval, is_active: true }),
    });
    setName(''); setPrompt(''); fetchJobs();
  };

  const toggleJob = async (id: string) => {
    await fetch(`http://localhost:8001/api/scheduler/jobs/${id}/toggle`, { method: 'POST' });
    fetchJobs();
  };

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }} className="anim-fade-in">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 4 }}>
          Standing Missions
        </h2>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Background tasks that execute automatically on a schedule without human intervention.
        </p>
      </div>

      {/* New job */}
      <div className="card" style={{ padding: 18, marginBottom: 20, borderRadius: 'var(--r-lg)' }}>
        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 14 }}>New mission</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Mission name" />
          <textarea className="textarea" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Task description…" rows={3} />
          <div style={{ display: 'flex', gap: 10 }}>
            <select className="input" style={{ flex: 1 }} value={interval} onChange={e => setInterval_(Number(e.target.value))}>
              <option value={300}>Every 5 min</option>
              <option value={900}>Every 15 min</option>
              <option value={1800}>Every 30 min</option>
              <option value={3600}>Every hour</option>
              <option value={14400}>Every 4 hours</option>
            </select>
            <button className="btn btn-primary" onClick={createJob} style={{ flexShrink: 0 }}>
              Deploy
            </button>
          </div>
        </div>
      </div>

      {/* Jobs list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {jobs.map(j => (
          <div key={j.job_id} className="card" style={{ padding: '14px 16px', borderRadius: 'var(--r-lg)' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                  <span className={`dot ${j.is_active ? 'dot-green' : 'dot-muted'}`} />
                  <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{j.name}</span>
                  <span className={`tag ${j.last_status === 'completed' ? 'tag-green' : j.last_status === 'error' ? 'tag-red' : 'tag-muted'}`} style={{ marginLeft: 'auto' }}>
                    {j.last_status}
                  </span>
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 8, maxWidth: 460 }}>
                  {j.task_prompt.slice(0, 100)}{j.task_prompt.length > 100 ? '…' : ''}
                </div>
                <div style={{ display: 'flex', gap: 14, fontSize: '0.75rem', color: 'var(--text-faint)' }}>
                  <span>{Math.round(j.interval_seconds / 60)}m interval</span>
                  <span>{j.run_count} runs</span>
                  {j.last_run_at && <span>{relativeTime(j.last_run_at)}</span>}
                </div>
              </div>
              <button
                className={`btn ${j.is_active ? 'btn-danger' : 'btn-success'}`}
                onClick={() => toggleJob(j.job_id)}
                style={{ flexShrink: 0 }}
              >
                {j.is_active ? 'Pause' : 'Resume'}
              </button>
            </div>
          </div>
        ))}
        {jobs.length === 0 && (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-faint)', fontSize: '0.875rem' }}>
            No missions deployed yet
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────── Main CommandCenter ──────────────────────────
export function CommandCenter({ events, isConnected, clearEvents }: CommandCenterProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [activeNav, setActiveNav] = useState('chat');
  const [pendingPermission, setPendingPermission] = useState<any>(null);
  const [handlingPermission, setHandlingPermission] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeModel, setActiveModel] = useState('');
  const [showTelemetry, setShowTelemetry] = useState(true);
  const [capturingScreen, setCapturingScreen] = useState(false);
  const [sessions, setSessions] = useState<SessionHistory[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const msgCounter = useRef(0);

  const newId = (prefix: string) => {
    msgCounter.current += 1;
    return `${prefix}-${Date.now()}-${msgCounter.current}`;
  };

  const fetchSessions = async () => {
    try {
      const r = await fetch('http://localhost:8001/api/sessions');
      const d = await r.json();
      setSessions(d.sessions || []);
    } catch {}
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) setMessages(JSON.parse(saved).slice(-60));
    } catch {}
    fetchModelStatus();
    fetchSessions();
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-60))); } catch {}
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  useEffect(() => {
    if (!events.length) return;
    const ev = events[events.length - 1];

    if (ev.type === 'permission.request' && !pendingPermission) {
      const p = ev.payload || ev;
      setPendingPermission({ request_id: p.request_id, command: p.command, action: p.action, reason: p.reason, risk: p.risk });
    }
    if (ev.type === 'agent.chunk') {
      setStreamingContent(prev => prev + (ev.payload?.chunk || ev.chunk || ''));
      setIsStreaming(true);
    }
    if (ev.type === 'agent.message' || ev.type === 'human.message.processed') {
      const content = ev.payload?.content || ev.content || '';
      if (content && content !== streamingContent) {
        setIsStreaming(false); setStreamingContent('');
        addAgentMessage(content, ev.thought, undefined, ev.model);
      } else if (streamingContent) {
        setIsStreaming(false);
        addAgentMessage(streamingContent, undefined, undefined, ev.model);
        setStreamingContent('');
      }
    }
  }, [events]);

  useEffect(() => {
    const poll = async () => {
      try { const r = await fetch('http://localhost:8001/api/permissions'); const d = await r.json(); setPendingCount((d.permissions || []).length); } catch {}
    };
    poll();
    const id = setInterval(poll, 4000);
    return () => clearInterval(id);
  }, []);

  const fetchModelStatus = async () => {
    try {
      const r = await fetch('http://localhost:8001/api/models/status');
      const d = await r.json();
      const name = d.routes?.default?.name || d.routes?.default?.backend;
      if (name) setActiveModel(name);
    } catch {}
  };

  const addAgentMessage = (content: string, thought?: string, steps?: ToolStep[], model?: string) => {
    setMessages(prev => [...prev, {
      id: newId('a'), sender: 'agent', content, thought, steps, model,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  };

  const clearHistory = () => {
    setMessages([]);
    setStreamingContent('');
    setIsStreaming(false);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  };

  const createNewChat = async () => {
    try {
      const r = await fetch('http://localhost:8001/api/sessions', { method: 'POST' });
      const d = await r.json();
      if (d.success) {
        setMessages([]);
        setCurrentSessionId(d.session_id);
        setActiveNav('chat');
        fetchSessions();
      }
    } catch {}
  };

  const switchSession = async (id: string) => {
    setMessages([]);
    setIsStreaming(false);
    setStreamingContent('');
    try {
      await fetch(`http://localhost:8001/api/sessions/${id}/switch`, { method: 'POST' });
      setCurrentSessionId(id);
      const r = await fetch(`http://localhost:8001/api/sessions/${id}/messages`);
      const d = await r.json();
      if (d.messages) setMessages(d.messages);
      setActiveNav('chat');
    } catch {}
  };

  const deleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`http://localhost:8001/api/sessions/${id}`, { method: 'DELETE' });
      fetchSessions();
      if (currentSessionId === id) {
        setMessages([]);
        setCurrentSessionId(null);
      }
    } catch {}
  };

  const handleSend = async (override?: string) => {
    const text = override || inputValue.trim();
    if (!text || sending) return;
    setInputValue('');
    setSending(true);

    setMessages(prev => [...prev, {
      id: newId('u'), sender: 'user', content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);

    try {
      const r = await fetch('http://localhost:8001/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode: '24/7' }),
      });
      const d = await r.json();
      if (d.final_response && !isStreaming) addAgentMessage(d.final_response, d.thought, d.steps, activeModel);
    } catch (e: any) {
      addAgentMessage(`**Error:** ${e.message}`);
    } finally { setSending(false); }
  };

  const handlePermissionDecision = async (approved: boolean) => {
    if (!pendingPermission || handlingPermission) return;
    setHandlingPermission(true);
    try {
      await fetch(`http://localhost:8001/api/permissions/${pendingPermission.request_id}/${approved ? 'approve' : 'deny'}`, { method: 'POST' });
      setPendingPermission(null);
    } catch { alert('Failed to send decision.'); }
    finally { setHandlingPermission(false); }
  };

  const handleScreenCapture = async () => {
    setCapturingScreen(true);
    try {
      const r = await fetch('http://localhost:8001/api/vision/screen', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Describe what you see on the screen in detail.' }),
      });
      const d = await r.json();
      if (d.analysis) addAgentMessage(`**Screen Analysis**\n\n${d.analysis}`);
    } catch (e: any) { addAgentMessage(`**Error:** ${e.message}`); }
    finally { setCapturingScreen(false); }
  };

  const quickPrompts = [
    'Check system health and RAM usage',
    'List all files on the Desktop',
    'Research the latest in AI agents',
    'Inspect my screen and describe it',
  ];

  const navSections = [
    {
      label: 'Workspace',
      items: [
        { id: 'chat',      icon: '⌘', label: 'Command Chat' },
        { id: 'missions',  icon: '◎', label: 'Missions', badge: undefined as number | undefined },
      ],
    },
    {
      label: 'Intelligence',
      items: [
        { id: 'analytics', icon: '◈', label: 'Analytics' },
        { id: 'screen',    icon: '▣', label: 'Screen Vision' },
      ],
    },
    {
      label: 'Security',
      items: [
        { id: 'security',  icon: '◐', label: 'Audit Log', badge: pendingCount > 0 ? pendingCount : undefined },
      ],
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

      {/* ── Topbar ── */}
      <header className="topbar">
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 22, height: 22, borderRadius: 6, flexShrink: 0,
            background: 'var(--blue-600)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.7rem', color: '#fff', fontWeight: 700,
          }}>⚡</div>
          <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            AI Sandbox
          </span>
        </div>

        <div style={{ width: 1, height: 16, background: 'var(--border-subtle)', margin: '0 4px' }} />

        {/* Model pill */}
        {activeModel && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="dot dot-green" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
              {activeModel}
            </span>
          </div>
        )}

        {/* Intercept alert */}
        {pendingCount > 0 && (
          <button
            onClick={() => setActiveNav('security')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'var(--red-bg)', border: '1px solid var(--red-border)',
              borderRadius: 'var(--r-md)', padding: '3px 10px',
              animation: 'pulse-red-border 2s ease infinite',
              cursor: 'pointer', color: 'var(--red-light)',
              fontSize: '0.75rem', fontWeight: 600, fontFamily: 'inherit',
            }}
          >
            ⚠ {pendingCount} intercept{pendingCount > 1 ? 's' : ''} pending
          </button>
        )}

        <div style={{ flex: 1 }} />

        {/* Connection status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className={`dot ${isConnected ? 'dot-green' : 'dot-red'}`} />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)' }}>
            {isConnected ? 'Live' : 'Offline'}
          </span>
        </div>

        <div style={{ width: 1, height: 16, background: 'var(--border-subtle)', margin: '0 4px' }} />

        {/* Toggle panel */}
        <button className="btn" onClick={() => setShowTelemetry(t => !t)} style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
          {showTelemetry ? 'Hide panel' : 'Telemetry'}
        </button>
      </header>

      {/* ── Body ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── Sidebar ── */}
        <nav className="sidebar">
          {navSections.map(sec => (
            <div key={sec.label}>
              <div className="section-label">{sec.label}</div>
              {sec.items.map(item => (
                <NavItem
                  key={item.id}
                  icon={item.icon}
                  label={item.label}
                  active={activeNav === item.id}
                  badge={item.badge}
                  onClick={() => setActiveNav(item.id)}
                />
              ))}
            </div>
          ))}

          {/* History */}
          <div style={{ marginTop: 14 }}>
            <div className="section-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>History</span>
              <button onClick={createNewChat} style={{
                background: 'none', border: 'none', color: 'var(--blue-400)',
                cursor: 'pointer', fontSize: '0.9rem', padding: '0 4px',
              }} title="New Chat">+</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '0 4px' }}>
              {sessions.slice(0, 15).map(s => (
                <div
                  key={s.session_id}
                  onClick={() => switchSession(s.session_id)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '6px 8px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                    background: currentSessionId === s.session_id ? 'rgba(255,255,255,0.06)' : 'transparent',
                    color: currentSessionId === s.session_id ? 'var(--text-primary)' : 'var(--text-muted)',
                    fontSize: '0.8125rem', transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => { if (currentSessionId !== s.session_id) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
                  onMouseLeave={e => { if (currentSessionId !== s.session_id) e.currentTarget.style.background = 'transparent'; }}
                >
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    Session #{s.session_number}
                  </span>
                  <button
                    onClick={(e) => deleteChat(s.session_id, e)}
                    style={{
                      background: 'none', border: 'none', color: 'var(--text-faint)',
                      cursor: 'pointer', padding: '0 4px', fontSize: '0.8rem',
                    }}
                    title="Delete Chat"
                    onMouseEnter={e => e.currentTarget.style.color = 'var(--red-light)'}
                    onMouseLeave={e => e.currentTarget.style.color = 'var(--text-faint)'}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div style={{ flex: 1 }} />

          {/* Status block */}
          <div style={{
            margin: '8px 4px 0', padding: '10px 10px',
            background: 'var(--bg-surface)', border: '1px solid var(--border-faint)',
            borderRadius: 'var(--r-md)',
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 5, fontWeight: 500 }}>Operator Mode</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="dot dot-green" />
              <span style={{ fontSize: '0.75rem', color: 'var(--green-light)', fontWeight: 500 }}>24/7 Active</span>
            </div>
          </div>
        </nav>

        {/* ── Main ── */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0, background: 'var(--bg-base)' }}>

          {/* CHAT */}
          {activeNav === 'chat' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

              {/* Chat toolbar: only shows when there are messages */}
              {messages.length > 0 && (
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '8px 24px', borderBottom: '1px solid var(--border-faint)',
                  background: 'var(--bg-base)', flexShrink: 0,
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)' }}>
                    {messages.length} message{messages.length !== 1 ? 's' : ''}
                  </span>
                  <button
                    className="btn"
                    onClick={clearHistory}
                    style={{ fontSize: '0.75rem', padding: '3px 10px', color: 'var(--text-muted)' }}
                  >
                    Clear history
                  </button>
                </div>
              )}

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column' }}>
                {messages.length === 0 && (
                  <div className="anim-fade-in" style={{
                    flex: 1, display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center', gap: 20, paddingBottom: 60,
                    minHeight: 300,
                  }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: 12,
                      background: 'var(--bg-surface)', border: '1px solid var(--border-base)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1.2rem', color: 'var(--blue-400)',
                    }}>⚡</div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 6, letterSpacing: '-0.02em' }}>
                        Command Center
                      </div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: 380, lineHeight: 1.7 }}>
                        Assign any task. Your AI agent can control your Mac, browse the web, write code, and run 24/7 background missions.
                      </div>
                    </div>
                    {/* Quick prompt chips */}
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 500 }}>
                      {quickPrompts.map(q => (
                        <button
                          key={q}
                          className="btn"
                          onClick={() => handleSend(q)}
                          style={{
                            fontSize: '0.8125rem',
                            color: 'var(--text-secondary)',
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--border-base)',
                            padding: '7px 14px',
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.background = 'var(--bg-overlay)';
                            e.currentTarget.style.borderColor = 'var(--border-strong)';
                            e.currentTarget.style.color = 'var(--text-primary)';
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.background = 'var(--bg-surface)';
                            e.currentTarget.style.borderColor = 'var(--border-base)';
                            e.currentTarget.style.color = 'var(--text-secondary)';
                          }}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {messages.map(m => <MessageBubble key={m.id} msg={m} />)}

                {isStreaming && streamingContent && (
                  <MessageBubble msg={{ id: 'streaming', sender: 'agent', content: streamingContent, timestamp: '…', streaming: true }} />
                )}

                {sending && !isStreaming && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <div style={{
                      width: 26, height: 26, borderRadius: '50%',
                      background: 'var(--blue-bg)', border: '1px solid var(--blue-border)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.7rem', color: 'var(--blue-400)',
                    }}>⚡</div>
                    <div style={{
                      padding: '8px 12px', borderRadius: '3px 10px 10px 10px',
                      background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                      display: 'flex', gap: 4, alignItems: 'center',
                    }}>
                      {[0, 0.18, 0.36].map((d, i) => (
                        <span key={i} style={{
                          width: 5, height: 5, borderRadius: '50%', background: 'var(--text-faint)',
                          display: 'inline-block', animation: `pulse-dot 1.1s ease ${d}s infinite`,
                        }} />
                      ))}
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div style={{
                padding: '10px 18px 14px',
                background: 'var(--bg-root)',
                borderTop: '1px solid var(--border-subtle)',
              }}>
                <div style={{
                  display: 'flex', gap: 8, alignItems: 'flex-end',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-base)',
                  borderRadius: 'var(--r-lg)',
                  padding: '8px 10px',
                  transition: 'border-color 0.12s',
                }}>
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={e => {
                      setInputValue(e.target.value);
                      e.target.style.height = 'auto';
                      e.target.style.height = Math.min(e.target.scrollHeight, 130) + 'px';
                    }}
                    onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                    placeholder="Assign any task to your agent… (Enter to send)"
                    rows={1}
                    style={{
                      flex: 1, background: 'none', border: 'none', outline: 'none',
                      color: 'var(--text-primary)', fontSize: '0.875rem',
                      lineHeight: 1.6, resize: 'none', fontFamily: 'inherit',
                      maxHeight: 130, letterSpacing: '-0.005em',
                    }}
                  />
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                    <button
                      className="btn"
                      onClick={handleScreenCapture}
                      disabled={capturingScreen}
                      title="Capture screen"
                      style={{ padding: '5px 9px', fontSize: '0.8rem' }}
                    >
                      {capturingScreen ? '◌' : '▣'}
                    </button>
                    <button
                      onClick={() => handleSend()}
                      disabled={sending || !inputValue.trim()}
                      className={`btn ${!sending && inputValue.trim() ? 'btn-primary' : ''}`}
                      style={{ width: 32, height: 32, padding: 0, justifyContent: 'center', borderRadius: 'var(--r-md)' }}
                    >
                      ↑
                    </button>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5, paddingInline: 2 }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-faint)' }}>
                    Enter to send · Shift+Enter for newline
                  </span>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-faint)' }}>⚡ 24/7 Operator Active</span>
                </div>
              </div>
            </div>
          )}

          {activeNav === 'missions' && <MissionsPanel />}

          {activeNav === 'analytics' && <DeepAnalytics />}

          {activeNav === 'screen' && (
            <div className="anim-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18, padding: 40 }}>
              <div style={{
                width: 52, height: 52, borderRadius: 14,
                background: 'var(--bg-surface)', border: '1px solid var(--border-base)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem',
              }}>▣</div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 5 }}>Screen Vision</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: 340, lineHeight: 1.7 }}>
                  Capture and analyze your current screen. The agent will describe what it sees and can take action based on the context.
                </div>
              </div>
              <button className="btn btn-primary" onClick={handleScreenCapture} disabled={capturingScreen} style={{ padding: '7px 18px' }}>
                {capturingScreen ? '◌ Capturing…' : 'Capture & Analyze'}
              </button>
            </div>
          )}

          {activeNav === 'security' && (
            <div className="anim-fade-in" style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
              <div style={{ marginBottom: 20 }}>
                <h2 style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                  Audit Log
                </h2>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  Safe Mode intercepts high-risk commands for approval before they execute on your system.
                </p>
              </div>
              {pendingCount === 0 ? (
                <div className="card" style={{ padding: '28px 20px', textAlign: 'center', borderRadius: 'var(--r-lg)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--green-light)', marginBottom: 4, fontSize: '0.875rem' }}>
                    No pending intercepts
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                    All agent actions are cleared. Safe Mode is active.
                  </div>
                </div>
              ) : (
                <div className="card" style={{
                  padding: '14px 16px', borderColor: 'var(--red-border)',
                  background: 'var(--red-bg)', borderRadius: 'var(--r-lg)',
                }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--red-light)', fontWeight: 600 }}>
                    {pendingCount} action{pendingCount > 1 ? 's' : ''} awaiting approval
                  </span>
                </div>
              )}
            </div>
          )}
        </main>

        {/* ── Right Telemetry ── */}
        {showTelemetry && (
          <TelemetryPanel isConnected={isConnected} events={events} pendingCount={pendingCount} />
        )}
      </div>

      {/* ── Security Modal ── */}
      {pendingPermission && (
        <SecurityModal
          permission={pendingPermission}
          onApprove={() => handlePermissionDecision(true)}
          onDeny={() => handlePermissionDecision(false)}
          loading={handlingPermission}
        />
      )}
    </div>
  );
}
