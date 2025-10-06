import React from 'react'
function MetricsCard({ metrics }) {
  return (
    <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
      {Object.entries(metrics).map(([model, vals]) => (
        <div key={model} className='card rounded-md p-4 shadow border border-cyan-900/30'>
          <div className='font-semibold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-teal-300'>
            {model.toUpperCase()}
          </div>
          <div className='text-sm'>RMSE: <span className='text-cyan-300'>{vals.RMSE.toFixed(4)}</span></div>
          <div className='text-sm'>MAE: <span className='text-cyan-300'>{vals.MAE.toFixed(4)}</span></div>
          <div className='text-sm'>MAPE: <span className='text-cyan-300'>{vals.MAPE.toFixed(2)}%</span></div>
        </div>
      ))}
    </div>
  )
}

export default MetricsCard


