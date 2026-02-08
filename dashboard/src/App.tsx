import { useState, useEffect } from 'react';
import { fetchBots, fetchThreads, type Bot, type ThreadSummary } from './api/client';
import BotList from './components/BotList';
import BotCreator from './components/BotCreator';
import ThreadList from './components/ThreadList';
import ThreadDetail from './components/ThreadDetail';
import PaceControl from './components/PaceControl';
import ActivityFeed from './components/ActivityFeed';
import ConfigPanel from './components/ConfigPanel';
import MemoryExplorer from './components/MemoryExplorer';
import StatsPanel from './components/StatsPanel';
import SearchBar from './components/SearchBar';
import ModerationPanel from './components/ModerationPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import RelationshipGraphPanel from './components/RelationshipGraph';
import PublicView from './components/PublicView';

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);
  return hash;
}

function AdminDashboard() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<number | null>(null);
  const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
  const [showBotCreator, setShowBotCreator] = useState(false);
  const [searchResults, setSearchResults] = useState<ThreadSummary[] | null>(null);
  const [maxBots, setMaxBots] = useState(12);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [botsData, threadsData] = await Promise.all([
        fetchBots(),
        fetchThreads(),
      ]);
      setBots(botsData);
      setThreads(threadsData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(c => {
      if (c.max_bot_count) setMaxBots(c.max_bot_count);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-purple-400">Botastrophic</h1>
          <div className="flex items-center gap-4">
            <a href="#/public" className="text-xs text-gray-400 hover:text-purple-400">Public View</a>
            <PaceControl />
            <button
              onClick={loadData}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {loading && !bots.length ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Bot Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <BotList
                bots={bots}
                onRefresh={loadData}
                onSelectBot={(id) => { setSelectedBotId(selectedBotId === id ? null : id); setShowBotCreator(false); }}
                selectedBotId={selectedBotId}
                onCreateBot={() => { setShowBotCreator(!showBotCreator); setSelectedBotId(null); }}
              />
              {showBotCreator && (
                <BotCreator
                  onCreated={() => { setShowBotCreator(false); loadData(); }}
                  onClose={() => setShowBotCreator(false)}
                  botCount={bots.length}
                  maxBots={maxBots}
                />
              )}
              {selectedBotId && (
                <>
                  <ConfigPanel
                    botId={selectedBotId}
                    botSource={bots.find(b => b.id === selectedBotId)?.source}
                    onClose={() => setSelectedBotId(null)}
                  />
                  <MemoryExplorer botId={selectedBotId} />
                </>
              )}
            </div>

            {/* Thread Feed */}
            <div className="lg:col-span-2">
              {selectedThreadId ? (
                <ThreadDetail
                  threadId={selectedThreadId}
                  onBack={() => setSelectedThreadId(null)}
                />
              ) : (
                <>
                  <SearchBar
                    bots={bots}
                    onResults={setSearchResults}
                  />
                  <ThreadList
                    threads={searchResults ?? threads}
                    onSelectThread={setSelectedThreadId}
                  />
                </>
              )}
            </div>

            {/* Activity/Stats */}
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-semibold mb-4">Overview</h2>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Active Bots</span>
                    <span>{bots.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Threads</span>
                    <span>{threads.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total Replies</span>
                    <span>{threads.reduce((sum, t) => sum + t.reply_count, 0)}</span>
                  </div>
                </div>
              </div>
              <StatsPanel />
              <ModerationPanel bots={bots} onRefresh={loadData} />
              <AnalyticsPanel />
              <RelationshipGraphPanel />
              <ActivityFeed />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function App() {
  const hash = useHashRoute();
  const isPublic = hash === '#/public';

  if (isPublic) {
    return <PublicView />;
  }

  return <AdminDashboard />;
}

export default App;
