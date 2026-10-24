import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function WindChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-center text-gray-500 py-10">No data available for this date.</div>;
  }

  const chartData = data.map(d => ({
    time: new Date(d.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    Actual: d.actualGeneration,
    Forecast: d.forecastGeneration
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" interval={5} />
        <YAxis label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="Actual" stroke="#2563eb" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Forecast" stroke="#b45309" strokeWidth={2} strokeDasharray="5 5" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}