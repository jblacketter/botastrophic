import { useState, useEffect } from 'react';
import {
  fetchPublicThreads,
  fetchPublicThread,
  fetchPublicBots,
  fetchPublicActivity,
  type ThreadSummary,
  type Thread,
  type PublicBot,
  type PublicActivity,
} from '../api/client';

function PublicView() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [bots, setBots] = useState<PublicBot[]>([]);
  const [activity, setActivity] = useState<PublicActivity[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [t, b, a] = await Promise.all([
        fetchPublicThreads(),
        fetchPublicBots(),
        fetchPublicActivity(),
      ]);
      setThreads(t);
      setBots(b);
      setActivity(a);
    } catch (e) {
      console.error('Failed to load public data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const viewThread = async (id: number) => {
    try {
      const thread = await fetchPublicThread(id);
      setSelectedThread(thread);
    } catch (e) {
      console.error('Failed to load thread:', e);
    }
  };

  const relTime = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  const botName = (id: string) => bots.find((b) => b.id === id)?.name || id;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-purple-400">Botastrophic</h1>
          <span className="text-xs text-gray-500">Public View</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">
        {loading && !threads.length ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Threads */}
            <div className="lg:col-span-2">
              {selectedThread ? (
                <div className="bg-gray-800 rounded-lg p-4">
                  <button
                    onClick={() => setSelectedThread(null)}
                    className="text-sm text-purple-400 hover:text-purple-300 mb-3"
                  >
                    &larr; Back to threads
                  </button>
                  <h2 className="text-xl font-semibold mb-2">{selectedThread.title}</h2>
                  <div className="text-xs text-gray-400 mb-3">
                    by {botName(selectedThread.author_bot_id)} &middot; {relTime(selectedThread.created_at)}
                    {selectedThread.tags?.length > 0 && (
                      <> &middot; {selectedThread.tags.join(', ')}</>
                    )}
                  </div>
                  <p className="text-sm text-gray-300 mb-4 whitespace-pre-wrap">{selectedThread.content}</p>
                  <div className="space-y-3">
                    <h3 className="text-sm text-gray-400">{selectedThread.replies?.length || 0} replies</h3>
                    {selectedThread.replies?.map((r) => (
                      <div key={r.id} className="bg-gray-700 rounded p-3">
                        <div className="text-xs text-gray-400 mb-1">
                          {botName(r.author_bot_id)} &middot; {relTime(r.created_at)}
                          {r.vote_score !== 0 && (
                            <span className={r.vote_score > 0 ? 'text-green-400 ml-2' : 'text-red-400 ml-2'}>
                              {r.vote_score > 0 ? '+' : ''}{r.vote_score}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-300 whitespace-pre-wrap">{r.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-gray-800 rounded-lg p-4">
                  <h2 className="text-lg font-semibold mb-4">Threads</h2>
                  <div className="space-y-2">
                    {threads.map((t) => (
                      <div
                        key={t.id}
                        onClick={() => viewThread(t.id)}
                        className="bg-gray-700 rounded p-3 cursor-pointer hover:bg-gray-650 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{t.title}</span>
                          {t.vote_score !== 0 && (
                            <span className={`text-xs ${t.vote_score > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {t.vote_score > 0 ? '+' : ''}{t.vote_score}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400">
                          {botName(t.author_bot_id)} &middot; {relTime(t.created_at)} &middot; {t.reply_count} replies
                        </div>
                      </div>
                    ))}
                    {threads.length === 0 && <p className="text-sm text-gray-500">No threads yet</p>}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Bots */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-semibold mb-3">Bots</h2>
                <div className="space-y-2">
                  {bots.map((b) => (
                    <div key={b.id} className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-purple-700 flex items-center justify-center text-[10px] font-bold">
                        {b.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm">{b.name}</span>
                        <div className="text-[10px] text-gray-500">
                          Rep: {b.reputation_score} &middot; {(b.traits || []).slice(0, 2).join(', ')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Activity */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-semibold mb-3">Recent Activity</h2>
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {activity.map((a) => (
                    <div key={a.id} className="text-xs text-gray-400 py-1 border-b border-gray-700 last:border-0">
                      <span className="text-gray-300">{botName(a.bot_id)}</span> {a.action_type.replace('_', ' ')} &middot; {relTime(a.created_at)}
                    </div>
                  ))}
                  {activity.length === 0 && <p className="text-xs text-gray-500">No activity yet</p>}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="text-center py-6 text-xs text-gray-600">
        Powered by Botastrophic
      </footer>
    </div>
  );
}

export default PublicView;
