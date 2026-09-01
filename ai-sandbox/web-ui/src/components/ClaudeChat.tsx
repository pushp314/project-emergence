'use client';

import React, { useState, useEffect, useRef } from 'react';
import { SandboxEvent } from '../hooks/useEventStream';

interface ToolStep {
  step?: number;
  thought?: string;
  action: string;
  action_input?: any;
  status: 'running' | 'success' | 'failed';
  result?: any;
  error?: string;
}

interface Message {
  id: string;
  sender: 'user' | 'agent' | 'system';
  agentName?: string;
  content: string;
  thought?: string;
  steps?: ToolStep[];
  desktopPath?: string;
  screenshotPath?: string;
  imageBase64?: string;
  timestamp: string;
  model?: string;
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

interface ClaudeChatProps {
  events: SandboxEvent[];
  isConnected: boolean;
  clearEvents: () => void;
}

const STORAGE_KEY = 'ai_sandbox_claude_chat_history_v1';

export function ClaudeChat({ events, isConnected, clearEvents }: ClaudeChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const [capturingScreen, setCapturingScreen] = useState(false);
  const [is247Mode, setIs247Mode] = useState(true);
  const [activeModel, setActiveModel] = useState('Gemini 3.1 Flash Lite');
  
  // Voice Input State
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  // High-Risk Tool Approval State
  const [pendingPermission, setPendingPermission] = useState<any>(null);
  const [handlingPermission, setHandlingPermission] = useState(false);

  // UI Accordion States
  const [expandedThoughts, setExpandedThoughts] = useState<{ [key: string]: boolean }>({});
  const [expandedTools, setExpandedTools] = useState<{ [key: string]: boolean }>({});
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Brain Inspector (Memory Viewer) State
  const [showMemoryModal, setShowMemoryModal] = useState(false);
  const [memoryData, setMemoryData] = useState<any>(null);
  const [loadingMemory, setLoadingMemory] = useState(false);

  // Settings State
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Gaps Modal
  const [showGapsModal, setShowGapsModal] = useState(false);
  const [gaps, setGaps] = useState<any[]>([]);
  const [loadingGaps, setLoadingGaps] = useState(false);

  // 24/7 Standing Jobs Modal
  const [showJobsModal, setShowJobsModal] = useState(false);
  const [jobs, setJobs] = useState<StandingJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [newJobName, setNewJobName] = useState('');
  const [newJobPrompt, setNewJobPrompt] = useState('');
  const [newJobInterval, setNewJobInterval] = useState(900);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 1. Restore Chat History from LocalStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
        }
      }
    } catch (e) {
      console.warn('Failed to load chat history', e);
    }
    fetchModelStatus();
    fetchScheduledJobs();

    // Initialize Web Speech API if supported
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          let transcript = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
          }
          if (transcript) {
            setInputValue(prev => (prev ? prev + ' ' + transcript : transcript));
          }
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognition.onerror = (e: any) => {
          console.warn('Speech recognition error:', e);
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      }
    }
  }, []);

  // 2. Persist Chat History to LocalStorage on change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-50)));
      } catch (e) {
        console.warn('Failed to save chat history', e);
      }
    }
  }, [messages]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, events, sending]);

  // 3. Listen for Permission Requests (Safe Mode Interception)
  useEffect(() => {
    if (events.length > 0) {
      const latest = events[events.length - 1];
      if (latest.type === 'permission.request' && !pendingPermission) {
        setPendingPermission(latest.payload);
      } else if ((latest.type === 'permission.approved' || latest.type === 'permission.denied') && pendingPermission) {
        if (latest.payload?.request_id === pendingPermission.request_id) {
          setPendingPermission(null);
        }
      }
    }
  }, [events, pendingPermission]);

  const handlePermissionDecision = async (approved: boolean) => {
    if (!pendingPermission || handlingPermission) return;
    setHandlingPermission(true);
    try {
      const endpoint = approved ? 'approve' : 'deny';
      await fetch(`http://localhost:8001/api/permissions/${pendingPermission.request_id}/${endpoint}`, {
        method: 'POST',
      });
      setPendingPermission(null);
    } catch (e) {
      alert('Failed to send permission decision');
    } finally {
      setHandlingPermission(false);
    }
  };

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        console.warn('Could not start recognition:', e);
        setIsListening(false);
      }
    }
  };

  const fetchModelStatus = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/models/status');
      const data = await res.json();
      if (data.routes?.default?.name) {
        setActiveModel(data.routes.default.name);
      }
    } catch (e) {
      console.warn('Failed to fetch model status', e);
    }
  };

  const fetchScheduledJobs = async () => {
    try {
      setLoadingJobs(true);
      const res = await fetch('http://localhost:8001/api/scheduler/jobs');
      const data = await res.json();
      if (data.jobs) {
        setJobs(data.jobs);
      }
    } catch (e) {
      console.warn('Failed to load jobs', e);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputValue;
    if (!text.trim() || sending) return;

    const userMsgId = 'user-' + Date.now();
    const userMsg: Message = {
      id: userMsgId,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setSending(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const res = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode: is247Mode ? '24/7' : 'step' })
      });
      const data = await res.json();

      if (data.success) {
        const agentMsg: Message = {
          id: 'agent-' + Date.now(),
          sender: 'agent',
          agentName: 'Atlas (Mac Autonomous Operator)',
          content: data.final_response || 'Task executed successfully on your Mac.',
          thought: data.thought,
          steps: data.steps || [],
          desktopPath: data.desktop_path,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: activeModel
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        setMessages(prev => [...prev, {
          id: 'agent-err-' + Date.now(),
          sender: 'agent',
          agentName: 'Atlas (System)',
          content: `⚠️ Execution failed: ${data.error || 'Unknown error'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      }
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: 'agent-err-' + Date.now(),
        sender: 'agent',
        agentName: 'System',
        content: `Error connecting to backend: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleCaptureScreen = async () => {
    if (capturingScreen) return;
    try {
      setCapturingScreen(true);
      const userMsg: Message = {
        id: 'user-snap-' + Date.now(),
        sender: 'user',
        content: '📷 Inspect and analyze what is currently open on my Mac screen.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, userMsg]);

      const res = await fetch('http://localhost:8001/api/vision/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Examine this screenshot of my Mac. Identify all open windows, code, UI elements, or errors, and summarize the state.' })
      });
      const data = await res.json();

      if (data.success) {
        const agentMsg: Message = {
          id: 'agent-snap-' + Date.now(),
          sender: 'agent',
          agentName: 'Atlas (Mac Vision Assistant)',
          content: data.analysis || 'Visual screen analysis completed.',
          screenshotPath: data.screenshot_path,
          imageBase64: data.image_base64,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: activeModel
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        alert('Screen capture error: ' + (data.error || 'Failed'));
      }
    } catch (e: any) {
      alert('Screen capture failed: ' + e.message);
    } finally {
      setCapturingScreen(false);
    }
  };

  const handleRevealInFinder = async (filePath: string) => {
    try {
      await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `Open folder in Finder: ${filePath}`, mode: '24/7' })
      });
    } catch (e) {
      console.warn('Failed to reveal in Finder', e);
    }
  };

  const handleExportSession = async () => {
    if (messages.length === 0) {
      alert('No messages in session to export.');
      return;
    }
    const transcriptText = messages.map(m => `### ${m.sender === 'user' ? '👤 User' : '🧠 ' + (m.agentName || 'Agent')} (${m.timestamp})\n${m.content}\n`).join('\n---\n\n');
    const prompt = `Create a markdown document on my Desktop named Session_Export_${Date.now()}.md with the following conversation content:\n\n${transcriptText.slice(0, 3000)}`;
    handleSendMessage(prompt);
  };

  const handleDiscoverGaps = async () => {
    try {
      setLoadingGaps(true);
      setShowGapsModal(true);
      const res = await fetch('http://localhost:8001/api/research/gaps');
      const data = await res.json();
      if (data.recommended_gaps) {
        setGaps(data.recommended_gaps);
      }
    } catch (err: any) {
      alert('Failed to discover gaps: ' + err.message);
    } finally {
      setLoadingGaps(false);
    }
  };

  const handleToggleJob = async (jobId: string) => {
    try {
      const res = await fetch(`http://localhost:8001/api/scheduler/jobs/${jobId}/toggle`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        fetchScheduledJobs();
      }
    } catch (e) {
      alert('Failed to toggle job');
    }
  };

  const fetchMemoryContext = async () => {
    try {
      setLoadingMemory(true);
      const res = await fetch('http://localhost:8001/api/memory');
      const data = await res.json();
      setMemoryData(data);
    } catch (e) {
      alert('Failed to load memory context');
    } finally {
      setLoadingMemory(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await fetch(`http://localhost:8001/api/scheduler/jobs/${jobId}`, { method: 'DELETE' });
      fetchScheduledJobs();
    } catch (e) {
      alert('Failed to delete job');
    }
  };

  const handleAddJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJobPrompt.trim()) return;
    try {
      await fetch('http://localhost:8001/api/scheduler/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newJobName || 'Standing Task',
          task_prompt: newJobPrompt,
          interval_seconds: Number(newJobInterval),
          is_active: true
        })
      });
      setNewJobName('');
      setNewJobPrompt('');
      fetchScheduledJobs();
    } catch (e: any) {
      alert('Failed to create job: ' + e.message);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Clear all conversation history and start fresh?')) {
      localStorage.removeItem(STORAGE_KEY);
      setMessages([]);
      clearEvents();
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleThought = (msgId: string) => {
    setExpandedThoughts(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const toggleToolDetail = (toolKey: string) => {
    setExpandedTools(prev => ({ ...prev, [toolKey]: !prev[toolKey] }));
  };

  const renderToolResultContent = (tool: ToolStep, toolKey: string) => {
    const res = tool.result;
    if (!res) return null;

    let outputText = '';
    if (tool.action === 'terminal') {
      outputText = res.stdout || res.output || res.stderr || (typeof res === 'string' ? res : JSON.stringify(res, null, 2));
    } else if (tool.action === 'filesystem') {
      outputText = res.content || res.files || res.message || JSON.stringify(res, null, 2);
    } else if (tool.action === 'spotlight') {
      outputText = res.results ? res.results.join('\n') : JSON.stringify(res, null, 2);
    } else {
      outputText = typeof res === 'string' ? res : JSON.stringify(res, null, 2);
    }

    return (
      <div style={{ position: 'relative' }}>
        <pre style={{
          margin: 0,
          padding: '10px 14px',
          background: '#050811',
          borderRadius: '6px',
          fontSize: '0.78rem',
          color: tool.action === 'terminal' ? '#38bdf8' : tool.action === 'spotlight' ? '#fcd34d' : '#6ee7b7',
          overflowX: 'auto',
          fontFamily: 'monospace',
          lineHeight: 1.4
        }}>
          {typeof outputText === 'string' ? outputText.trim() : JSON.stringify(outputText, null, 2)}
        </pre>
        <button
          onClick={() => copyToClipboard(typeof outputText === 'string' ? outputText : JSON.stringify(outputText), toolKey)}
          style={{
            position: 'absolute',
            top: '6px',
            right: '6px',
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            borderRadius: '4px',
            color: '#cbd5e1',
            fontSize: '0.7rem',
            padding: '3px 8px',
            cursor: 'pointer'
          }}
        >
          {copiedKey === toolKey ? '✓ Copied' : '📋 Copy'}
        </button>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', background: '#0b0f19', color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* ── LEFT SIDEBAR ── */}
      <aside style={{
        width: '280px',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        background: '#070a12',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        gap: '12px',
        flexShrink: 0
      }}>
        {/* Brand & Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>🧠</span> Mac Controller
          </div>
          <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: isConnected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: isConnected ? '#34d399' : '#f87171' }}>
            {isConnected ? '● Online' : '○ Offline'}
          </span>
        </div>

        <button
          onClick={handleClearHistory}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.06)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            color: '#f8fafc',
            fontWeight: 600,
            fontSize: '0.88rem',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)')}
        >
          <span>+</span> New Mission (Reset)
        </button>

        {/* 24/7 Continuous Mode Toggle Card */}
        <div style={{
          padding: '12px',
          borderRadius: '10px',
          background: is247Mode ? 'rgba(168, 85, 247, 0.08)' : 'rgba(255, 255, 255, 0.03)',
          border: `1px solid ${is247Mode ? 'rgba(168, 85, 247, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: is247Mode ? '#c084fc' : '#94a3b8' }}>
              ⚡ 24/7 Autonomy Mode
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
              {is247Mode ? 'Continuous multi-step loop' : 'Step confirmation'}
            </div>
          </div>
          <input
            type="checkbox"
            checked={is247Mode}
            onChange={(e) => setIs247Mode(e.target.checked)}
            style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: '#a855f7' }}
          />
        </div>

        {/* Standing 24/7 Missions Button */}
        <button
          onClick={() => { setShowJobsModal(true); fetchScheduledJobs(); }}
          style={{
            padding: '10px 12px',
            borderRadius: '8px',
            background: 'rgba(168, 85, 247, 0.1)',
            border: '1px solid rgba(168, 85, 247, 0.25)',
            color: '#c084fc',
            fontSize: '0.83rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            justifyContent: 'center'
          }}
        >
          <span>⏰</span> Standing 24/7 Missions ({jobs.filter(j => j.is_active).length} Active)
        </button>

        {/* Discover Unexplored Gaps Button */}
        <button
          onClick={handleDiscoverGaps}
          style={{
            padding: '10px 12px',
            borderRadius: '8px',
            background: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            color: '#38bdf8',
            fontSize: '0.83rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            justifyContent: 'center'
          }}
        >
          <span>🔭</span> Discover Unexplored Gaps
        </button>

        {/* Export Chat as Markdown Button */}
        <button
          onClick={handleExportSession}
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            color: '#94a3b8',
            fontSize: '0.8rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            justifyContent: 'center'
          }}
        >
          <span>📥</span> Export Session to Desktop
        </button>

        {/* Brain Inspector Button */}
        <button
          onClick={() => { setShowMemoryModal(true); fetchMemoryContext(); }}
          style={{
            padding: '10px 12px',
            borderRadius: '8px',
            background: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.25)',
            color: '#facc15',
            fontSize: '0.83rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            justifyContent: 'center'
          }}
        >
          <span>🧠</span> Brain Inspector
        </button>

        {/* Settings Button */}
        <button
          onClick={() => setShowSettingsModal(true)}
          style={{
            padding: '8px 12px',
            borderRadius: '8px',
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            color: '#94a3b8',
            fontSize: '0.8rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            justifyContent: 'center'
          }}
        >
          <span>⚙️</span> System Settings
        </button>

        {/* Active Model Indicator */}
        <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)', fontSize: '0.8rem' }}>
          <div style={{ color: '#64748b', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active LLM Provider</div>
          <div style={{ color: '#38bdf8', fontWeight: 600, marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>🟢</span> {activeModel}
          </div>
        </div>

        {/* Desktop Folder Quick Link */}
        <div style={{ marginTop: 'auto', padding: '10px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.15)', fontSize: '0.75rem', color: '#a7f3d0' }}>
          📁 <b>Desktop Output:</b><br />
          <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: '#6ee7b7' }}>~/Desktop/Research_Reports/</span>
        </div>
      </aside>

      {/* ── MAIN CHAT CANVAS ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        
        {/* Messages Stream */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', width: '100%', margin: '0 auto' }}>
          
          {/* Welcome Card if chat is empty */}
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '30px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '20px', background: 'linear-gradient(135deg, #a855f7, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', boxShadow: '0 8px 32px rgba(168, 85, 247, 0.3)' }}>
                🧠
              </div>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 700, margin: 0, color: '#f8fafc' }}>
                Mac Autonomous Operator
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.92rem', maxWidth: '560px', lineHeight: 1.5, margin: 0 }}>
                I have direct access to your Mac. Assign any task—running terminal scripts, inspecting hardware, organizing files, controlling open windows, or writing deep research directly to your Desktop.
              </p>

              {/* Quick Prompt Chips */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginTop: '14px', maxWidth: '680px', width: '100%' }}>
                {[
                  { icon: '📷', title: 'Inspect My Mac Screen', text: '📷 Inspect and analyze what is currently open on my Mac screen' },
                  { icon: '🔍', title: 'Spotlight File Search', text: 'Use Spotlight to find all python files on my Desktop' },
                  { icon: '💻', title: 'Check Battery & Processes', text: 'Check my Mac battery status and list top 5 memory processes' },
                  { icon: '🔬', title: 'Deep Research to Desktop', text: 'Research quantum error mitigation and write full paper to Desktop' }
                ].map((chip, idx) => (
                  <div
                    key={idx}
                    onClick={() => chip.icon === '📷' ? handleCaptureScreen() : handleSendMessage(chip.text)}
                    style={{
                      padding: '14px 16px',
                      borderRadius: '10px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
                      e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.3)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>{chip.icon}</span> {chip.title}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>
                      "{chip.text}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rendered Messages */}
          {messages.map((msg) => (
            <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              
              {/* Message Header */}
              <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 600, color: msg.sender === 'user' ? '#94a3b8' : '#c084fc' }}>
                  {msg.sender === 'user' ? 'You' : msg.agentName || 'Atlas (Mac Operator)'}
                </span>
                <span>•</span>
                <span>{msg.timestamp}</span>
              </div>

              {/* Message Body */}
              <div style={{
                maxWidth: '88%',
                padding: '16px 20px',
                borderRadius: '14px',
                background: msg.sender === 'user' ? '#3b82f6' : '#131b2e',
                border: msg.sender === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                color: '#f8fafc',
                fontSize: '0.92rem',
                lineHeight: 1.6,
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
              }}>
                
                {/* Expandable Thinking Block (Claude 3.7 Style) */}
                {msg.thought && (
                  <div style={{ marginBottom: '12px' }}>
                    <div
                      onClick={() => toggleThought(msg.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        color: '#a78bfa',
                        padding: '6px 10px',
                        borderRadius: '6px',
                        background: 'rgba(168, 85, 247, 0.08)',
                        border: '1px solid rgba(168, 85, 247, 0.2)'
                      }}
                    >
                      <span>💭</span>
                      <span style={{ fontWeight: 600 }}>Autonomous Reasoning & Planning</span>
                      <span style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>{expandedThoughts[msg.id] ? '▲' : '▼'}</span>
                    </div>
                    {expandedThoughts[msg.id] && (
                      <div style={{
                        marginTop: '6px',
                        padding: '10px 12px',
                        borderRadius: '6px',
                        background: 'rgba(0, 0, 0, 0.3)',
                        fontSize: '0.8rem',
                        color: '#cbd5e1',
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        borderLeft: '2px solid #a855f7'
                      }}>
                        {msg.thought}
                      </div>
                    )}
                  </div>
                )}

                {/* Inline Tool Execution Steps */}
                {msg.steps && msg.steps.length > 0 && (
                  <div style={{ marginBottom: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {msg.steps.map((tool, tIdx) => {
                      const toolKey = `${msg.id}-step-${tIdx}`;
                      const isExpanded = expandedTools[toolKey] !== false;

                      return (
                        <div key={tIdx} style={{
                          borderRadius: '8px',
                          background: 'rgba(0, 0, 0, 0.35)',
                          border: `1px solid ${tool.status === 'failed' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.25)'}`,
                          overflow: 'hidden'
                        }}>
                          {/* Tool Header Bar */}
                          <div
                            onClick={() => toggleToolDetail(toolKey)}
                            style={{
                              padding: '8px 12px',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              cursor: 'pointer',
                              background: 'rgba(255, 255, 255, 0.02)',
                              fontSize: '0.82rem'
                            }}
                          >
                            <span style={{ fontSize: '0.9rem' }}>
                              {tool.action === 'terminal' ? '💻' : tool.action === 'filesystem' ? '📁' : tool.action === 'spotlight' ? '🔍' : tool.action === 'mac_notify' ? '🔔' : tool.action === 'window_manager' ? '🪟' : '⚙️'}
                            </span>
                            <span style={{ fontWeight: 600, color: '#38bdf8', textTransform: 'capitalize' }}>
                              {tool.action}
                            </span>
                            <span style={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '320px' }}>
                              {tool.action_input?.command || tool.action_input?.path || tool.action_input?.query || tool.action_input?.message || JSON.stringify(tool.action_input)}
                            </span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.72rem', padding: '2px 6px', borderRadius: '4px', background: tool.status === 'failed' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)', color: tool.status === 'failed' ? '#fca5a5' : '#6ee7b7', fontWeight: 600 }}>
                              {tool.status === 'failed' ? '✗ Failed' : '✓ Executed'}
                            </span>
                            <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: '4px' }}>
                              {isExpanded ? '▲' : '▼'}
                            </span>
                          </div>

                          {/* Tool Output Body */}
                          {isExpanded && (
                            <div style={{ padding: '8px 12px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                              {renderToolResultContent(tool, toolKey)}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Screenshot Visual Card */}
                {msg.screenshotPath && (
                  <div style={{ margin: '10px 0', padding: '10px 14px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.25)', fontSize: '0.8rem' }}>
                    <div style={{ fontWeight: 600, color: '#38bdf8', marginBottom: '4px' }}>📷 Mac Screen Snapshot Analyzed</div>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: '#94a3b8' }}>{msg.screenshotPath}</div>
                  </div>
                )}

                {/* Desktop Report Publication Card */}
                {msg.desktopPath && (
                  <div style={{
                    margin: '12px 0',
                    padding: '12px 14px',
                    borderRadius: '8px',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontWeight: 600, color: '#34d399', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>📁</span> Documentation Published to Mac Desktop
                      </div>
                      <button
                        onClick={() => handleRevealInFinder(msg.desktopPath!)}
                        style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: 'rgba(16, 185, 129, 0.2)',
                          border: 'none',
                          color: '#6ee7b7',
                          fontSize: '0.72rem',
                          cursor: 'pointer',
                          fontWeight: 600
                        }}
                      >
                        📂 Reveal in Finder
                      </button>
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.78rem', color: '#e2e8f0', wordBreak: 'break-all' }}>
                      {msg.desktopPath}
                    </div>
                  </div>
                )}

                {/* Markdown Content */}
                <div style={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {(sending || capturingScreen) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#a78bfa', fontSize: '0.88rem' }}>
              <div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(168, 85, 247, 0.3)', borderTopColor: '#a855f7', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <span>{capturingScreen ? 'Capturing & inspecting your Mac screen...' : 'Autonomous operator executing on your Mac...'}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ── BOTTOM CHAT DOCK (Claude Style) ── */}
        <div style={{
          padding: '16px 24px 24px',
          background: 'linear-gradient(to top, #0b0f19 80%, transparent)',
          maxWidth: '900px',
          width: '100%',
          margin: '0 auto'
        }}>
          <div style={{
            background: '#131b2e',
            border: `1px solid ${isListening ? '#ef4444' : 'rgba(255, 255, 255, 0.12)'}`,
            borderRadius: '16px',
            padding: '12px 16px',
            boxShadow: isListening ? '0 0 20px rgba(239, 68, 68, 0.3)' : '0 8px 32px rgba(0, 0, 0, 0.4)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            transition: 'border 0.2s'
          }}>
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? '🎙️ Listening to your voice...' : "Assign any task on your Mac (e.g. 'Check battery', 'Search python files', 'Write script on Desktop', 'Research topic')..."}
              style={{
                width: '100%',
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#f8fafc',
                fontSize: '0.92rem',
                lineHeight: 1.5,
                resize: 'none',
                fontFamily: 'inherit'
              }}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#64748b' }}>
                <button
                  onClick={handleCaptureScreen}
                  disabled={capturingScreen || sending}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    background: 'rgba(56, 189, 248, 0.12)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    color: '#38bdf8',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}
                >
                  <span>📷</span> See Screen
                </button>

                <button
                  onClick={toggleVoiceInput}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    background: isListening ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                    border: `1px solid ${isListening ? '#ef4444' : 'rgba(255, 255, 255, 0.15)'}`,
                    color: isListening ? '#fca5a5' : '#cbd5e1',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: 600
                  }}
                >
                  <span>{isListening ? '🔴 Stop Voice' : '🎙️ Speak'}</span>
                </button>

                <span>•</span>
                <span style={{ color: is247Mode ? '#c084fc' : '#64748b' }}>
                  {is247Mode ? '⚡ 24/7 Operator Active' : 'Step Mode'}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputValue.trim() || sending}
                  style={{
                    padding: '8px 18px',
                    borderRadius: '8px',
                    background: inputValue.trim() && !sending ? 'linear-gradient(135deg, #a855f7, #3b82f6)' : 'rgba(255, 255, 255, 0.08)',
                    border: 'none',
                    color: '#fff',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: inputValue.trim() && !sending ? 'pointer' : 'default',
                    transition: 'all 0.2s',
                    boxShadow: inputValue.trim() && !sending ? '0 4px 12px rgba(168, 85, 247, 0.3)' : 'none'
                  }}
                >
                  🚀 Assign Task
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 24/7 STANDING MISSIONS MODAL ── */}
      {showJobsModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#131b2e',
            border: '1px solid rgba(168, 85, 247, 0.3)',
            borderRadius: '16px',
            maxWidth: '740px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            gap: '16px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#c084fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>⏰</span> Standing 24/7 Background Missions
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
                  Autonomous daemon tasks running periodically in the background of your Mac.
                </div>
              </div>
              <button
                onClick={() => setShowJobsModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Add New Standing Job Form */}
            <form onSubmit={handleAddJob} style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>+ Create Recurring 24/7 Task</div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Mission Name (e.g. Hourly Repo Test Runner)"
                  value={newJobName}
                  onChange={(e) => setNewJobName(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.8rem' }}
                />
                <select
                  value={newJobInterval}
                  onChange={(e) => setNewJobInterval(Number(e.target.value))}
                  style={{ padding: '8px 10px', borderRadius: '6px', background: '#0b0f19', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.8rem' }}
                >
                  <option value={300}>Every 5 Mins</option>
                  <option value={900}>Every 15 Mins</option>
                  <option value={1800}>Every 30 Mins</option>
                  <option value={3600}>Every 1 Hour</option>
                  <option value={14400}>Every 4 Hours</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="Task instruction (e.g. 'Run test suite and log any failing tests to Desktop')..."
                  value={newJobPrompt}
                  onChange={(e) => setNewJobPrompt(e.target.value)}
                  style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '0.8rem' }}
                />
                <button
                  type="submit"
                  disabled={!newJobPrompt.trim()}
                  style={{ padding: '8px 14px', borderRadius: '6px', background: 'linear-gradient(135deg, #a855f7, #3b82f6)', border: 'none', color: '#fff', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  Add Standing Job
                </button>
              </div>
            </form>

            {/* List of Standing Jobs */}
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {jobs.map((j) => (
                <div key={j.job_id} style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'rgba(0,0,0,0.25)',
                  border: `1px solid ${j.is_active ? 'rgba(168, 85, 247, 0.3)' : 'rgba(255,255,255,0.06)'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: j.is_active ? '#34d399' : '#64748b' }} />
                      <b style={{ color: '#fff', fontSize: '0.9rem' }}>{j.name}</b>
                      <span style={{ fontSize: '0.72rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', color: '#94a3b8' }}>
                        Every {Math.round(j.interval_seconds / 60)}m
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => handleToggleJob(j.job_id)}
                        style={{
                          padding: '4px 10px',
                          borderRadius: '4px',
                          background: j.is_active ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                          border: 'none',
                          color: j.is_active ? '#fca5a5' : '#6ee7b7',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        {j.is_active ? 'Pause' : 'Activate'}
                      </button>
                      <button
                        onClick={() => handleDeleteJob(j.job_id)}
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          background: 'rgba(255,255,255,0.06)',
                          border: 'none',
                          color: '#94a3b8',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>"{j.task_prompt}"</div>
                  <div style={{ fontSize: '0.72rem', color: '#64748b', display: 'flex', gap: '12px' }}>
                    <span>Executed: <b>{j.run_count} times</b></span>
                    <span>Last run: {j.last_run_at ? new Date(j.last_run_at).toLocaleTimeString() : 'Pending'}</span>
                    <span>Status: <b style={{ color: j.last_status === 'completed' ? '#34d399' : '#38bdf8' }}>{j.last_status}</b></span>
                  </div>
                  {j.last_result_summary && (
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'rgba(0,0,0,0.3)', padding: '6px 8px', borderRadius: '4px', fontStyle: 'italic' }}>
                      "{j.last_result_summary}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── UNEXPLORED GAPS DISCOVERY MODAL ── */}
      {showGapsModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#131b2e',
            border: '1px solid rgba(168, 85, 247, 0.3)',
            borderRadius: '16px',
            maxWidth: '680px',
            width: '100%',
            maxHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            gap: '16px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#c084fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🔭</span> Unexplored Research Frontiers
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
                  Identified by analyzing prior knowledge coverage & vector memory
                </div>
              </div>
              <button
                onClick={() => setShowGapsModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {loadingGaps ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#c084fc' }}>
                Analyzing previous research sessions and finding unexplored hypotheses...
              </div>
            ) : (
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {gaps.map((gap, i) => (
                  <div key={i} style={{
                    padding: '12px 14px',
                    borderRadius: '10px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>
                        {gap.topic}
                      </div>
                      <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: gap.impact === 'HIGH' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)', color: gap.impact === 'HIGH' ? '#6ee7b7' : '#fcd34d', fontWeight: 600, flexShrink: 0 }}>
                        {gap.impact} Impact
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                      {gap.rationale} <span style={{ color: '#a78bfa', fontStyle: 'italic' }}>({gap.unexplored_aspect})</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
                      <button
                        onClick={() => {
                          setShowGapsModal(false);
                          handleSendMessage(gap.topic);
                        }}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '6px',
                          background: 'linear-gradient(135deg, #a855f7, #3b82f6)',
                          border: 'none',
                          color: '#fff',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        🚀 Research This Topic & Save to Desktop
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── HIGH-RISK TOOL APPROVAL MODAL (SAFE MODE) ── */}
      {pendingPermission && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.85)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          padding: '20px'
        }}>
          <div style={{
            background: '#1a1025',
            border: '2px solid #ef4444',
            borderRadius: '16px',
            maxWidth: '540px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            gap: '16px',
            boxShadow: '0 0 40px rgba(239, 68, 68, 0.4)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ fontSize: '2rem' }}>⚠️</div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.3rem', color: '#fca5a5' }}>High-Risk Action Intercepted</h3>
                <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '4px' }}>
                  The autonomous agent is attempting to execute a potentially destructive command.
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: '8px', padding: '16px', border: '1px solid rgba(239,68,68,0.2)' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Command to Execute:</div>
              <div style={{ fontFamily: 'monospace', fontSize: '1rem', color: '#f8fafc', marginTop: '8px', wordBreak: 'break-all' }}>
                {pendingPermission.command}
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              <b>Reason:</b> {pendingPermission.reason}
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button
                onClick={() => handlePermissionDecision(false)}
                disabled={handlingPermission}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Deny Execution
              </button>
              <button
                onClick={() => handlePermissionDecision(true)}
                disabled={handlingPermission}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '8px',
                  background: '#ef4444',
                  border: 'none',
                  color: '#fff',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(239,68,68,0.4)'
                }}
              >
                Approve & Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── BRAIN INSPECTOR MODAL ── */}
      {showMemoryModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#131b2e',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: '16px',
            maxWidth: '800px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            gap: '16px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#facc15', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🧠</span> Brain Inspector
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '2px' }}>
                  Live view of the Agent's Short-Term Context & Long-Term Vector Memory
                </div>
              </div>
              <button
                onClick={() => setShowMemoryModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {loadingMemory || !memoryData ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#facc15' }}>
                Synapsing neural pathways... Loading memory blocks...
              </div>
            ) : (
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '8px' }}>Current Turn</div>
                    <div style={{ fontSize: '1.5rem', color: '#38bdf8', fontWeight: 700 }}>{memoryData.turn}</div>
                  </div>
                  <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '8px' }}>Vector Store Entries</div>
                    <div style={{ fontSize: '1.5rem', color: '#a855f7', fontWeight: 700 }}>{memoryData.vector_store_entries}</div>
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <h4 style={{ margin: '0 0 12px 0', color: '#cbd5e1', fontSize: '0.9rem' }}>Active Context Dictionary</h4>
                  <pre style={{ margin: 0, padding: '12px', background: '#050811', borderRadius: '8px', color: '#6ee7b7', fontSize: '0.75rem', overflowX: 'auto' }}>
                    {JSON.stringify(memoryData.context || {}, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── SETTINGS MODAL ── */}
      {showSettingsModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#131b2e',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            maxWidth: '500px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px',
            gap: '24px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>⚙️</span> System Settings
                </h3>
              </div>
              <button
                onClick={() => setShowSettingsModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>High-Risk Safe Mode</div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>Intercept dangerous commands (e.g. sudo, rm) and ask for approval.</div>
                  </div>
                  <input type="checkbox" checked={true} readOnly style={{ width: '18px', height: '18px', accentColor: '#ef4444' }} />
                </div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem', marginBottom: '12px' }}>Active Base Model</div>
                <select 
                  value={activeModel} 
                  disabled 
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#050811', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', fontSize: '0.85rem' }}
                >
                  <option value={activeModel}>{activeModel}</option>
                </select>
                <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '8px' }}>Model selection is currently managed via the backend config.yaml.</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Global CSS Animation for Spinners */}
      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
