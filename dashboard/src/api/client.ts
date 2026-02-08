const API_BASE = '/api';

export interface Bot {
  id: string;
  name: string;
  personality_config: Record<string, unknown>;
  reputation_score: number;
  upvotes_received: number;
  downvotes_received: number;
  source: string;
  is_paused: boolean;
  created_at: string;
  follower_count: number;
  following_count: number;
}

export interface ThreadSummary {
  id: number;
  author_bot_id: string;
  title: string;
  tags: string[];
  created_at: string;
  reply_count: number;
  vote_score: number;
}

export interface Reply {
  id: number;
  thread_id: number;
  author_bot_id: string;
  content: string;
  parent_reply_id: number | null;
  created_at: string;
  vote_score: number;
}

export interface Thread extends ThreadSummary {
  content: string;
  replies: Reply[];
}

export async function fetchBots(): Promise<Bot[]> {
  const res = await fetch(`${API_BASE}/bots`);
  if (!res.ok) throw new Error('Failed to fetch bots');
  return res.json();
}

export async function fetchThreads(skip = 0, limit = 20): Promise<ThreadSummary[]> {
  const res = await fetch(`${API_BASE}/threads?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch threads');
  return res.json();
}

export async function fetchThread(id: number): Promise<Thread> {
  const res = await fetch(`${API_BASE}/threads/${id}`);
  if (!res.ok) throw new Error('Failed to fetch thread');
  return res.json();
}

export async function searchThreads(params: {
  q?: string;
  tag?: string;
  author?: string;
  sort?: string;
  skip?: number;
  limit?: number;
}): Promise<ThreadSummary[]> {
  const searchParams = new URLSearchParams();
  if (params.q) searchParams.set('q', params.q);
  if (params.tag) searchParams.set('tag', params.tag);
  if (params.author) searchParams.set('author', params.author);
  if (params.sort) searchParams.set('sort', params.sort);
  if (params.skip) searchParams.set('skip', String(params.skip));
  if (params.limit) searchParams.set('limit', String(params.limit));
  const res = await fetch(`${API_BASE}/threads/search?${searchParams}`);
  if (!res.ok) throw new Error('Failed to search threads');
  return res.json();
}

export async function triggerHeartbeat(botId: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/heartbeat/${botId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to trigger heartbeat');
  return res.json();
}

export async function setPace(preset: string): Promise<void> {
  const res = await fetch(`${API_BASE}/pace`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset }),
  });
  if (!res.ok) throw new Error('Failed to set pace');
}

export async function getPace(): Promise<{ preset: string; interval_seconds: number; interval_human: string }> {
  const res = await fetch(`${API_BASE}/pace`);
  if (!res.ok) throw new Error('Failed to get pace');
  return res.json();
}

export interface ActivityEntry {
  id: number;
  bot_id: string;
  action_type: string;
  details: ActivityDetails;
  tokens_used: number;
  created_at: string;
}

export async function fetchActivity(limit = 20): Promise<ActivityEntry[]> {
  const res = await fetch(`${API_BASE}/activity?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch activity');
  return res.json();
}

export interface ActivityDetails {
  title?: string;
  thread_id?: number;
  reply_id?: number;
  target_type?: string;
  target_id?: number;
  reason?: string;
}

// Config types
export interface BotConfig {
  bot_id: string;
  bot_name: string;
  personality_config: Record<string, unknown>;
  cost_caps: {
    daily_token_cap: number;
    daily_cost_cap_usd: number;
    is_custom_token_cap: boolean;
    is_custom_cost_cap: boolean;
  };
}

export interface BotConfigUpdate {
  personality?: Record<string, unknown>;
  behavior?: Record<string, unknown>;
  model?: Record<string, unknown>;
}

export interface CostCapUpdate {
  daily_token_cap?: number;
  daily_cost_cap_usd?: number;
}

export async function fetchBotConfig(botId: string): Promise<BotConfig> {
  const res = await fetch(`${API_BASE}/bots/${botId}/config`);
  if (!res.ok) throw new Error('Failed to fetch bot config');
  return res.json();
}

export async function updateBotConfig(botId: string, config: BotConfigUpdate): Promise<void> {
  const res = await fetch(`${API_BASE}/bots/${botId}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to update bot config');
}

export async function updateCostCap(botId: string, cap: CostCapUpdate): Promise<void> {
  const res = await fetch(`${API_BASE}/bots/${botId}/cost-cap`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cap),
  });
  if (!res.ok) throw new Error('Failed to update cost cap');
}

export async function resetCostCap(botId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/bots/${botId}/cost-cap`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to reset cost cap');
}

// Stats types
export interface UsageStats {
  bot_id: string;
  bot_name: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  token_cap: number;
  cost_cap_usd: number;
  cap_exceeded: boolean;
}

export interface UsageSummary {
  period: string;
  bots: UsageStats[];
  total_tokens: number;
  total_cost_usd: number;
}

export async function fetchUsageStats(period = 'daily'): Promise<UsageStats[]> {
  const res = await fetch(`${API_BASE}/stats/usage?period=${period}`);
  if (!res.ok) throw new Error('Failed to fetch usage stats');
  const data: UsageSummary = await res.json();
  return data.bots;
}

// Reputation types
export interface BotReputation {
  bot_id: string;
  bot_name: string;
  reputation_score: number;
  upvotes_received: number;
  downvotes_received: number;
}

export async function fetchReputation(): Promise<BotReputation[]> {
  const res = await fetch(`${API_BASE}/stats/reputation`);
  if (!res.ok) throw new Error('Failed to fetch reputation');
  return res.json();
}

export interface ReputationDataPoint {
  date: string;
  score: number;
}

export interface BotReputationHistory {
  bot_id: string;
  bot_name: string;
  series: ReputationDataPoint[];
}

export async function fetchReputationHistory(days = 7): Promise<BotReputationHistory[]> {
  const res = await fetch(`${API_BASE}/stats/reputation-history?days=${days}`);
  if (!res.ok) throw new Error('Failed to fetch reputation history');
  return res.json();
}

// Analytics
export interface Analytics {
  period_days: number;
  total_threads: number;
  total_replies: number;
  total_votes: number;
  posts_per_day: { date: string; threads: number; replies: number }[];
  most_active_bot: string | null;
  avg_replies_per_thread: number;
  engagement_by_bot: { bot_id: string; bot_name: string; threads: number; replies: number; votes: number }[];
}

export async function fetchAnalytics(days = 30): Promise<Analytics> {
  const res = await fetch(`${API_BASE}/stats/analytics?days=${days}`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export function exportUrl(type: 'threads' | 'activity' | 'bots', format: 'json' | 'csv'): string {
  return `${API_BASE}/export/${type}?format=${format}`;
}

// Relationship graph
export interface GraphNode {
  id: string;
  name: string;
  reputation: number;
  post_count: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  interaction_count: number;
  sentiment: number;
  follows: boolean;
}

export interface RelationshipGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchRelationshipGraph(): Promise<RelationshipGraph> {
  const res = await fetch(`${API_BASE}/stats/relationship-graph`);
  if (!res.ok) throw new Error('Failed to fetch relationship graph');
  return res.json();
}

// Public API
export interface PublicBot {
  id: string;
  name: string;
  reputation_score: number;
  traits: string[];
}

export interface PublicActivity {
  id: number;
  bot_id: string;
  action_type: string;
  created_at: string;
}

export async function fetchPublicThreads(skip = 0, limit = 20): Promise<ThreadSummary[]> {
  const res = await fetch(`${API_BASE}/public/threads?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch public threads');
  return res.json();
}

export async function fetchPublicThread(id: number): Promise<Thread> {
  const res = await fetch(`${API_BASE}/public/threads/${id}`);
  if (!res.ok) throw new Error('Failed to fetch public thread');
  return res.json();
}

export async function fetchPublicBots(): Promise<PublicBot[]> {
  const res = await fetch(`${API_BASE}/public/bots`);
  if (!res.ok) throw new Error('Failed to fetch public bots');
  return res.json();
}

export async function fetchPublicActivity(limit = 20): Promise<PublicActivity[]> {
  const res = await fetch(`${API_BASE}/public/activity?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch public activity');
  return res.json();
}

// Memory types
export interface WarmMemory {
  facts_learned: Record<string, unknown>[];
  relationships: Record<string, unknown>[];
  interests: string[];
  opinions: Record<string, unknown>[];
  memories: Record<string, unknown>[];
}

export interface ColdMemorySummary {
  id: number;
  period_start: string;
  period_end: string;
  summary: string;
  facts_compressed: number;
  memories_compressed: number;
  created_at: string;
}

export async function fetchWarmMemory(botId: string): Promise<WarmMemory> {
  const res = await fetch(`${API_BASE}/stats/bots/${botId}/memory/warm`);
  if (!res.ok) throw new Error('Failed to fetch warm memory');
  return res.json();
}

export async function fetchColdMemories(botId: string, limit = 10, offset = 0): Promise<ColdMemorySummary[]> {
  const res = await fetch(`${API_BASE}/stats/bots/${botId}/memory/cold?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error('Failed to fetch cold memories');
  return res.json();
}

// Moderation
export interface ContentFlag {
  id: number;
  target_type: string;
  target_id: number;
  flag_type: string;
  flagged_by: string;
  resolved: boolean;
  created_at: string;
}

export async function pauseBot(botId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/moderation/bots/${botId}/pause`, { method: 'PUT' });
  if (!res.ok) throw new Error('Failed to pause bot');
}

export async function unpauseBot(botId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/moderation/bots/${botId}/unpause`, { method: 'PUT' });
  if (!res.ok) throw new Error('Failed to unpause bot');
}

export async function fetchFlags(resolved = false): Promise<ContentFlag[]> {
  const res = await fetch(`${API_BASE}/moderation/flags?resolved=${resolved}`);
  if (!res.ok) throw new Error('Failed to fetch flags');
  return res.json();
}

export async function fetchFlagCount(): Promise<number> {
  const res = await fetch(`${API_BASE}/moderation/flags/count`);
  if (!res.ok) throw new Error('Failed to fetch flag count');
  const data = await res.json();
  return data.unresolved;
}

export async function resolveFlag(flagId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/moderation/flags/${flagId}/resolve`, { method: 'PUT' });
  if (!res.ok) throw new Error('Failed to resolve flag');
}

export async function deleteThread(threadId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/moderation/threads/${threadId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete thread');
}

export async function deleteReply(replyId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/moderation/replies/${replyId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete reply');
}

// Custom bot creation
export interface CustomBotRequest {
  name: string;
  personality: {
    traits: string[];
    communication_style: string;
    engagement_style: string;
    interests: string[];
    quirks: string[];
    creativity_level: number;
    leadership_tendency: number;
    skepticism: number;
    aggression: number;
    shyness: number;
  };
  model?: {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
  };
}

export async function createCustomBot(request: CustomBotRequest): Promise<Bot> {
  const res = await fetch(`${API_BASE}/bots/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create bot' }));
    throw new Error(err.detail || 'Failed to create bot');
  }
  return res.json();
}
