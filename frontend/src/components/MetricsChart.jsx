import React from 'react'
import Plot from 'react-plotly.js'

function MetricsChart({ data, metric, title }) {
  if (!data || !data.aggregated_metrics || Object.keys(data.aggregated_metrics).length === 0) {
    return (
      <div className="w-full h-64 bg-gray-800 rounded-lg p-4 flex flex-col items-center justify-center border border-gray-700">
        <div className="text-gray-400 text-center">
          <div className="mb-2">No {metric} data available</div>
          {data?.message && (
            <div className="text-xs text-gray-500 mt-2">{data.message}</div>
          )}
          {!data?.message && (
            <div className="text-xs text-gray-500 mt-2">
              Create forecasts and run evaluation to see metrics
            </div>
          )}
        </div>
      </div>
    )
  }

  // Sort by datetime if available, otherwise by date string
  const entries = Object.entries(data.aggregated_metrics || {}).map(([key, value]) => ({
    key,
    date: value.date || key,
    datetime: value.datetime || value.date || key,
    metrics: value.average_metrics || {}
  }))
  
  // Sort by datetime for proper chronological order
  entries.sort((a, b) => {
    try {
      const dateA = new Date(a.datetime).getTime()
      const dateB = new Date(b.datetime).getTime()
      return dateA - dateB
    } catch {
      return a.date.localeCompare(b.date)
    }
  })
  
  // Use actual datetime objects for X-axis to ensure proper spacing
  // Plotly needs datetime objects, not formatted strings, to create proper time series
  const dateObjects = entries.map(e => {
    const dt = e.datetime || e.date
    if (!dt) return null
    try {
      return new Date(dt)
    } catch {
      return null
    }
  }).filter(d => d !== null)
  
  // Use datetime objects for X-axis (Plotly will handle formatting)
  const dates = entries.map(e => {
    const dt = e.datetime || e.date
    if (!dt) return e.date
    try {
      return new Date(dt)
    } catch {
      return e.date
    }
  })
  const values = entries.map(e => e.metrics[metric] || 0)

  // If only one data point, show it as a marker (not a line)
  const trace = {
    x: dates,
    y: values,
    type: 'scatter',
    mode: entries.length === 1 ? 'markers' : 'lines+markers',
    name: metric,
    line: { color: '#10b981', width: 2 },
    marker: { size: entries.length === 1 ? 10 : 6, color: '#10b981' }
  }

  const layout = {
    title: title || `${metric} Over Time`,
    paper_bgcolor: 'rgba(17, 24, 39, 1)',
    plot_bgcolor: 'rgba(17, 24, 39, 1)',
    font: { color: '#e5e7eb' },
    xaxis: { 
      title: 'Date',
      type: 'date',  // Tell Plotly this is a date axis for proper time series spacing
      gridcolor: 'rgba(55, 65, 81, 0.5)',
      tickformat: '%b %d, %Y %H:%M'  // Format: "Nov 10, 2025 14:30"
    },
    yaxis: { 
      title: metric,
      gridcolor: 'rgba(55, 65, 81, 0.5)'
    },
    margin: { l: 60, r: 30, t: 50, b: 50 }
  }

  return (
    <div className="w-full h-64 bg-gray-800 rounded-lg p-4">
      <Plot
        data={[trace]}
        layout={layout}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
        config={{ responsive: true, displayModeBar: false }}
      />
    </div>
  )
}

export default MetricsChart

