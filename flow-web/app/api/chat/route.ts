import { streamChatCompletion, chatCompletion, buildSystemPrompt, type Message } from '@/lib/cerebras';

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

// Check if query is about the conversation itself (meta-query)
function isMetaQuery(query: string): boolean {
  const metaPatterns = [
    /last (question|message|thing)/i,
    /previous (question|message)/i,
    /what did (i|you) (ask|say)/i,
    /repeat/i,
    /earlier in (this|our) (chat|conversation)/i,
  ];
  return metaPatterns.some(pattern => pattern.test(query));
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

// Format conversation history for context
function formatConversationHistory(messages: Array<{ role: string; content: string }>): string {
  if (messages.length === 0) return '';

  const history = messages.slice(-10).map((m, i) => {
    const role = m.role === 'user' ? 'User' : 'Assistant';
    return `${role}: ${m.content}`;
  }).join('\n');

  return `CONVERSATION HISTORY:\n${history}`;
}

// Quick check: Can Cerebras answer from local context or conversation history?
async function canAnswerFromContext(
  query: string,
  context: string[],
  conversationHistory: string,
  apiKey: string
): Promise<{ canAnswer: boolean; quickAnswer?: string }> {
  const isMeta = isMetaQuery(query);

  // For meta queries, we can answer from conversation history alone
  if (isMeta && conversationHistory) {
    const metaPrompt = `Based on the conversation history below, answer this question: "${query}"

${conversationHistory}

Provide a brief, direct answer.`;

    try {
      const response = await chatCompletion(
        [{ role: 'user', content: metaPrompt }],
        apiKey,
        { max_tokens: 300, temperature: 0.3 }
      );
      console.log('[Chat] Answering meta-query from conversation history (fast path)');
      return { canAnswer: true, quickAnswer: response };
    } catch (error) {
      console.error('[Chat] Meta-query check failed:', error);
    }
  }

  // For knowledge queries, check if we have relevant context
  if (context.length === 0) {
    return { canAnswer: false };
  }

  const checkPrompt = `Based on the context below, can you answer this question: "${query}"

${conversationHistory ? conversationHistory + '\n\n---\n\n' : ''}KNOWLEDGE BASE:
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

    // Format conversation history for context
    const conversationHistory = formatConversationHistory(messages.slice(0, -1)); // Exclude current message

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

    // Quick check: Can we answer from local context or conversation history?
    const { canAnswer, quickAnswer } = await canAnswerFromContext(contextQuery, context, conversationHistory, apiKey);

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
