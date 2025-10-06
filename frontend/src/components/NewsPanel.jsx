import React from 'react'

function NewsPanel({ news }) {
  if (!news || news.length === 0) return null
  return (
    <div className='card rounded-md p-4 shadow'>
      <div className='text-sm uppercase tracking-wide text-cyan-300/80 mb-3'>Recent Headlines</div>
      <div className='space-y-2 max-h-64 overflow-auto pr-1'>
        {news.map((n, idx) => (
          <div key={idx} className='group p-2 rounded hover:bg-slate-900/60 transition-colors'>
            <div className='text-xs text-gray-400'>{n.date}</div>
            <div className='text-sm'>{n.headline}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default NewsPanel


