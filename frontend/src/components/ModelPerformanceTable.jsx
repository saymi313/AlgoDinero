import React from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

function ModelPerformanceTable({ rankings, trends, loading }) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-gray-400">Loading performance data...</div>
      </div>
    )
  }

  const getTrendIcon = (trend) => {
    if (trend === 'improving') return <TrendingUp className="w-4 h-4 text-green-400" />
    if (trend === 'degrading') return <TrendingDown className="w-4 h-4 text-red-400" />
    return <Minus className="w-4 h-4 text-gray-400" />
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Model Performance Rankings</h3>
      
      {rankings && rankings.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-2 px-3 text-gray-300">Rank</th>
                <th className="text-left py-2 px-3 text-gray-300">Model</th>
                <th className="text-right py-2 px-3 text-gray-300">MAPE</th>
                <th className="text-right py-2 px-3 text-gray-300">RMSE</th>
                <th className="text-right py-2 px-3 text-gray-300">MAE</th>
                <th className="text-center py-2 px-3 text-gray-300">Evaluations</th>
              </tr>
            </thead>
            <tbody>
              {rankings.map((model, idx) => (
                <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-2 px-3 text-gray-400">#{idx + 1}</td>
                  <td className="py-2 px-3 text-white font-medium">
                    {model.model?.replace('_', ' ').toUpperCase()}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-300">
                    {model.average_mape?.toFixed(2)}%
                  </td>
                  <td className="py-2 px-3 text-right text-gray-300">
                    {model.average_rmse?.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-300">
                    {model.average_mae?.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-center text-gray-400">
                    {model.evaluations || 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {trends && Object.keys(trends).length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-700">
          <h4 className="text-md font-semibold text-white mb-3">Performance Trends</h4>
          <div className="space-y-2">
            {Object.entries(trends).map(([metric, trend]) => (
              <div key={metric} className="flex items-center justify-between p-2 bg-gray-700/30 rounded">
                <div className="flex items-center gap-2">
                  {getTrendIcon(trend.trend)}
                  <span className="text-sm text-gray-300">{metric}</span>
                </div>
                <div className="text-sm text-gray-400">
                  {trend.change_percentage > 0 ? '+' : ''}{trend.change_percentage.toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {(!rankings || rankings.length === 0) && (!trends || Object.keys(trends).length === 0) && (
        <div className="text-center text-gray-400 py-8">
          <div className="mb-2">No performance data available</div>
          <div className="text-xs text-gray-500">
            Run evaluation to see model rankings and trends
          </div>
        </div>
      )}
    </div>
  )
}

export default ModelPerformanceTable

