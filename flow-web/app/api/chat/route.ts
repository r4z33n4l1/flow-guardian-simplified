import { streamChatCompletion, buildSystemPrompt, type Message } from '@/lib/cerebras';

const FLOW_GUARDIAN_URL = process.env.FLOW_GUARDIAN_URL || 'http://localhost:8090';

// Background task to analyze conversation and create Linear issues if needed
async function analyzeConversationForLinear(messages: Array<{ role: string; content: string }>) {
  try {
    // Build conversation text
    const conversationText = messages.map(m => `${m.role}: ${m.content}`).join('\n');

    // Call Flow Guardian to analyze and potentially create issues
    const response = await fetch(`${FLOW_GUARDIAN_URL}/analyze-for-linear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation: conversationText }),
    });

    if (response.ok) {
      const result = await response.json();
      console.log('[Chat] Linear analysis result:', result);
    }
  } catch (error) {
    // Don't fail the main request if analysis fails
    console.log('[Chat] Linear analysis skipped (endpoint may not exist):', error);
  }
}

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

// Check if query is asking about the system's knowledge/context (debug query)
function isDebugQuery(query: string): boolean {
  const debugPatterns = [
    /your (local )?(context|knowledge|memory)/i,
    /what do you know/i,
    /show me.*(context|knowledge|memory)/i,
    /what('s| is) in your (memory|knowledge|context)/i,
    /list.*(learnings|knowledge|context)/i,
  ];
  return debugPatterns.some(pattern => pattern.test(query));
}

// Format local context as a readable response
function formatContextAsResponse(context: string[]): string {
  if (context.length === 0) {
    return "I don't have any local context stored yet. Try adding some learnings or uploading documents.";
  }

  const formatted = context.slice(0, 10).map((item, i) => `${i + 1}. ${item}`).join('\n\n');
  return `Here's what I have in my local knowledge base:\n\n${formatted}`;
}

// Check if local context has relevant terms for the query
function hasRelevantLocalContext(query: string, context: string[]): boolean {
  if (context.length === 0) return false;
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const contextText = context.join(' ').toLowerCase();
  return queryWords.some(word => contextText.includes(word));
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

    // Handle debug queries - return local context directly
    if (isDebugQuery(contextQuery)) {
      console.log('[Chat] Debug query - returning local context directly');
      const debugResponse = formatContextAsResponse(context);
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          const data = JSON.stringify({ content: debugResponse });
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

    // PHASE 2: If local context insufficient, fetch from Backboard
    if (!hasRelevantLocalContext(contextQuery, context)) {
      console.log('[Chat] Phase 2: Local context insufficient, fetching from Backboard...');
      context = await getContextFromBackboard(contextQuery, false); // Include Backboard
    } else {
      console.log('[Chat] Local context has relevant terms, using local context');
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
    let fullResponse = '';
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        try {
          for await (const chunk of streamChatCompletion(fullMessages, apiKey)) {
            // Send as SSE format
            const data = JSON.stringify({ content: chunk });
            controller.enqueue(encoder.encode(`data: ${data}\n\n`));
            fullResponse += chunk;
          }
          // Send done signal
          controller.enqueue(encoder.encode('data: [DONE]\n\n'));

          // Fire-and-forget: Analyze conversation for potential Linear issues
          // This runs in background and doesn't block the response
          const allMessages = [...messages, { role: 'assistant', content: fullResponse }];
          analyzeConversationForLinear(allMessages).catch(() => {});
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
