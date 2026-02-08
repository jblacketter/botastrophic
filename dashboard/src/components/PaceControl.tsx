import { useState, useEffect } from 'react';
import { getPace, setPace } from '../api/client';

const PACE_OPTIONS = ['slow', 'normal', 'fast', 'turbo'];

function PaceControl() {
  const [currentPace, setCurrentPace] = useState('slow');
  const [changing, setChanging] = useState(false);

  useEffect(() => {
    getPace()
      .then((data) => setCurrentPace(data.preset))
      .catch(() => console.error('Failed to get pace'));
  }, []);

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newPace = e.target.value;
    try {
      setChanging(true);
      await setPace(newPace);
      setCurrentPace(newPace);
    } catch {
      console.error('Failed to set pace');
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-gray-400">Pace:</label>
      <select
        value={currentPace}
        onChange={handleChange}
        disabled={changing}
        className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm disabled:opacity-50"
      >
        {PACE_OPTIONS.map((pace) => (
          <option key={pace} value={pace}>
            {pace}
          </option>
        ))}
      </select>
    </div>
  );
}

export default PaceControl;
