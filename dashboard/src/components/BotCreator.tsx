import { useState } from 'react';
import { createCustomBot, type CustomBotRequest } from '../api/client';

interface BotCreatorProps {
  onCreated: () => void;
  onClose: () => void;
  botCount: number;
  maxBots: number;
}

function BotCreator({ onCreated, onClose, botCount, maxBots }: BotCreatorProps) {
  const [name, setName] = useState('');
  const [traits, setTraits] = useState<string[]>([]);
  const [traitInput, setTraitInput] = useState('');
  const [interests, setInterests] = useState<string[]>([]);
  const [interestInput, setInterestInput] = useState('');
  const [communicationStyle, setCommunicationStyle] = useState('friendly and direct');
  const [engagementStyle, setEngagementStyle] = useState('active');
  const [creativity, setCreativity] = useState(50);
  const [leadership, setLeadership] = useState(50);
  const [skepticism, setSkepticism] = useState(50);
  const [aggression, setAggression] = useState(20);
  const [shyness, setShyness] = useState(30);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addTag = (
    value: string,
    list: string[],
    setList: (v: string[]) => void,
    setInput: (v: string) => void,
  ) => {
    const trimmed = value.trim();
    if (trimmed && !list.includes(trimmed) && list.length < 10) {
      setList([...list, trimmed]);
    }
    setInput('');
  };

  const removeTag = (tag: string, list: string[], setList: (v: string[]) => void) => {
    setList(list.filter((t) => t !== tag));
  };

  const handleSubmit = async () => {
    if (!name.trim() || name.trim().length < 3) {
      setError('Name must be at least 3 characters');
      return;
    }
    if (traits.length === 0) {
      setError('Add at least one personality trait');
      return;
    }

    const request: CustomBotRequest = {
      name: name.trim(),
      personality: {
        traits,
        communication_style: communicationStyle,
        engagement_style: engagementStyle,
        interests,
        quirks: [],
        creativity_level: creativity,
        leadership_tendency: leadership,
        skepticism,
        aggression,
        shyness,
      },
    };

    try {
      setCreating(true);
      setError(null);
      await createCustomBot(request);
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create bot');
    } finally {
      setCreating(false);
    }
  };

  const atLimit = botCount >= maxBots;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Create Bot</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-sm">
          Cancel
        </button>
      </div>

      <div className="text-xs text-gray-400 mb-4">
        {botCount} / {maxBots} bots
      </div>

      {atLimit ? (
        <p className="text-sm text-red-400">Bot limit reached. Delete a bot or increase MAX_BOT_COUNT.</p>
      ) : (
        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Name (3-30 chars)</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={30}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              placeholder="e.g. Nova"
            />
          </div>

          {/* Traits */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Personality Traits</label>
            <div className="flex flex-wrap gap-1 mb-2">
              {traits.map((t) => (
                <span
                  key={t}
                  onClick={() => removeTag(t, traits, setTraits)}
                  className="bg-purple-700 text-xs px-2 py-0.5 rounded cursor-pointer hover:bg-purple-600"
                >
                  {t} &times;
                </span>
              ))}
            </div>
            <input
              type="text"
              value={traitInput}
              onChange={(e) => setTraitInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTag(traitInput, traits, setTraits, setTraitInput);
                }
              }}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              placeholder="Type + Enter to add"
            />
          </div>

          {/* Interests */}
          <div>
            <label className="block text-xs text-gray-400 mb-1">Interests</label>
            <div className="flex flex-wrap gap-1 mb-2">
              {interests.map((i) => (
                <span
                  key={i}
                  onClick={() => removeTag(i, interests, setInterests)}
                  className="bg-teal-700 text-xs px-2 py-0.5 rounded cursor-pointer hover:bg-teal-600"
                >
                  {i} &times;
                </span>
              ))}
            </div>
            <input
              type="text"
              value={interestInput}
              onChange={(e) => setInterestInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTag(interestInput, interests, setInterests, setInterestInput);
                }
              }}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              placeholder="Type + Enter to add"
            />
          </div>

          {/* Style dropdowns */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Communication</label>
              <select
                value={communicationStyle}
                onChange={(e) => setCommunicationStyle(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-2 text-sm"
              >
                <option value="friendly and direct">Friendly & Direct</option>
                <option value="formal and precise">Formal & Precise</option>
                <option value="casual and humorous">Casual & Humorous</option>
                <option value="philosophical and reflective">Philosophical</option>
                <option value="provocative and bold">Provocative & Bold</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Engagement</label>
              <select
                value={engagementStyle}
                onChange={(e) => setEngagementStyle(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-2 text-sm"
              >
                <option value="active">Active</option>
                <option value="reactive">Reactive</option>
                <option value="observer">Observer</option>
              </select>
            </div>
          </div>

          {/* Personality Sliders */}
          <div className="space-y-3">
            <label className="block text-xs text-gray-400">Personality (0-100)</label>
            {[
              { label: 'Creativity', value: creativity, set: setCreativity },
              { label: 'Leadership', value: leadership, set: setLeadership },
              { label: 'Skepticism', value: skepticism, set: setSkepticism },
              { label: 'Aggression', value: aggression, set: setAggression },
              { label: 'Shyness', value: shyness, set: setShyness },
            ].map(({ label, value, set }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-xs text-gray-300 w-20">{label}</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={value}
                  onChange={(e) => set(Number(e.target.value))}
                  className="flex-1 accent-purple-500"
                />
                <span className="text-xs text-gray-400 w-8 text-right">{value}</span>
              </div>
            ))}
          </div>

          {/* Error */}
          {error && <p className="text-sm text-red-400">{error}</p>}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={creating}
            className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {creating ? 'Creating...' : 'Create Bot'}
          </button>
        </div>
      )}
    </div>
  );
}

export default BotCreator;
