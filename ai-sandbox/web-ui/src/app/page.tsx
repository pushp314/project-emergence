'use client';

import React from 'react';
import { useEventStream } from '../hooks/useEventStream';
import { CommandCenter } from '../components/CommandCenter';

export default function Home() {
  const { events, isConnected, clearEvents } = useEventStream('ws://localhost:8001/ws/events');

  return (
    <CommandCenter
      events={events}
      isConnected={isConnected}
      clearEvents={clearEvents}
    />
  );
}
