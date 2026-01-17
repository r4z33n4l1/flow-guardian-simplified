"use client";

import { useEffect, useState, useCallback } from "react";

export interface Session {
  id: string;
  timestamp: string;
  branch: string;
  summary: string;
  context?: {
    decisions?: string[];
    next_steps?: string[];
    blockers?: string[];
  };
}

export interface Learning {
  id: string;
  text?: string;
  insight?: string;
  tags: string[];
  timestamp: string;
  team?: boolean;
  author?: string;
}

export interface ActivityState {
  sessions: Session[];
  learnings: Learning[];
  connected: boolean;
  lastUpdate: Date | null;
}

export function useActivityStream() {
  const [state, setState] = useState<ActivityState>({
    sessions: [],
    learnings: [],
    connected: false,
    lastUpdate: null,
  });

  const connect = useCallback(() => {
    const eventSource = new EventSource("/api/activity/stream");

    eventSource.onopen = () => {
      setState((prev) => ({ ...prev, connected: true }));
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "init":
            setState((prev) => ({
              ...prev,
              connected: true,
              lastUpdate: new Date(),
            }));
            break;

          case "sessions":
            setState((prev) => ({
              ...prev,
              sessions: data.sessions || [],
              lastUpdate: new Date(),
            }));
            break;

          case "learnings":
            setState((prev) => ({
              ...prev,
              learnings: data.learnings || [],
              lastUpdate: new Date(),
            }));
            break;

          case "heartbeat":
            setState((prev) => ({
              ...prev,
              lastUpdate: new Date(data.timestamp),
            }));
            break;

          case "error":
            console.error("Activity stream error:", data.message);
            break;
        }
      } catch (error) {
        console.error("Failed to parse activity event:", error);
      }
    };

    eventSource.onerror = () => {
      setState((prev) => ({ ...prev, connected: false }));
      eventSource.close();

      // Reconnect after 5 seconds
      setTimeout(connect, 5000);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  return state;
}
