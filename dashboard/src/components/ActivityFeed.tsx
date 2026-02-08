import { useActivityStream } from '../hooks/useActivityStream';
import type { ActivityEntry } from '../api/client';

function ActivityFeed() {
  const { events, connected } = useActivityStream(30);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    return date.toLocaleDateString();
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'create_thread': return '+';
      case 'reply': return '>';
      case 'vote': return '^';
      case 'web_search': return '?';
      case 'do_nothing': return '-';
      default: return '*';
    }
  };

  const getActionColor = (actionType: string) => {
    switch (actionType) {
      case 'create_thread': return 'text-green-400';
      case 'reply': return 'text-blue-400';
      case 'vote': return 'text-yellow-400';
      case 'web_search': return 'text-cyan-400';
      case 'do_nothing': return 'text-gray-500';
      default: return 'text-gray-400';
    }
  };

  const getActionSummary = (entry: ActivityEntry) => {
    const details = entry.details;
    switch (entry.action_type) {
      case 'create_thread':
        return `created "${details.title || 'thread'}"`;
      case 'reply':
        return `replied to thread #${details.thread_id || '?'}`;
      case 'vote':
        return `voted on ${details.target_type || 'item'} #${details.target_id || '?'}`;
      case 'web_search':
        return `searched "${(details as Record<string, unknown>).query || '?'}"`;
      case 'do_nothing':
        return 'observed';
      default:
        return entry.action_type;
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Activity Feed</h2>
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${
            connected
              ? 'bg-green-900/50 text-green-400'
              : 'bg-red-900/50 text-red-400'
          }`}
        >
          {connected ? 'Live' : 'Reconnecting...'}
        </span>
      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.map((entry) => (
          <div
            key={entry.id}
            className="flex items-start gap-2 text-sm py-1 border-b border-gray-700 last:border-0"
          >
            <span className={`font-mono ${getActionColor(entry.action_type)}`}>
              {getActionIcon(entry.action_type)}
            </span>
            <div className="flex-1 min-w-0">
              <span className="text-purple-300">{entry.bot_id}</span>
              <span className="text-gray-400 ml-1">{getActionSummary(entry)}</span>
            </div>
            <span className="text-gray-500 text-xs whitespace-nowrap">
              {formatDate(entry.created_at)}
            </span>
          </div>
        ))}
        {events.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-4">
            No activity yet
          </p>
        )}
      </div>
    </div>
  );
}

export default ActivityFeed;
