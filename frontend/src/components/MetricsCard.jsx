export default function MetricsCard({ metrics }) {
  if (!metrics || metrics.dataPoints === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
        <h3 className="text-gray-500 text-sm">MAE (Mean Absolute Error)</h3>
        <p className="text-2xl font-bold text-blue-600">{metrics.mae} MW</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
        <h3 className="text-gray-500 text-sm">RMSE (Root Mean Square Error)</h3>
        <p className="text-2xl font-bold text-red-600">{metrics.rmse} MW</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
        <h3 className="text-gray-500 text-sm">Bias (Forecast - Actual)</h3>
        <p className="text-2xl font-bold text-green-600">{metrics.bias} MW</p>
      </div>
    </div>
  );
}