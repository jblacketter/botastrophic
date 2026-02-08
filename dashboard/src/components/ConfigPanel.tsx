import { useState, useEffect } from 'react';
import {
  fetchBotConfig,
  updateBotConfig,
  updateCostCap,
  resetCostCap,
  type BotConfig,
} from '../api/client';

interface ConfigPanelProps {
  botId: string;
  botSource?: string;
  onClose: () => void;
}

function ConfigPanel({ botId, botSource, onClose }: ConfigPanelProps) {
  const [config, setConfig] = useState<BotConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<'personality' | 'model' | 'costs'>('personality');
  const [message, setMessage] = useState<string | null>(null);

  // Editable state
  const [traits, setTraits] = useState<string[]>([]);
  const [style, setStyle] = useState('');
  const [interests, setInterests] = useState('');
  const [creativity, setCreativity] = useState(50);
  const [leadership, setLeadership] = useState(50);
  const [skepticism, setSkepticism] = useState(50);
  const [aggression, setAggression] = useState(15);
  const [shyness, setShyness] = useState(20);
  const [engagement, setEngagement] = useState('active');
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-sonnet-4-5-20250929');
  const [temperature, setTemperature] = useState(0.8);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [tokenCap, setTokenCap] = useState(100000);
  const [costCap, setCostCap] = useState(1.0);
  const [isCustomTokenCap, setIsCustomTokenCap] = useState(false);
  const [isCustomCostCap, setIsCustomCostCap] = useState(false);

  useEffect(() => {
    loadConfig();
  }, [botId]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await fetchBotConfig(botId);
      setConfig(data);

      const pc = data.personality_config;
      const p = (pc.personality || {}) as Record<string, unknown>;
      const b = (pc.behavior || {}) as Record<string, unknown>;
      const m = (pc.model || {}) as Record<string, unknown>;

      setTraits((p.traits as string[]) || []);
      setStyle((p.communication_style as string) || '');
      setInterests(((p.interests as string[]) || []).join(', '));
      // Read creativity_level as numeric; legacy YAML bots may store strings
      const rawCreativity = b.creativity_level;
      if (typeof rawCreativity === 'number') {
        setCreativity(rawCreativity);
      } else if (typeof rawCreativity === 'string') {
        setCreativity(parseLevel(rawCreativity));
      } else {
        setCreativity(50);
      }
      setLeadership((b.leadership_tendency as number) || 50);
      setSkepticism((b.skepticism as number) || 50);
      setAggression((b.aggression as number) || 15);
      setShyness((b.shyness as number) || 20);
      setEngagement((b.engagement_style as string) || 'active');
      setProvider((m.provider as string) || 'anthropic');
      setModel((m.model as string) || 'claude-sonnet-4-5-20250929');
      setTemperature((m.temperature as number) || 0.8);
      setMaxTokens((m.max_tokens as number) || 1000);

      setTokenCap(data.cost_caps.daily_token_cap);
      setCostCap(data.cost_caps.daily_cost_cap_usd);
      setIsCustomTokenCap(data.cost_caps.is_custom_token_cap);
      setIsCustomCostCap(data.cost_caps.is_custom_cost_cap);
    } catch {
      setMessage('Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  const parseLevel = (level: string): number => {
    switch (level) {
      case 'high': return 80;
      case 'medium': return 50;
      case 'low': return 20;
      default: return 50;
    }
  };

  const savePersonality = async () => {
    setSaving(true);
    try {
      await updateBotConfig(botId, {
        personality: {
          traits,
          communication_style: style,
          interests: interests.split(',').map(s => s.trim()).filter(Boolean),
        },
        behavior: {
          creativity_level: creativity,
          leadership_tendency: leadership,
          skepticism,
          aggression,
          shyness,
          engagement_style: engagement,
        },
      });
      setMessage('Personality saved');
      setTimeout(() => setMessage(null), 2000);
    } catch {
      setMessage('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const saveModel = async () => {
    setSaving(true);
    try {
      await updateBotConfig(botId, {
        model: { provider, model, temperature, max_tokens: maxTokens },
      });
      setMessage('Model config saved');
      setTimeout(() => setMessage(null), 2000);
    } catch {
      setMessage('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const saveCostCaps = async () => {
    setSaving(true);
    try {
      await updateCostCap(botId, {
        daily_token_cap: tokenCap,
        daily_cost_cap_usd: costCap,
      });
      setIsCustomTokenCap(true);
      setIsCustomCostCap(true);
      setMessage('Cost caps saved');
      setTimeout(() => setMessage(null), 2000);
    } catch {
      setMessage('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleResetCaps = async () => {
    setSaving(true);
    try {
      await resetCostCap(botId);
      setTokenCap(100000);
      setCostCap(1.0);
      setIsCustomTokenCap(false);
      setIsCustomCostCap(false);
      setMessage('Reset to defaults');
      setTimeout(() => setMessage(null), 2000);
    } catch {
      setMessage('Failed to reset');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm">Loading config...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">
          Configure: {config?.bot_name}
        </h2>
        <button onClick={onClose} className="text-gray-400 hover:text-white text-sm">
          Close
        </button>
      </div>

      {botSource === 'yaml' && (
        <div className="text-xs text-yellow-400 mb-3 bg-yellow-900/30 rounded px-3 py-1">
          YAML bot — edits reset on restart unless YAML is updated.
        </div>
      )}

      {message && (
        <div className="text-sm text-green-400 mb-3 bg-green-900/30 rounded px-3 py-1">
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4">
        {(['personality', 'model', 'costs'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1 text-sm rounded ${
              tab === t ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Personality Tab */}
      {tab === 'personality' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Traits (comma-separated)</label>
            <input
              value={traits.join(', ')}
              onChange={(e) => setTraits(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Communication Style</label>
            <input
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Interests (comma-separated)</label>
            <input
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Engagement Style</label>
            <select
              value={engagement}
              onChange={(e) => setEngagement(e.target.value)}
              className="bg-gray-700 rounded px-3 py-1.5 text-sm"
            >
              <option value="active">Active</option>
              <option value="reactive">Reactive</option>
              <option value="observer">Observer</option>
            </select>
          </div>

          {/* Sliders */}
          {[
            { label: 'Creativity', value: creativity, set: setCreativity },
            { label: 'Leadership', value: leadership, set: setLeadership },
            { label: 'Skepticism', value: skepticism, set: setSkepticism },
            { label: 'Aggression', value: aggression, set: setAggression },
            { label: 'Shyness', value: shyness, set: setShyness },
          ].map(({ label, value, set }) => (
            <div key={label}>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>{label}</span>
                <span>{value}</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={value}
                onChange={(e) => set(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
          ))}

          <button
            onClick={savePersonality}
            disabled={saving}
            className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Personality'}
          </button>
        </div>
      )}

      {/* Model Tab */}
      {tab === 'model' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="bg-gray-700 rounded px-3 py-1.5 text-sm"
            >
              <option value="anthropic">Anthropic</option>
              <option value="ollama">Ollama</option>
              <option value="mock">Mock</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Model</label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Temperature</span>
              <span>{temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full accent-purple-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Max Tokens</label>
            <input
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
              min="100"
              max="4000"
            />
          </div>
          <button
            onClick={saveModel}
            disabled={saving}
            className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Model Config'}
          </button>
        </div>
      )}

      {/* Costs Tab */}
      {tab === 'costs' && (
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Daily Token Cap</span>
              <span className={isCustomTokenCap ? 'text-yellow-400' : ''}>
                {isCustomTokenCap ? 'Custom' : 'Default (global)'}
              </span>
            </div>
            <input
              type="number"
              value={tokenCap}
              onChange={(e) => setTokenCap(Number(e.target.value))}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
              min="1000"
              step="10000"
            />
          </div>
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Daily Cost Cap (USD)</span>
              <span className={isCustomCostCap ? 'text-yellow-400' : ''}>
                {isCustomCostCap ? 'Custom' : 'Default (global)'}
              </span>
            </div>
            <input
              type="number"
              value={costCap}
              onChange={(e) => setCostCap(Number(e.target.value))}
              className="w-full bg-gray-700 rounded px-3 py-1.5 text-sm"
              min="0.01"
              step="0.10"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={saveCostCaps}
              disabled={saving}
              className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Caps'}
            </button>
            <button
              onClick={handleResetCaps}
              disabled={saving}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm disabled:opacity-50"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ConfigPanel;
