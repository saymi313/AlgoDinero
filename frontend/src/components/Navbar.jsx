import React from 'react'
import { Flame } from 'lucide-react'

function Navbar() {
  return (
    <div className='flex items-center py-3'>
      <div className='flex items-center gap-2 text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-teal-300'>
        <Flame className='w-5 h-5 text-cyan-300' /> AlgoDinero
      </div>
      <div className='ml-auto text-xs uppercase tracking-wide text-cyan-300/80 border border-cyan-700/50 rounded px-2 py-1 glow'>FinTech Forecasting</div>
    </div>
  )
}

export default Navbar


