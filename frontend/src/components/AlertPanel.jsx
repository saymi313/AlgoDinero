import React from 'react'
import { AlertTriangle, Info } from 'lucide-react'

function AlertPanel({ alerts, loading }) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="text-gray-400">Loading alerts...</div>
      </div>
    )
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex flex-col items-center gap-2 text-gray-400">
          <Info className="w-5 h-5" />
          <span>No alerts at this time</span>
          <div className="text-xs text-gray-500 mt-2 text-center">
            Alerts will appear when model performance metrics exceed thresholds
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-yellow-400" />
        <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
        <span className="ml-auto text-sm text-gray-400">{alerts.length} alerts</span>
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.map((alert, idx) => (
          <div
            key={idx}
            className={`p-3 rounded border-l-4 ${
              alert.severity === 'error'
                ? 'bg-red-900/20 border-red-500'
                : 'bg-yellow-900/20 border-yellow-500'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-sm font-medium ${
                    alert.severity === 'error' ? 'text-red-300' : 'text-yellow-300'
                  }`}>
                    {alert.type?.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400">{alert.ticker}</span>
                </div>
                <p className="text-sm text-gray-300">{alert.message}</p>
                <div className="mt-2 text-xs text-gray-400">
                  {alert.evaluation_date ? new Date(alert.evaluation_date).toLocaleString() : ''}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AlertPanel

