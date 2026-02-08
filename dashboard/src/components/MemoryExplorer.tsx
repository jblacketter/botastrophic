import { useState, useEffect } from 'react';
import { fetchWarmMemory, fetchColdMemories, type WarmMemory, type ColdMemorySummary } from '../api/client';

interface MemoryExplorerProps {
  botId: string;
}

function MemoryExplorer({ botId }: MemoryExplorerProps) {
  const [warm, setWarm] = useState<WarmMemory | null>(null);
  const [cold, setCold] = useState<ColdMemorySummary[]>([]);
  const [tab, setTab] = useState<'facts' | 'relationships' | 'opinions' | 'cold'>('facts');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMemory();
  }, [botId]);

  const loadMemory = async () => {
    setLoading(true);
    try {
      const [warmData, coldData] = await Promise.all([
        fetchWarmMemory(botId),
        fetchColdMemories(botId),
      ]);
      setWarm(warmData);
      setCold(coldData);
    } catch (e) {
      console.error('Failed to load memory:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-gray-400 text-sm py-4">Loading memory...</div>;
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-md font-semibold mb-3">Memory Explorer</h3>

      <div className="flex gap-1 mb-3">
        {(['facts', 'relationships', 'opinions', 'cold'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-2 py-1 text-xs rounded ${
              tab === t ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {t === 'facts' && warm ? ` (${warm.facts_learned.length})` : ''}
            {t === 'relationships' && warm ? ` (${warm.relationships.length})` : ''}
            {t === 'cold' ? ` (${cold.length})` : ''}
          </button>
        ))}
      </div>

      <div className="max-h-64 overflow-y-auto space-y-2">
        {tab === 'facts' && warm?.facts_learned.map((fact, i) => (
          <div key={i} className="text-xs bg-gray-700 rounded p-2">
            <span className="text-gray-300">{(fact as Record<string, string>).fact}</span>
            {(fact as Record<string, string>).source && (
              <span className="text-gray-500 ml-2">({(fact as Record<string, string>).source})</span>
            )}
          </div>
        ))}

        {tab === 'relationships' && warm?.relationships.map((rel, i) => {
          const r = rel as Record<string, unknown>;
          return (
            <div key={i} className="text-xs bg-gray-700 rounded p-2">
              <div className="flex justify-between">
                <span className="text-purple-300 font-medium">{r.bot as string}</span>
                <span className="text-gray-400">{r.sentiment as string}</span>
              </div>
              {(r.interaction_count as number) > 0 && (
                <div className="text-gray-500 mt-1">
                  {r.interaction_count as number} interactions | Last: {r.last_interaction as string}
                </div>
              )}
              {(r.history as Array<Record<string, string>>)?.length > 0 && (
                <div className="mt-1 pl-2 border-l border-gray-600">
                  {(r.history as Array<Record<string, string>>).slice(-3).map((h, j) => (
                    <div key={j} className="text-gray-500">
                      {h.date}: {h.event}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {tab === 'opinions' && warm?.opinions.map((op, i) => {
          const o = op as Record<string, unknown>;
          return (
            <div key={i} className="text-xs bg-gray-700 rounded p-2">
              <span className="text-yellow-300">{o.topic as string}</span>
              <span className="text-gray-400 ml-2">{o.stance as string}</span>
              <span className="text-gray-500 ml-2">(conf: {(o.confidence as number)?.toFixed(1) ?? '?'})</span>
            </div>
          );
        })}

        {tab === 'cold' && cold.map((m) => (
          <div key={m.id} className="text-xs bg-gray-700 rounded p-2">
            <div className="text-gray-400 mb-1">
              {m.period_start} to {m.period_end} | {m.facts_compressed} facts, {m.memories_compressed} memories
            </div>
            <div className="text-gray-300">{m.summary}</div>
          </div>
        ))}

        {tab === 'facts' && (!warm?.facts_learned.length) && (
          <p className="text-gray-500 text-xs text-center py-2">No facts yet</p>
        )}
        {tab === 'relationships' && (!warm?.relationships.length) && (
          <p className="text-gray-500 text-xs text-center py-2">No relationships yet</p>
        )}
        {tab === 'opinions' && (!warm?.opinions.length) && (
          <p className="text-gray-500 text-xs text-center py-2">No opinions yet</p>
        )}
        {tab === 'cold' && cold.length === 0 && (
          <p className="text-gray-500 text-xs text-center py-2">No cold memories yet</p>
        )}
      </div>
    </div>
  );
}

export default MemoryExplorer;
