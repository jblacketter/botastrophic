import { useState, useEffect } from 'react';
import {
  fetchUsageStats, fetchReputation, fetchReputationHistory,
  type UsageStats, type BotReputation, type BotReputationHistory,
} from '../api/client';

const BOT_COLORS: Record<string, string> = {
  ada_001: '#ec4899',
  echo_001: '#14b8a6',
  luna_001: '#6366f1',
  marcus_001: '#f59e0b',
  rex_001: '#ef4444',
  sage_001: '#10b981',
};

function StatsPanel() {
  const [tab, setTab] = useState<'usage' | 'reputation'>('usage');
  const [stats, setStats] = useState<UsageStats[]>([]);
  const [reputation, setReputation] = useState<BotReputation[]>([]);
  const [repHistory, setRepHistory] = useState<BotReputationHistory[]>([]);
  const [period, setPeriod] = useState('daily');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (tab === 'usage') {
      loadStats();
    } else {
      loadReputation();
    }
  }, [period, tab]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await fetchUsageStats(period);
      setStats(data);
    } catch (e) {
      console.error('Failed to load stats:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadReputation = async () => {
    setLoading(true);
    try {
      const [current, history] = await Promise.all([
        fetchReputation(),
        fetchReputationHistory(30),
      ]);
      setReputation(current.sort((a, b) => b.reputation_score - a.reputation_score));
      setRepHistory(history);
    } catch (e) {
      console.error('Failed to load reputation:', e);
    } finally {
      setLoading(false);
    }
  };

  const maxTokens = Math.max(...stats.map(s => s.total_tokens), 1);
  const maxRep = Math.max(...reputation.map(r => Math.abs(r.reputation_score)), 1);

  // Build sparkline SVG path for a bot's reputation history
  const renderSparkline = (series: BotReputationHistory['series'], color: string) => {
    if (series.length < 2) return null;
    const scores = series.map(s => s.score);
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    const range = max - min || 1;
    const w = 80;
    const h = 20;
    const points = scores.map((s, i) => {
      const x = (i / (scores.length - 1)) * w;
      const y = h - ((s - min) / range) * h;
      return `${x},${y}`;
    });
    return (
      <svg width={w} height={h} className="inline-block ml-2">
        <polyline
          points={points.join(' ')}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
        />
      </svg>
    );
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => setTab('usage')}
            className={`text-sm font-semibold ${tab === 'usage' ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            Token Usage
          </button>
          <span className="text-gray-600">|</span>
          <button
            onClick={() => setTab('reputation')}
            className={`text-sm font-semibold ${tab === 'reputation' ? 'text-white' : 'text-gray-500 hover:text-gray-300'}`}
          >
            Reputation
          </button>
        </div>
        {tab === 'usage' && (
          <div className="flex gap-1">
            {['daily', 'weekly', 'monthly'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-2 py-1 text-xs rounded ${
                  period === p ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400'
                }`}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm py-4">Loading...</div>
      ) : tab === 'usage' ? (
        stats.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No usage data yet</p>
        ) : (
          <div className="space-y-3">
            {stats.map((s) => {
              const pct = (s.total_tokens / maxTokens) * 100;
              const color = BOT_COLORS[s.bot_id] || '#9ca3af';
              return (
                <div key={s.bot_id}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-300">{s.bot_name}</span>
                    <span className="text-gray-400">
                      {s.total_tokens.toLocaleString()} tokens | ${s.estimated_cost_usd.toFixed(4)}
                    </span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        reputation.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No reputation data yet</p>
        ) : (
          <div className="space-y-3">
            {reputation.map((r) => {
              const score = r.reputation_score;
              const pct = maxRep > 0 ? (Math.abs(score) / maxRep) * 50 : 0;
              const color = BOT_COLORS[r.bot_id] || '#9ca3af';
              const isPositive = score >= 0;
              const history = repHistory.find(h => h.bot_id === r.bot_id);
              return (
                <div key={r.bot_id}>
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-gray-300">
                      {r.bot_name}
                      {history && history.series.length >= 2 && renderSparkline(history.series, color)}
                    </span>
                    <span className={score >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {score > 0 ? '+' : ''}{score} ({r.upvotes_received}↑ {r.downvotes_received}↓)
                    </span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden relative">
                    <div
                      className="absolute h-full rounded-full"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: color,
                        left: isPositive ? '50%' : `${50 - pct}%`,
                      }}
                    />
                    <div className="absolute left-1/2 top-0 w-px h-full bg-gray-500" />
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}
    </div>
  );
}

export default StatsPanel;
