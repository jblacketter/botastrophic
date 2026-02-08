import { useState } from 'react';
import { triggerHeartbeat, type Bot } from '../api/client';

interface BotListProps {
  bots: Bot[];
  onRefresh: () => void;
  onSelectBot: (botId: string) => void;
  selectedBotId: string | null;
  onCreateBot?: () => void;
}

const BOT_COLORS: Record<string, string> = {
  ada_001: 'bg-pink-600',
  echo_001: 'bg-teal-600',
  luna_001: 'bg-indigo-600',
  marcus_001: 'bg-amber-600',
  rex_001: 'bg-red-600',
  sage_001: 'bg-emerald-600',
};

function BotList({ bots, onRefresh, onSelectBot, selectedBotId, onCreateBot }: BotListProps) {
  const [triggering, setTriggering] = useState<string | null>(null);

  const handleTrigger = async (e: React.MouseEvent, botId: string) => {
    e.stopPropagation();
    try {
      setTriggering(botId);
      await triggerHeartbeat(botId);
      onRefresh();
    } catch {
      console.error('Failed to trigger heartbeat');
    } finally {
      setTriggering(null);
    }
  };

  const getInitials = (name: string) => name.slice(0, 2).toUpperCase();
  const getColor = (id: string) => BOT_COLORS[id] || 'bg-gray-600';

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Bots</h2>
        {onCreateBot && (
          <button
            onClick={onCreateBot}
            className="w-7 h-7 bg-purple-600 hover:bg-purple-700 rounded-full text-sm font-bold flex items-center justify-center"
            title="Create new bot"
          >
            +
          </button>
        )}
      </div>
      <div className="space-y-3">
        {bots.map((bot) => {
          const personality = bot.personality_config?.personality as Record<string, unknown> | undefined;
          const traits = (personality?.traits as string[]) || [];
          const isSelected = selectedBotId === bot.id;
          return (
            <div
              key={bot.id}
              onClick={() => onSelectBot(bot.id)}
              className={`rounded-lg p-3 cursor-pointer transition-colors ${
                isSelected ? 'bg-purple-900/50 ring-1 ring-purple-500' : 'bg-gray-700 hover:bg-gray-650'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-8 h-8 rounded-full ${getColor(bot.id)} flex items-center justify-center text-xs font-bold`}>
                  {getInitials(bot.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <span className="font-medium">{bot.name}</span>
                  {bot.is_paused && (
                    <span className="ml-2 text-xs bg-yellow-700 text-yellow-200 px-1.5 py-0.5 rounded">Paused</span>
                  )}
                  <div className="text-xs text-gray-400">
                    Rep: {bot.reputation_score}
                    {bot.source === 'custom' && <span className="ml-2 text-purple-400">custom</span>}
                  </div>
                </div>
                <button
                  onClick={(e) => handleTrigger(e, bot.id)}
                  disabled={triggering === bot.id}
                  className="text-xs px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
                >
                  {triggering === bot.id ? '...' : 'Heartbeat'}
                </button>
              </div>
              <div className="text-xs text-gray-400 mb-2">
                {(traits as string[]).slice(0, 3).join(', ')}
              </div>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>{bot.follower_count} followers</span>
                <span>{bot.following_count} following</span>
              </div>
            </div>
          );
        })}
        {bots.length === 0 && (
          <p className="text-gray-400 text-sm">No bots loaded</p>
        )}
      </div>
    </div>
  );
}

export default BotList;
