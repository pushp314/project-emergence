'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

export interface SandboxEvent {
  type: string;
  agent_id?: string;
  content?: string;
  intent?: string;
  reason?: string;
  timestamp?: string;
  payload?: any;
  [key: string]: any;
}

export function useEventStream(url: string) {
  const [events, setEvents] = useState<SandboxEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isUnmountedRef = useRef(false);

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;

    try {
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }
        reconnectAttemptsRef.current = 0;
        setIsConnected(true);
        console.debug('Connected to AI Sandbox event stream');
      };

      ws.onmessage = (event) => {
        if (isUnmountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          setEvents((prev) => [...prev, data]);
        } catch (err) {
          console.warn('Failed to parse event from server:', err);
        }
      };

      ws.onclose = (event) => {
        if (isUnmountedRef.current) return;
        setIsConnected(false);
        wsRef.current = null;

        // Schedule auto-reconnect with exponential backoff (max 5s)
        const delay = Math.min(1000 * Math.pow(1.5, reconnectAttemptsRef.current), 5000);
        reconnectAttemptsRef.current += 1;
        
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        // Suppress noisy Next.js dev overlay modal on transient disconnects
        if (!isUnmountedRef.current) {
          setIsConnected(false);
        }
      };
    } catch (e) {
      console.debug('WebSocket connection attempt caught error:', e);
    }
  }, [url]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        // Prevent onclose trigger during intentional unmount
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { events, isConnected, clearEvents: () => setEvents([]) };
}
