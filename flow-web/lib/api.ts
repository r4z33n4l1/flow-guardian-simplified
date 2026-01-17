// Flow Guardian API client

const API_URL = process.env.NEXT_PUBLIC_FLOW_GUARDIAN_URL || 'http://localhost:8090';

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

export interface StatusResponse {
  backboard_connected: boolean;
  team_available: boolean;
  last_capture: string | null;
  last_summary: string | null;
}

export interface CaptureResponse {
  saved: boolean;
  local: boolean;
  cloud: boolean;
  branch: string;
}

export interface RecallResponse {
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

class FlowGuardianAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  async health(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error('API not available');
    return res.json();
  }

  async status(): Promise<StatusResponse> {
    const res = await fetch(`${this.baseUrl}/status`);
    if (!res.ok) throw new Error('Failed to get status');
    return res.json();
  }

  async capture(data: {
    summary: string;
    decisions?: string[];
    next_steps?: string[];
    blockers?: string[];
  }): Promise<CaptureResponse> {
    const res = await fetch(`${this.baseUrl}/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to capture context');
    return res.json();
  }

  async recall(query: string): Promise<RecallResponse> {
    const res = await fetch(`${this.baseUrl}/recall`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) throw new Error('Failed to recall context');
    return res.json();
  }

  async learn(data: {
    insight: string;
    tags?: string[];
    share_with_team?: boolean;
  }): Promise<{ stored: boolean; personal: boolean; team: boolean }> {
    const res = await fetch(`${this.baseUrl}/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to store learning');
    return res.json();
  }

  async team(query: string): Promise<{
    available: boolean;
    query?: string;
    results?: string;
    message?: string;
  }> {
    const res = await fetch(`${this.baseUrl}/team`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) throw new Error('Failed to query team');
    return res.json();
  }

  async sessions(params?: {
    page?: number;
    limit?: number;
    branch?: string;
  }): Promise<{ sessions: Session[]; total: number; page: number }> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.branch) searchParams.set('branch', params.branch);

    const res = await fetch(`${this.baseUrl}/sessions?${searchParams}`);
    if (!res.ok) throw new Error('Failed to get sessions');
    return res.json();
  }

  async learnings(params?: {
    page?: number;
    limit?: number;
    tag?: string;
    team?: boolean;
  }): Promise<{ learnings: Learning[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.tag) searchParams.set('tag', params.tag);
    if (params?.team !== undefined) searchParams.set('team', String(params.team));

    const res = await fetch(`${this.baseUrl}/learnings?${searchParams}`);
    if (!res.ok) throw new Error('Failed to get learnings');
    return res.json();
  }

  async stats(): Promise<{
    sessions_count: number;
    learnings_count: number;
    team_learnings: number;
    top_tags: string[];
  }> {
    const res = await fetch(`${this.baseUrl}/stats`);
    if (!res.ok) throw new Error('Failed to get stats');
    return res.json();
  }
}

export const api = new FlowGuardianAPI();
export default api;
