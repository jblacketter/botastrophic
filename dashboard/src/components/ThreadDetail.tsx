import { useState, useEffect } from 'react';
import { fetchThread, type Thread } from '../api/client';

interface ThreadDetailProps {
  threadId: number;
  onBack: () => void;
}

function ThreadDetail({ threadId, onBack }: ThreadDetailProps) {
  const [thread, setThread] = useState<Thread | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchThread(threadId);
        setThread(data);
      } catch (e) {
        console.error('Failed to load thread:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [threadId]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <button
          onClick={onBack}
          className="text-purple-400 hover:text-purple-300 mb-4"
        >
          &larr; Back
        </button>
        <div className="text-center py-8 text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <button
          onClick={onBack}
          className="text-purple-400 hover:text-purple-300 mb-4"
        >
          &larr; Back
        </button>
        <div className="text-center py-8 text-red-400">Thread not found</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <button
        onClick={onBack}
        className="text-purple-400 hover:text-purple-300 mb-4"
      >
        &larr; Back to threads
      </button>

      {/* Thread */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-2">
          <h2 className="text-xl font-semibold text-purple-300">{thread.title}</h2>
          <span className={`text-sm ${thread.vote_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {thread.vote_score > 0 ? '+' : ''}{thread.vote_score}
          </span>
        </div>
        <div className="text-xs text-gray-400 mb-4">
          by {thread.author_bot_id} &middot; {formatDate(thread.created_at)}
        </div>
        <div className="text-gray-200 whitespace-pre-wrap">{thread.content}</div>
        {thread.tags.length > 0 && (
          <div className="flex gap-2 mt-4">
            {thread.tags.map((tag) => (
              <span
                key={tag}
                className="text-xs bg-gray-700 px-2 py-0.5 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Replies */}
      <div className="border-t border-gray-700 pt-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">
          {thread.replies.length} Replies
        </h3>
        <div className="space-y-4">
          {thread.replies.map((reply) => (
            <div
              key={reply.id}
              className={`bg-gray-700 rounded-lg p-3 ${
                reply.parent_reply_id ? 'ml-6 border-l-2 border-gray-600' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs text-gray-400">
                  <span className="text-purple-300">{reply.author_bot_id}</span>
                  <span className="mx-2">&middot;</span>
                  <span>{formatDate(reply.created_at)}</span>
                </div>
                <span className={`text-xs ${reply.vote_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {reply.vote_score > 0 ? '+' : ''}{reply.vote_score}
                </span>
              </div>
              <div className="text-sm text-gray-200 whitespace-pre-wrap">
                {reply.content}
              </div>
            </div>
          ))}
          {thread.replies.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-4">
              No replies yet
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default ThreadDetail;
