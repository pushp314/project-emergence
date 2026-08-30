'use client';

import React, { useEffect, useState } from 'react';

export function PermissionModal() {
  const [requests, setRequests] = useState<any[]>([]);

  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        const res = await fetch('http://localhost:8001/api/permissions');
        const data = await res.json();
        setRequests(data.permissions || []);
      } catch (err) {
        console.error('Failed to fetch permissions', err);
      }
    };

    fetchPermissions();
    const interval = setInterval(fetchPermissions, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (id: string, action: 'approve' | 'deny') => {
    try {
      await fetch(`http://localhost:8001/api/permissions/${id}/${action}`, { method: 'POST' });
      setRequests(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      console.error('Failed to process permission', err);
    }
  };

  if (requests.length === 0) return null;

  const req = requests[0]; // Show first pending request

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0, 0, 0, 0.6)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="glass-panel fade-in" style={{ padding: '30px', width: '500px', maxWidth: '90%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <span style={{ fontSize: '24px' }}>⚠️</span>
          <h2 style={{ color: 'var(--warning)', margin: 0 }}>High Risk Action Requested</h2>
        </div>
        
        <p style={{ marginBottom: '20px' }}>
          Agent <strong style={{ color: 'var(--accent)' }}>{req.agent_id}</strong> wants to execute <strong>{req.action}</strong>.
        </p>

        <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', marginBottom: '24px', fontFamily: 'monospace', fontSize: '0.9rem', whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto' }}>
          {JSON.stringify(req.details, null, 2)}
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button className="btn btn-danger" onClick={() => handleAction(req.id, 'deny')}>
            Deny
          </button>
          <button className="btn btn-primary" onClick={() => handleAction(req.id, 'approve')}>
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
