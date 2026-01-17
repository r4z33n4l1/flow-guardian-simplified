import { NextRequest } from "next/server";

const FLOW_GUARDIAN_URL =
  process.env.FLOW_GUARDIAN_URL || "http://localhost:8090";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();

  // Track controller state
  let controllerClosed = false;
  let pollInterval: ReturnType<typeof setInterval> | null = null;

  const stream = new ReadableStream({
    start(controller) {
      // Safe send function that checks controller state
      const send = (data: string) => {
        if (controllerClosed) return;
        try {
          controller.enqueue(encoder.encode(`data: ${data}\n\n`));
        } catch {
          controllerClosed = true;
          stopPolling();
        }
      };

      // Stop polling and cleanup
      const stopPolling = () => {
        if (pollInterval) {
          clearInterval(pollInterval);
          pollInterval = null;
        }
      };

      // Handle client disconnect
      request.signal.addEventListener("abort", () => {
        controllerClosed = true;
        stopPolling();
      });

      // Initial status fetch (don't await in start)
      fetch(`${FLOW_GUARDIAN_URL}/status`)
        .then(res => res.ok ? res.json() : null)
        .then(status => {
          if (status && !controllerClosed) {
            send(JSON.stringify({ type: "init", status }));
          }
        })
        .catch(() => {});

      // Start polling every 5 seconds
      pollInterval = setInterval(() => {
        if (controllerClosed) {
          stopPolling();
          return;
        }

        // Fetch sessions and learnings in parallel
        Promise.all([
          fetch(`${FLOW_GUARDIAN_URL}/sessions?limit=5`).then(r => r.ok ? r.json() : null).catch(() => null),
          fetch(`${FLOW_GUARDIAN_URL}/learnings?limit=5`).then(r => r.ok ? r.json() : null).catch(() => null),
        ]).then(([sessionsData, learningsData]) => {
          if (controllerClosed) return;

          if (sessionsData?.sessions) {
            send(JSON.stringify({ type: "sessions", sessions: sessionsData.sessions }));
          }
          if (learningsData?.learnings) {
            send(JSON.stringify({ type: "learnings", learnings: learningsData.learnings }));
          }

          // Heartbeat
          send(JSON.stringify({ type: "heartbeat", timestamp: new Date().toISOString() }));
        }).catch(() => {});
      }, 5000);
    },

    cancel() {
      controllerClosed = true;
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
