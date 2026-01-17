// Cerebras streaming client for chat completions

const CEREBRAS_API_URL = 'https://api.cerebras.ai/v1/chat/completions';

export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface StreamOptions {
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

const MODELS = ['llama-3.3-70b', 'llama3.1-8b']; // Fallback models

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 2,
  delay = 1000
): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, options);
      if (response.ok || response.status < 500) return response;
      // Server error - retry
      if (attempt < retries) {
        console.log(`[Cerebras] Retry ${attempt + 1}/${retries} after ${response.status}`);
        await new Promise(r => setTimeout(r, delay * (attempt + 1)));
      }
    } catch (error) {
      if (attempt < retries) {
        console.log(`[Cerebras] Retry ${attempt + 1}/${retries} after connection error`);
        await new Promise(r => setTimeout(r, delay * (attempt + 1)));
      } else {
        throw error;
      }
    }
  }
  return fetch(url, options); // Final attempt
}

export async function* streamChatCompletion(
  messages: Message[],
  apiKey: string,
  options: StreamOptions = {}
): AsyncGenerator<string, void, unknown> {
  const {
    model = MODELS[0],
    temperature = 0.7,
    max_tokens = 2000,
  } = options;

  const response = await fetchWithRetry(CEREBRAS_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens,
      stream: true,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Cerebras API error: ${response.status} - ${error}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.delta?.content;
          if (content) yield content;
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}

// Non-streaming completion
export async function chatCompletion(
  messages: Message[],
  apiKey: string,
  options: StreamOptions = {}
): Promise<string> {
  const {
    model = MODELS[0],
    temperature = 0.7,
    max_tokens = 2000,
  } = options;

  const response = await fetchWithRetry(CEREBRAS_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Cerebras API error: ${response.status} - ${error}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || '';
}

// Build system prompt for Flow Guardian
export function buildSystemPrompt(context: string[]): string {
  return `You are Flow Guardian, a team memory assistant that helps users understand what their development team is working on.

IMPORTANT INSTRUCTIONS:
1. Answer based ONLY on the context provided below
2. If you don't have enough context to answer, say so clearly
3. Cite sources with @author and timestamps when available
4. Keep responses concise and actionable
5. Highlight blockers, decisions, and key insights
6. Use markdown formatting for readability

CONTEXT FROM TEAM MEMORY:
${context.length > 0 ? context.join('\n\n---\n\n') : 'No relevant context found.'}

Remember: You are helping non-developers understand technical work. Explain things clearly without jargon when possible.`;
}
