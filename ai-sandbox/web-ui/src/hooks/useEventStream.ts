'use client';

import { useEffect, useState, useRef } from 'react';

export interface SandboxEvent {
  type: string;
  agent_id?: string;
  content?: string;
  intent?: string;
  reason?: string;
  timestamp?: string;
  [key: string]: any;
}

export function useEventStream(url: string) {
  const [events, setEvents] = useState<SandboxEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to event stream');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents(prev => [...prev, data]);
      } catch (err) {
        console.error('Failed to parse event', err);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from event stream');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [url]);

  return { events, isConnected, clearEvents: () => setEvents([]) };
}
