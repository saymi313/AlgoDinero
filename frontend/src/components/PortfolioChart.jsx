import React from 'react'
import Plot from 'react-plotly.js'

function PortfolioChart({ portfolioHistory, priceData, loading }) {
  if (loading) {
    return (
      <div className="w-full h-64 bg-gray-800 rounded-lg p-4 flex items-center justify-center">
        <div className="text-gray-400">Loading chart...</div>
      </div>
    )
  }

  if (!portfolioHistory || portfolioHistory.length === 0) {
    return (
      <div className="w-full h-64 bg-gray-800 rounded-lg p-4 flex flex-col items-center justify-center border border-gray-700">
        <div className="text-gray-400 text-center">
          <div className="mb-2">No portfolio data available</div>
          <div className="text-xs text-gray-500 mt-2">
            Create a portfolio and execute trades to see value history
          </div>
        </div>
      </div>
    )
  }

  // Memoize chart data to prevent unnecessary re-renders
  const chartData = React.useMemo(() => {

    const portfolioDates = portfolioHistory.map(entry => entry.date || entry.timestamp)
    const portfolioValues = portfolioHistory.map(entry => entry.value || entry.total_value || 0)

    // Create portfolio value trace
    const portfolioTrace = {
      x: portfolioDates,
      y: portfolioValues,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Portfolio Value',
      line: { color: '#10b981', width: 2 },
      marker: { size: 6 },
      yaxis: 'y',
      fill: 'tozeroy',
      fillcolor: 'rgba(16, 185, 129, 0.1)'
    }

    const traces = [portfolioTrace]

    // Add price forecast trace if priceData is available
    if (priceData && priceData.historical && priceData.historical.length > 0) {
      // Combine historical and forecast prices
      const historicalPrices = priceData.historical || []
      const forecastPrices = priceData.forecast || []
      
      const priceDates = []
      const priceValues = []
      
      // Add historical prices
      historicalPrices.forEach(item => {
        priceDates.push(item.date || item.Date)
        priceValues.push(item.close || item.Close || 0)
      })
      
      // Add forecast prices
      if (forecastPrices.length > 0) {
        forecastPrices.forEach(item => {
          priceDates.push(item.date || item.Date)
          priceValues.push(item.close || item.Close || 0)
        })
      }
      
      if (priceDates.length > 0 && priceValues.length > 0) {
        const priceTrace = {
          x: priceDates,
          y: priceValues,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Stock Price',
          line: { color: '#06b6d4', width: 2, dash: 'dash' },
          marker: { size: 5 },
          yaxis: 'y2' // Use second y-axis for price
        }
        traces.push(priceTrace)
      }
    }

    // Determine if we need dual y-axes
    const hasPriceData = priceData && priceData.historical && priceData.historical.length > 0
    const useDualAxis = hasPriceData && portfolioValues.length > 0 && priceData.historical.length > 0
    
    return { traces, useDualAxis }
  }, [portfolioHistory, priceData])

  const { traces, useDualAxis } = chartData

  const layout = {
    title: useDualAxis ? 'Portfolio Value & Stock Price Over Time' : 'Portfolio Value Over Time',
    paper_bgcolor: 'rgba(17, 24, 39, 1)',
    plot_bgcolor: 'rgba(17, 24, 39, 1)',
    font: { color: '#e5e7eb' },
    xaxis: { 
      title: 'Date',
      gridcolor: 'rgba(55, 65, 81, 0.5)'
    },
    yaxis: { 
      title: 'Portfolio Value ($)',
      gridcolor: 'rgba(55, 65, 81, 0.5)',
      side: 'left',
      titlefont: { color: '#10b981' },
      tickfont: { color: '#10b981' }
    },
    margin: { l: 60, r: useDualAxis ? 60 : 30, t: 50, b: 50 },
    legend: {
      x: 0,
      y: 1,
      bgcolor: 'rgba(17, 24, 39, 0.8)',
      bordercolor: 'rgba(55, 65, 81, 0.5)',
      borderwidth: 1
    }
  }

  // Add second y-axis if we have price data
  if (useDualAxis) {
    layout.yaxis2 = {
      title: 'Stock Price ($)',
      overlaying: 'y',
      side: 'right',
      titlefont: { color: '#06b6d4' },
      tickfont: { color: '#06b6d4' },
      gridcolor: 'rgba(55, 65, 81, 0.3)'
    }
  }

  return (
    <div className="w-full h-64 bg-gray-800 rounded-lg p-4">
      <Plot
        data={traces}
        layout={layout}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
        config={{ responsive: true, displayModeBar: false }}
      />
    </div>
  )
}

export default PortfolioChart

