import { streamChatCompletion, chatCompletion, buildSystemPrompt, type Message } from '@/lib/cerebras';

const FLOW_GUARDIAN_URL = process.env.FLOW_GUARDIAN_URL || 'http://localhost:8090';

interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
}

interface RecallResponse {
  query: string;
  results: Array<{
    content: string;
    source: string;
    timestamp?: string;
  }>;
  sources: {
    local: boolean;
    cloud: boolean;
  };
}

async function getContextFromBackboard(query: string, localOnly: boolean = true): Promise<string[]> {
  try {
    const response = await fetch(`${FLOW_GUARDIAN_URL}/recall`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, local_only: localOnly }),
    });

    if (!response.ok) {
      console.error('Failed to fetch context from Flow Guardian');
      return [];
    }

    const data: RecallResponse = await response.json();
    return data.results.map((r) => {
      const parts = [r.content];
      if (r.source) parts.push(`Source: ${r.source}`);
      if (r.timestamp) parts.push(`Time: ${r.timestamp}`);
      return parts.join('\n');
    });
  } catch (error) {
    console.error('Error fetching context:', error);
    return [];
  }
}

// Quick check: Can Cerebras answer from local context?
async function canAnswerFromContext(
  query: string,
  context: string[],
  apiKey: string
): Promise<{ canAnswer: boolean; quickAnswer?: string }> {
  if (context.length === 0) {
    return { canAnswer: false };
  }

  const checkPrompt = `Based on the context below, can you answer this question: "${query}"

CONTEXT:
${context.slice(0, 5).join('\n---\n')}

If you CAN answer from this context, provide a brief answer.
If you CANNOT answer (context doesn't contain relevant info), respond ONLY with: NEED_MORE_CONTEXT`;

  try {
    const response = await chatCompletion(
      [{ role: 'user', content: checkPrompt }],
      apiKey,
      { max_tokens: 300, temperature: 0.3 }
    );

    if (response.trim() === 'NEED_MORE_CONTEXT' || response.includes('NEED_MORE_CONTEXT')) {
      console.log('[Chat] Local context insufficient, will fetch from Backboard');
      return { canAnswer: false };
    }

    console.log('[Chat] Answering from local context (fast path)');
    return { canAnswer: true, quickAnswer: response };
  } catch (error) {
    console.error('[Chat] Quick check failed:', error);
    return { canAnswer: false };
  }
}

export async function POST(request: Request) {
  try {
    const body: ChatRequest = await request.json();
    const { messages } = body;

    if (!messages || messages.length === 0) {
      return new Response(JSON.stringify({ error: 'Messages are required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const apiKey = process.env.CEREBRAS_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'CEREBRAS_API_KEY not configured' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get the latest user message for context query
    const latestUserMessage = messages.filter((m) => m.role === 'user').pop();
    const contextQuery = latestUserMessage?.content || '';

    // PHASE 1: Try with local context only (fast)
    console.log('[Chat] Phase 1: Fetching local context...');
    let context = await getContextFromBackboard(contextQuery, true); // local_only=true

    // Quick check: Can we answer from local context?
    const { canAnswer, quickAnswer } = await canAnswerFromContext(contextQuery, context, apiKey);

    // PHASE 2: If local context insufficient, fetch from Backboard
    if (!canAnswer) {
      console.log('[Chat] Phase 2: Fetching from Backboard...');
      context = await getContextFromBackboard(contextQuery, false); // Include Backboard
    }

    // If we got a quick answer, return it directly (no streaming needed)
    if (canAnswer && quickAnswer) {
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          const data = JSON.stringify({ content: quickAnswer });
          controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          controller.enqueue(encoder.encode('data: [DONE]\n\n'));
          controller.close();
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // Build messages with system prompt for full response
    const systemPrompt = buildSystemPrompt(context);
    const fullMessages: Message[] = [
      { role: 'system', content: systemPrompt },
      ...messages.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
    ];

    // Create a ReadableStream for SSE-style streaming
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        try {
          for await (const chunk of streamChatCompletion(fullMessages, apiKey)) {
            // Send as SSE format
            const data = JSON.stringify({ content: chunk });
            controller.enqueue(encoder.encode(`data: ${data}\n\n`));
          }
          // Send done signal
          controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        } catch (error) {
          console.error('Streaming error:', error);
          const errorData = JSON.stringify({ error: 'Stream error occurred' });
          controller.enqueue(encoder.encode(`data: ${errorData}\n\n`));
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
