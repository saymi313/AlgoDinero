import React from 'react'

function InstrumentSelector({ ticker, onChange, onCurate, loading }) {
  return (
    <div className='card rounded-md p-4 shadow'>
      <div className='mb-2 text-gray-300'>Ticker</div>
      <div className='flex items-center gap-2'>
        <select value={ticker} onChange={e => onChange(e.target.value)}
                className='w-full px-3 py-2 rounded bg-slate-900 border border-slate-700 focus:outline-none focus:border-cyan-500'>
          <option value='AAPL'>AAPL — Apple</option>
          <option value='TSLA'>TSLA — Tesla</option>
          <option value='BTC-USD'>BTC-USD — Bitcoin</option>
          <option value='ETH-USD'>ETH-USD — Ethereum</option>
          <option value='GLD'>GLD — SPDR Gold Trust</option>
          <option value='EURUSD=X'>EURUSD — Euro / USD</option>
        </select>
        <button onClick={onCurate} disabled={loading}
                className='px-3 py-2 rounded bg-cyan-600 hover:bg-cyan-500 transition-colors glow disabled:opacity-60'>
          Curate
        </button>
      </div>
    </div>
  )
}

export default InstrumentSelector


