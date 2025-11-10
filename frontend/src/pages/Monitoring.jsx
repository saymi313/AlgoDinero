import React from 'react'
import Navbar from '../components/Navbar.jsx'
import MetricsChart from '../components/MetricsChart.jsx'
import AlertPanel from '../components/AlertPanel.jsx'
import ModelPerformanceTable from '../components/ModelPerformanceTable.jsx'
import Footer from '../components/Footer.jsx'

const API_BASE = 'http://127.0.0.1:8001'

function Monitoring() {
  const [ticker, setTicker] = React.useState('AAPL')
  const [loading, setLoading] = React.useState(false)
  const [maeData, setMaeData] = React.useState(null)
  const [rmseData, setRmseData] = React.useState(null)
  const [mapeData, setMapeData] = React.useState(null)
  const [alerts, setAlerts] = React.useState([])
  const [rankings, setRankings] = React.useState([])
  const [trends, setTrends] = React.useState(null)
  const [window, setWindow] = React.useState('daily')
  const [daysBack, setDaysBack] = React.useState(30)
  const [evaluating, setEvaluating] = React.useState(false)
  const [evalMessage, setEvalMessage] = React.useState(null)

  const fetchMetrics = React.useCallback(async () => {
    setLoading(true)
    try {
      // Fetch aggregated metrics (contains all metrics: MAE, RMSE, MAPE)
      const metricsRes = await fetch(
        `${API_BASE}/api/monitoring/metrics?ticker=${ticker}&window=${window}&days_back=${daysBack}`
      )
      const metricsData = await metricsRes.json()
      
      // All three charts use the same data, but display different metrics
      setMaeData(metricsData)
      setRmseData(metricsData)
      setMapeData(metricsData)

      // Fetch alerts
      const alertsRes = await fetch(`${API_BASE}/api/monitoring/alerts?ticker=${ticker}&limit=20`)
      const alertsData = await alertsRes.json()
      setAlerts(alertsData.alerts || [])

      // Fetch rankings
      const rankingsRes = await fetch(`${API_BASE}/api/monitoring/rankings?ticker=${ticker}&metric=MAPE&days_back=${daysBack}`)
      const rankingsData = await rankingsRes.json()
      if (rankingsData.success && rankingsData.rankings) {
        // Transform rankings to include all metrics
        const transformedRankings = rankingsData.rankings.map(rank => ({
          model: rank.model,
          average_mape: rank.average_mape || 0,
          average_rmse: rank.average_rmse || 0,
          average_mae: rank.average_mae || 0,
          evaluations: rank.evaluations || 0
        }))
        setRankings(transformedRankings)
      } else {
        setRankings([])
      }

      // Fetch trends
      const trendsRes = await fetch(
        `${API_BASE}/api/monitoring/performance-trends?ticker=${ticker}&days_back=${daysBack}`
      )
      const trendsData = await trendsRes.json()
      if (trendsData.success && trendsData.trends) {
        setTrends(trendsData.trends)
      }
    } catch (e) {
      console.error('Failed to fetch monitoring data', e)
    } finally {
      setLoading(false)
    }
  }, [ticker, window, daysBack])

  const runEvaluation = React.useCallback(async () => {
    setEvaluating(true)
    setEvalMessage(null)
    try {
      const res = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days_back: 7 })
      })
      const data = await res.json()
      if (res.ok && data.success) {
        setEvalMessage({ type: 'success', text: `Evaluation completed! Evaluated ${data.count || 0} predictions.` })
        // Refresh metrics after evaluation
        setTimeout(() => {
          fetchMetrics()
        }, 1000)
      } else {
        setEvalMessage({ type: 'error', text: data.message || 'Evaluation failed' })
      }
    } catch (e) {
      setEvalMessage({ type: 'error', text: 'Failed to run evaluation: ' + e.message })
    } finally {
      setEvaluating(false)
    }
  }, [ticker, fetchMetrics])

  React.useEffect(() => {
    fetchMetrics()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [fetchMetrics])

  return (
    <div className="space-y-6">
      <Navbar />
      
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Monitoring Dashboard</h1>
        <div className="flex items-center gap-4">
          {evalMessage && (
            <div className={`px-3 py-2 rounded text-sm ${
              evalMessage.type === 'success' 
                ? 'bg-green-900/50 text-green-300 border border-green-700' 
                : 'bg-red-900/50 text-red-300 border border-red-700'
            }`}>
              {evalMessage.text}
            </div>
          )}
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
          >
            <option value="AAPL">AAPL — Apple</option>
            <option value="TSLA">TSLA — Tesla</option>
            <option value="BTC-USD">BTC-USD — Bitcoin</option>
            <option value="ETH-USD">ETH-USD — Ethereum</option>
            <option value="GLD">GLD — SPDR Gold Trust</option>
            <option value="EURUSD=X">EURUSD — Euro / USD</option>
          </select>
          <select
            value={window}
            onChange={(e) => setWindow(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <input
            type="number"
            value={daysBack}
            onChange={(e) => setDaysBack(Number(e.target.value))}
            placeholder="Days"
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm w-20"
          />
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            Refresh
          </button>
          <button
            onClick={runEvaluation}
            disabled={evaluating || loading}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            {evaluating ? 'Evaluating...' : 'Run Evaluation'}
          </button>
        </div>
      </div>

      {(!maeData || !maeData.aggregated_metrics || Object.keys(maeData.aggregated_metrics || {}).length === 0) && (
        <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 text-blue-300 text-sm">
          <div className="font-semibold mb-2">💡 How to see metrics over time:</div>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Create multiple forecasts for the same ticker (each forecast creates a data point)</li>
            <li>Run evaluation after each forecast (or click "Run Evaluation" to evaluate all recent forecasts)</li>
            <li>Each evaluation will appear as a separate point in the charts</li>
            <li>Try creating forecasts on different days to see a time series</li>
          </ol>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-white mb-2">Performance Metrics Over Time</h2>
          <p className="text-sm text-gray-400">
            These charts display prediction accuracy metrics that track how well the forecasting models perform over time. Lower values indicate better prediction accuracy.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-cyan-300 mb-1">Mean Absolute Error (MAE)</h3>
            <p className="text-xs text-gray-400">
              Shows the average absolute difference between predicted and actual prices, indicating the typical magnitude of prediction errors.
            </p>
          </div>
          <MetricsChart data={maeData} metric="MAE" title="Mean Absolute Error" />
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-cyan-300 mb-1">Root Mean Squared Error (RMSE)</h3>
            <p className="text-xs text-gray-400">
              Displays the square root of average squared errors, giving more weight to larger prediction errors and highlighting significant deviations.
            </p>
          </div>
          <MetricsChart data={rmseData} metric="RMSE" title="Root Mean Squared Error" />
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="mb-3">
          <h3 className="text-lg font-semibold text-cyan-300 mb-1">Mean Absolute Percentage Error (MAPE)</h3>
          <p className="text-xs text-gray-400">
            Illustrates the average percentage error between predicted and actual prices, providing a relative measure of prediction accuracy that is easy to interpret.
          </p>
        </div>
        <MetricsChart data={mapeData} metric="MAPE" title="Mean Absolute Percentage Error" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertPanel alerts={alerts} loading={loading} />
        <ModelPerformanceTable rankings={rankings} trends={trends} loading={loading} />
      </div>

      <Footer />
    </div>
  )
}

export default Monitoring

