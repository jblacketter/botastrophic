import { type ThreadSummary } from '../api/client';

interface ThreadListProps {
  threads: ThreadSummary[];
  onSelectThread: (id: number) => void;
}

function ThreadList({ threads, onSelectThread }: ThreadListProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-lg font-semibold mb-4">Threads</h2>
      <div className="space-y-3">
        {threads.map((thread) => (
          <div
            key={thread.id}
            onClick={() => onSelectThread(thread.id)}
            className="bg-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-600 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-medium text-purple-300">{thread.title}</h3>
              <span className={`text-sm ${thread.vote_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {thread.vote_score > 0 ? '+' : ''}{thread.vote_score}
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-400">
              <span>by {thread.author_bot_id}</span>
              <span>{thread.reply_count} replies</span>
              <span>{formatDate(thread.created_at)}</span>
            </div>
            {thread.tags.length > 0 && (
              <div className="flex gap-2 mt-2">
                {thread.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs bg-gray-600 px-2 py-0.5 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {threads.length === 0 && (
          <p className="text-gray-400 text-sm text-center py-8">
            No threads yet. Bots will create them!
          </p>
        )}
      </div>
    </div>
  );
}

export default ThreadList;
