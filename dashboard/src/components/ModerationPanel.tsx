import { useState, useEffect } from 'react';
import {
  fetchFlags,
  fetchFlagCount,
  resolveFlag,
  pauseBot,
  unpauseBot,
  type ContentFlag,
  type Bot,
} from '../api/client';

interface ModerationPanelProps {
  bots: Bot[];
  onRefresh: () => void;
}

const FLAG_COLORS: Record<string, string> = {
  repetitive: 'bg-yellow-700 text-yellow-200',
  low_quality: 'bg-orange-700 text-orange-200',
  frequency: 'bg-red-700 text-red-200',
  off_topic: 'bg-blue-700 text-blue-200',
  toxic: 'bg-red-800 text-red-200',
};

function ModerationPanel({ bots, onRefresh }: ModerationPanelProps) {
  const [flags, setFlags] = useState<ContentFlag[]>([]);
  const [flagCount, setFlagCount] = useState(0);
  const [showResolved, setShowResolved] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadFlags = async () => {
    try {
      setLoading(true);
      const [flagData, count] = await Promise.all([
        fetchFlags(showResolved),
        fetchFlagCount(),
      ]);
      setFlags(flagData);
      setFlagCount(count);
    } catch (e) {
      console.error('Failed to load flags:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFlags();
  }, [showResolved]);

  const handleResolve = async (flagId: number) => {
    try {
      await resolveFlag(flagId);
      loadFlags();
    } catch (e) {
      console.error('Failed to resolve flag:', e);
    }
  };

  const handleTogglePause = async (bot: Bot) => {
    try {
      if (bot.is_paused) {
        await unpauseBot(bot.id);
      } else {
        await pauseBot(bot.id);
      }
      onRefresh();
    } catch (e) {
      console.error('Failed to toggle pause:', e);
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

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          Moderation
          {flagCount > 0 && (
            <span className="ml-2 bg-red-600 text-xs px-2 py-0.5 rounded-full">{flagCount}</span>
          )}
        </h2>
      </div>

      {/* Bot pause controls */}
      <div className="mb-4">
        <h3 className="text-sm text-gray-400 mb-2">Bot Controls</h3>
        <div className="space-y-1">
          {bots.map((bot) => (
            <div key={bot.id} className="flex items-center justify-between text-sm py-1">
              <span className={bot.is_paused ? 'text-yellow-400' : 'text-gray-300'}>{bot.name}</span>
              <button
                onClick={() => handleTogglePause(bot)}
                className={`text-xs px-2 py-1 rounded ${
                  bot.is_paused
                    ? 'bg-green-700 hover:bg-green-600 text-green-200'
                    : 'bg-yellow-700 hover:bg-yellow-600 text-yellow-200'
                }`}
              >
                {bot.is_paused ? 'Unpause' : 'Pause'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Flags */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm text-gray-400">Flags</h3>
          <button
            onClick={() => setShowResolved(!showResolved)}
            className="text-xs text-purple-400 hover:text-purple-300"
          >
            {showResolved ? 'Show Unresolved' : 'Show Resolved'}
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : flags.length === 0 ? (
          <p className="text-sm text-gray-500">
            {showResolved ? 'No resolved flags' : 'No flags'}
          </p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {flags.map((flag) => (
              <div key={flag.id} className="bg-gray-700 rounded p-2 text-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${FLAG_COLORS[flag.flag_type] || 'bg-gray-600'}`}>
                    {flag.flag_type}
                  </span>
                  <span className="text-xs text-gray-500">{relTime(flag.created_at)}</span>
                </div>
                <div className="text-xs text-gray-400">
                  {flag.target_type} #{flag.target_id} &middot; by {flag.flagged_by}
                </div>
                {!flag.resolved && (
                  <button
                    onClick={() => handleResolve(flag.id)}
                    className="mt-1 text-xs text-green-400 hover:text-green-300"
                  >
                    Resolve
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ModerationPanel;
