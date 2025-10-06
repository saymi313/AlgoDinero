import React from 'react'

function ForecastOptions({ horizon, setHorizon, onVisualize, onForecast, loading }) {
  const opts = [1, 3, 24, 72]
  return (
    <div className='card rounded-md p-4 shadow'>
      <div className='flex items-center justify-between'>
        <div className='inline-flex rounded overflow-hidden border border-slate-700'>
          {opts.map(h => (
            <button key={h} onClick={() => setHorizon(h)}
                    className={`px-3 py-1.5 transition-colors ${Number(horizon)===h? 'bg-cyan-600 text-white' : 'bg-slate-900 text-gray-300 hover:bg-slate-800'}`}>
              {h}h
            </button>
          ))}
        </div>
        <div className='flex gap-2'>
          <button onClick={onVisualize} disabled={loading} className='px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 transition-colors glow disabled:opacity-60'>Visualize</button>
          <button onClick={onForecast} disabled={loading} className='px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 transition-colors glow disabled:opacity-60'>Forecast</button>
        </div>
      </div>
    </div>
  )
}

export default ForecastOptions


