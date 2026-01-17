import { NextRequest } from "next/server";

const FLOW_GUARDIAN_URL =
  process.env.FLOW_GUARDIAN_URL || "http://localhost:8090";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      // Send initial state
      try {
        const statusRes = await fetch(`${FLOW_GUARDIAN_URL}/status`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "init", status })}\n\n`
            )
          );
        }
      } catch (error) {
        console.error("Failed to fetch initial status:", error);
      }

      // Poll for updates every 5 seconds
      const interval = setInterval(async () => {
        try {
          // Check for recent sessions
          const sessionsRes = await fetch(
            `${FLOW_GUARDIAN_URL}/sessions?limit=5`
          );
          if (sessionsRes.ok) {
            const data = await sessionsRes.json();
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({ type: "sessions", sessions: data.sessions })}\n\n`
              )
            );
          }

          // Check for recent learnings
          const learningsRes = await fetch(
            `${FLOW_GUARDIAN_URL}/learnings?limit=5`
          );
          if (learningsRes.ok) {
            const data = await learningsRes.json();
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({ type: "learnings", learnings: data.learnings })}\n\n`
              )
            );
          }

          // Send heartbeat
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "heartbeat", timestamp: new Date().toISOString() })}\n\n`
            )
          );
        } catch (error) {
          console.error("Activity stream error:", error);
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "error", message: "Failed to fetch updates" })}\n\n`
            )
          );
        }
      }, 5000);

      // Cleanup on abort
      request.signal.addEventListener("abort", () => {
        clearInterval(interval);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
