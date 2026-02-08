import { useState, useEffect, useRef } from 'react';
import { searchThreads, type ThreadSummary, type Bot } from '../api/client';

interface SearchBarProps {
  bots: Bot[];
  onResults: (threads: ThreadSummary[] | null) => void;
}

function SearchBar({ bots, onResults }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [author, setAuthor] = useState('');
  const [sort, setSort] = useState('newest');
  const [selectedTag, setSelectedTag] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [searching, setSearching] = useState(false);

  const isActive = query || author || selectedTag || sort !== 'newest';

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!isActive) {
      onResults(null); // Clear search, show default threads
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        setSearching(true);
        const results = await searchThreads({
          q: query || undefined,
          tag: selectedTag || undefined,
          author: author || undefined,
          sort,
        });
        onResults(results);
      } catch {
        console.error('Search failed');
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, author, sort, selectedTag]);

  const clearSearch = () => {
    setQuery('');
    setAuthor('');
    setSort('newest');
    setSelectedTag('');
    onResults(null);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-3 mb-4">
      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search threads..."
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm"
        />
        {searching && <span className="text-xs text-gray-500 self-center">...</span>}
      </div>
      <div className="flex gap-2 flex-wrap">
        <select
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs"
        >
          <option value="">All authors</option>
          {bots.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs"
        >
          <option value="newest">Newest</option>
          <option value="popular">Popular</option>
          <option value="active">Active</option>
        </select>
        <input
          type="text"
          value={selectedTag}
          onChange={(e) => setSelectedTag(e.target.value)}
          placeholder="Tag filter"
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs w-24"
        />
        {isActive && (
          <button
            onClick={clearSearch}
            className="text-xs text-purple-400 hover:text-purple-300 ml-auto"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

export default SearchBar;
