import { useState, useEffect } from 'react';
import { fetchWindData } from './api';
import WindChart from './components/WindChart';
import MetricsCard from './components/MetricsCard';

function App() {
  const [date, setDate] = useState('2026-01-15');
  const [data, setData] = useState([]);
  const [metrics, setMetrics] = useState(null);
  // Start loaded==true so the first fetch shows a spinner without a sync setState in the effect.
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Re-fetch when the date changes. The effect body's synchronous part contains
  // NO setState (the first statement is an await), satisfying react-hooks/set-state-in-effect.
  useEffect(() => {
    let cancelled = false;

    async function run() {
      try {
        const res = await fetchWindData(date);   // suspend here first -> later setStates are async
        if (cancelled) return;                   // date changed mid-flight: drop this response
        setData(res.data);
        setMetrics(res.metrics);
        setError('');
      } catch {
        if (cancelled) return;
        setError('Failed to fetch data. Is the backend running on port 8000?');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => { cancelled = true; };          // cleanup on date change / unmount
  }, [date]);

  // Event handler -> free to set state synchronously, no lint rule applies.
  function handleDateChange(e) {
    const next = e.target.value;
    setDate(next);
    setLoading(true);
    setError('');
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">UK Wind Power Analytics</h1>
        <p className="text-gray-600">Elexon FUELHH & WINDFOR Analysis (Jan 2026)</p>
      </header>

      <div className="mb-6 flex items-center gap-4">
        <label htmlFor="date-picker" className="font-medium text-gray-700">Select Date:</label>
        <input
          id="date-picker"
          type="date"
          value={date}
          min="2026-01-01"
          max="2026-01-31"
          onChange={handleDateChange}
          className="border rounded p-2 focus:ring-2 focus:ring-blue-500 outline-none"
        />
      </div>

      {loading && <div role="status" className="text-center py-10 text-blue-600">Loading data…</div>}
      {!loading && error && <div role="alert" className="text-center py-10 text-red-600">{error}</div>}

      {!loading && !error && (
        <>
          <MetricsCard metrics={metrics} />
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <h2 className="text-xl font-semibold mb-4">Generation Forecast vs Actual</h2>
            <WindChart data={data} />
          </div>

          <div className="bg-white p-4 rounded-lg shadow overflow-x-auto">
            <h2 className="text-xl font-semibold mb-4">Data Table (30-min intervals)</h2>
            <table className="min-w-full divide-y divide-gray-200">
              <caption className="sr-only">Wind generation actual versus forecast per 30-minute settlement period</caption>
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actual (MW)</th>
                  <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Forecast (MW)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-6 text-center text-sm text-gray-500">No data for this date.</td>
                  </tr>
                ) : (
                  data.map((row, i) => (
                    <tr key={row.startTime ?? i} className="hover:bg-gray-50">
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        {new Date(row.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{row.actualGeneration?.toFixed(2) ?? '-'}</td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{row.forecastGeneration?.toFixed(2) ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default App;