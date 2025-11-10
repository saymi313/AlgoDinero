import React from 'react'
import Plot from 'react-plotly.js'
import ErrorOverlay from './ErrorOverlay.jsx'

function ChartDisplay({ historical, forecast, components, sentiment, errors, loading }) {
  const [show, setShow] = React.useState({ ma:false, arima:false, mlp:false, var:false, gru:false, lstm:false, transformer:false })
  const [showErrors, setShowErrors] = React.useState(false)

  const ohlc = {
    x: historical.map(d => d.date),
    open: historical.map(d => d.open),
    high: historical.map(d => d.high),
    low: historical.map(d => d.low),
    close: historical.map(d => d.close),
    type: 'candlestick', name: 'Historical',
    increasing: { line: { color: '#22c55e' }, fillcolor: '#22c55e' },
    decreasing: { line: { color: '#ef4444' }, fillcolor: '#ef4444' }
  }
  const forecastTrace = {
    x: forecast.map(d => d.date), y: forecast.map(d => d.close),
    type: 'scatter', mode: 'lines+markers', name: 'Forecast', line: { color:'#22d3ee', width:2 }
  }
  const extras = []
  if (components) {
    const start = forecast[0]?.date
    const keys = [
      ['ma','moving_average','#f59e0b'],
      ['arima','arima','#10b981'],
      ['mlp','mlp','#6366f1'],
      ['var','var','#ef4444'],
      ['gru','gru','#a855f7'],
      ['lstm','lstm','#f97316'],
      ['transformer','transformer','#eab308']
    ]
    keys.forEach(([flag, key, color]) => {
      if (show[flag] && components[key]?.length) {
        extras.push({ x: components[key].map((_,i)=>forecast[i]?.date||start), y: components[key], type:'scatter', mode:'lines', name:key.toUpperCase(), line:{ color, width:1.5, dash:'dot' } })
      }
    })
  }
  const colorMap = { ma:'#f59e0b', arima:'#10b981', mlp:'#6366f1', var:'#ef4444', gru:'#a855f7', lstm:'#f97316', transformer:'#eab308' }
  const sentimentTrace = {
    x: sentiment.map(s=>s.date), y: sentiment.map(s=>s.score), type:'bar', name:'Sentiment', marker:{ color:'#60a5fa' }, xaxis:'x', yaxis:'y2'
  }

  // Error overlay traces
  const errorTraces = []
  if (showErrors && errors && errors.length > 0) {
    errors.forEach((error, idx) => {
      if (error.actual && error.predicted) {
        const errorValue = error.actual - error.predicted
        const errorPct = error.actual > 0 ? (errorValue / error.actual) * 100 : 0
        
        // Create error bar trace
        errorTraces.push({
          x: [error.date],
          y: [error.actual],
          type: 'scatter',
          mode: 'markers',
          name: `Error ${idx + 1}`,
          error_y: {
            type: 'data',
            array: [Math.abs(errorValue)],
            color: errorValue > 0 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
            thickness: 3
          },
          marker: {
            color: errorValue > 0 ? '#22c55e' : '#ef4444',
            size: 8,
            line: { width: 1, color: errorValue > 0 ? '#16a34a' : '#dc2626' }
          },
          text: [`Error: ${errorPct.toFixed(2)}%`],
          hovertemplate: '<b>%{text}</b><br>Actual: $%{y:.2f}<br>Predicted: $' + error.predicted.toFixed(2) + '<extra></extra>'
        })
      }
    })

    // Add error bands (colored regions)
    if (errors.length > 1) {
      const errorDates = errors.map(e => e.date).filter(Boolean)
      const upperBounds = errors.map(e => e.actual > e.predicted ? e.actual : e.predicted)
      const lowerBounds = errors.map(e => e.actual < e.predicted ? e.actual : e.predicted)
      
      errorTraces.push({
        x: errorDates,
        y: upperBounds,
        type: 'scatter',
        mode: 'lines',
        name: 'Error Upper',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip'
      })
      
      errorTraces.push({
        x: errorDates,
        y: lowerBounds,
        type: 'scatter',
        mode: 'lines',
        name: 'Error Band',
        fill: 'tonexty',
        fillcolor: 'rgba(239, 68, 68, 0.1)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip'
      })
    }
  }
  const layout = {
    paper_bgcolor:'#0b1220', plot_bgcolor:'#0b1220', font:{ color:'#e5e7eb' },
    xaxis:{ gridcolor:'#334155' }, yaxis:{ gridcolor:'#334155', domain:[0.35,1] },
    xaxis2:{ gridcolor:'#334155' }, yaxis2:{ gridcolor:'#334155', domain:[0,0.25] },
    hovermode: 'x unified', dragmode: 'pan', legend:{ orientation:'h', x:0, y:1.1 },
    margin:{ t:28, r:24, b:48, l:56 }, height:660,
    transition: { duration: 300, easing: 'cubic-in-out' }
  }

  return (
    <div className='bg-slate-900 rounded-md p-3 shadow'>
      <ErrorOverlay errors={errors} showErrors={showErrors} onToggle={setShowErrors} />
      <div className='flex flex-wrap gap-2 mb-3'>
        {Object.keys(show).map(k => {
          const active = !!show[k]
          const c = colorMap[k] || '#22d3ee'
          return (
            <button
              key={k}
              onClick={()=>setShow(s=>({ ...s, [k]: !s[k] }))}
              className={`group relative inline-flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${active ? 'border-transparent bg-slate-800 shadow-[0_0_20px_rgba(34,211,238,0.15)]' : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/60'}`}
              style={active ? { boxShadow: `0 0 18px ${c}44` } : {}}
              aria-pressed={active}
            >
              <span className='w-2.5 h-2.5 rounded-full' style={{ background: c }} />
              <span className={`text-xs tracking-wide ${active ? 'text-white' : 'text-gray-300 group-hover:text-gray-200'}`}>{k.toUpperCase()}</span>
            </button>
          )
        })}
      </div>
      {loading ? (
        <div className='py-16 flex justify-center'>
          <div className='h-8 w-8 animate-spin rounded-full border-2 border-cyan-300 border-t-transparent' />
        </div>
      ) : (
        <Plot
          data={[ohlc, forecastTrace, ...extras, ...errorTraces, sentimentTrace]}
          layout={layout}
          style={{ width:'100%', height:'100%' }}
          useResizeHandler
          config={{ displayModeBar:true, displaylogo:false, responsive:true, scrollZoom:true, modeBarButtonsToRemove:['autoScale2d','toggleSpikelines'] }}
        />
      )}
    </div>
  )
}

export default ChartDisplay


