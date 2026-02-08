import { useEffect, useRef, useState, useCallback } from 'react';
import { fetchActivity, type ActivityEntry } from '../api/client';

export interface ActivityEvent {
  type: string;
  bot_id: string;
  bot_name: string;
  action: string;
  details: Record<string, unknown>;
  tokens_used: number;
  timestamp: string;
}

interface UseActivityStreamReturn {
  events: ActivityEntry[];
  connected: boolean;
}

export function useActivityStream(maxEvents = 50): UseActivityStreamReturn {
  const [events, setEvents] = useState<ActivityEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const pollIntervalRef = useRef<ReturnType<typeof setInterval>>();
  const reconnectDelayRef = useRef(1000);
  const nextIdRef = useRef(-1); // Negative IDs for WS events to avoid collisions
  const unmountedRef = useRef(false);

  // Load initial data via HTTP
  const loadInitial = useCallback(async () => {
    try {
      const data = await fetchActivity(maxEvents);
      setEvents(data);
    } catch (e) {
      console.error('Failed to load initial activity:', e);
    }
  }, [maxEvents]);

  // Fallback polling when WS is disconnected
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return;
    pollIntervalRef.current = setInterval(async () => {
      try {
        const data = await fetchActivity(maxEvents);
        setEvents(data);
      } catch (e) {
        console.error('Polling failed:', e);
      }
    }, 10000);
  }, [maxEvents]);

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = undefined;
    }
  }, []);

  const connectWs = useCallback(() => {
    if (unmountedRef.current) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/activity`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectDelayRef.current = 1000; // Reset backoff
      stopPolling();
    };

    ws.onmessage = (event) => {
      try {
        const data: ActivityEvent = JSON.parse(event.data);
        if (data.type === 'heartbeat_complete') {
          const newEntry: ActivityEntry = {
            id: nextIdRef.current--,
            bot_id: data.bot_id,
            action_type: data.action,
            details: data.details as ActivityEntry['details'],
            tokens_used: data.tokens_used,
            created_at: data.timestamp,
          };
          setEvents((prev) => [newEntry, ...prev].slice(0, maxEvents));
        }
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      startPolling(); // Fallback to polling

      // Reconnect with exponential backoff (max 30s)
      const delay = reconnectDelayRef.current;
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectDelayRef.current = Math.min(delay * 2, 30000);
        connectWs();
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [maxEvents, startPolling, stopPolling]);

  useEffect(() => {
    unmountedRef.current = false;
    loadInitial();
    connectWs();

    return () => {
      unmountedRef.current = true;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      stopPolling();
    };
  }, [loadInitial, connectWs, stopPolling]);

  return { events, connected };
}
