import React from 'react'
import { TrendingUp, DollarSign, BarChart3 } from 'lucide-react'

function PerformanceMetrics({ metrics, loading }) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-gray-400">Loading metrics...</div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex flex-col items-center gap-2 text-gray-400">
          <div>No performance data available</div>
          <div className="text-xs text-gray-500 mt-2 text-center">
            Create a portfolio and execute trades to see performance metrics
          </div>
        </div>
      </div>
    )
  }

  const m = metrics.metrics || metrics

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5" />
        Performance Metrics
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-700/50 rounded p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-gray-400">Total Return</span>
          </div>
          <div className={`text-xl font-bold ${
            m.total_return_pct >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {m.total_return_pct >= 0 ? '+' : ''}{m.total_return_pct?.toFixed(2) || 0}%
          </div>
          <div className="text-xs text-gray-500 mt-1">
            ${m.total_return?.toFixed(2) || 0}
          </div>
        </div>

        <div className="bg-gray-700/50 rounded p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-gray-400">Annualized Return</span>
          </div>
          <div className={`text-xl font-bold ${
            m.annualized_return >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {m.annualized_return >= 0 ? '+' : ''}{m.annualized_return?.toFixed(2) || 0}%
          </div>
        </div>

        <div className="bg-gray-700/50 rounded p-4">
          <div className="text-xs text-gray-400 mb-2">Volatility</div>
          <div className="text-xl font-bold text-yellow-400">
            {m.volatility?.toFixed(2) || 0}
          </div>
        </div>

        <div className="bg-gray-700/50 rounded p-4">
          <div className="text-xs text-gray-400 mb-2">Sharpe Ratio</div>
          <div className={`text-xl font-bold ${
            m.sharpe_ratio >= 1 ? 'text-green-400' : m.sharpe_ratio >= 0 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {m.sharpe_ratio?.toFixed(2) || 0}
          </div>
        </div>
      </div>

      {m.current_value && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-400">Current Value</span>
            <span className="text-lg font-semibold text-white">
              ${m.current_value.toFixed(2)}
            </span>
          </div>
          {m.initial_value && (
            <div className="flex justify-between items-center mt-2">
              <span className="text-sm text-gray-400">Initial Value</span>
              <span className="text-sm text-gray-300">
                ${m.initial_value.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default PerformanceMetrics

