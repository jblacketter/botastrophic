import { useState, useEffect } from 'react';
import { fetchAnalytics, exportUrl, type Analytics } from '../api/client';

function AnalyticsPanel() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchAnalytics(period);
        setAnalytics(data);
      } catch (e) {
        console.error('Failed to load analytics:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [period]);

  if (loading && !analytics) return <div className="bg-gray-800 rounded-lg p-4 text-gray-400 text-sm">Loading analytics...</div>;
  if (!analytics) return null;

  const maxPosts = Math.max(...analytics.posts_per_day.map((d) => d.threads + d.replies), 1);
  const maxEngagement = Math.max(
    ...analytics.engagement_by_bot.map((e) => e.threads + e.replies + e.votes),
    1,
  );

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Analytics</h2>
        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs"
        >
          <option value={7}>7 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </select>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        {[
          { label: 'Threads', value: analytics.total_threads },
          { label: 'Replies', value: analytics.total_replies },
          { label: 'Votes', value: analytics.total_votes },
          { label: 'Avg Replies', value: analytics.avg_replies_per_thread },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-700 rounded p-2 text-center">
            <div className="text-lg font-bold text-purple-400">{value}</div>
            <div className="text-xs text-gray-400">{label}</div>
          </div>
        ))}
      </div>

      {/* Posts per day chart */}
      {analytics.posts_per_day.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm text-gray-400 mb-2">Posts / Day</h3>
          <div className="flex items-end gap-px h-24">
            {analytics.posts_per_day.slice(-14).map((d) => {
              const total = d.threads + d.replies;
              const pct = (total / maxPosts) * 100;
              const threadPct = (d.threads / maxPosts) * 100;
              return (
                <div key={d.date} className="flex-1 flex flex-col justify-end" title={`${d.date}: ${d.threads}t, ${d.replies}r`}>
                  <div
                    className="bg-teal-600 rounded-t-sm"
                    style={{ height: `${pct - threadPct}%`, minHeight: total > 0 ? 2 : 0 }}
                  />
                  <div
                    className="bg-purple-600 rounded-t-sm"
                    style={{ height: `${threadPct}%`, minHeight: d.threads > 0 ? 2 : 0 }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] text-gray-500 mt-1">
            <span>{analytics.posts_per_day[Math.max(0, analytics.posts_per_day.length - 14)]?.date.slice(5)}</span>
            <span>{analytics.posts_per_day[analytics.posts_per_day.length - 1]?.date.slice(5)}</span>
          </div>
        </div>
      )}

      {/* Engagement by bot */}
      {analytics.engagement_by_bot.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm text-gray-400 mb-2">Engagement by Bot</h3>
          <div className="space-y-1">
            {analytics.engagement_by_bot.map((e) => {
              const total = e.threads + e.replies + e.votes;
              const pct = (total / maxEngagement) * 100;
              return (
                <div key={e.bot_id} className="flex items-center gap-2 text-xs">
                  <span className="w-16 text-gray-300 truncate">{e.bot_name}</span>
                  <div className="flex-1 bg-gray-700 rounded-full h-3 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-600 to-teal-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-gray-500 w-8 text-right">{total}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Export buttons */}
      <div>
        <h3 className="text-sm text-gray-400 mb-2">Export</h3>
        <div className="flex flex-wrap gap-2">
          {(['threads', 'activity', 'bots'] as const).map((type) => (
            <div key={type} className="flex gap-1">
              <span className="text-xs text-gray-400 self-center capitalize">{type}:</span>
              <a
                href={exportUrl(type, 'json')}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                JSON
              </a>
              <a
                href={exportUrl(type, 'csv')}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
              >
                CSV
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AnalyticsPanel;
