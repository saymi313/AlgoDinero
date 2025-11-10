import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Flame, BarChart3, Wallet } from 'lucide-react'

function Navbar() {
  const location = useLocation()
  
  return (
    <div className='flex items-center py-3'>
      <div className='flex items-center gap-2 text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-teal-300'>
        <Flame className='w-5 h-5 text-cyan-300' /> AlgoDinero
      </div>
      <div className='ml-auto flex items-center gap-4'>
        <Link
          to="/"
          className={`text-sm px-3 py-1 rounded transition-colors ${
            location.pathname === '/'
              ? 'bg-cyan-600 text-white'
              : 'text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-900/30'
          }`}
        >
          Forecast
        </Link>
        <Link
          to="/monitoring"
          className={`text-sm px-3 py-1 rounded transition-colors flex items-center gap-1 ${
            location.pathname === '/monitoring'
              ? 'bg-cyan-600 text-white'
              : 'text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-900/30'
          }`}
        >
          <BarChart3 className='w-4 h-4' />
          Monitoring
        </Link>
        <Link
          to="/portfolio"
          className={`text-sm px-3 py-1 rounded transition-colors flex items-center gap-1 ${
            location.pathname === '/portfolio'
              ? 'bg-cyan-600 text-white'
              : 'text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-900/30'
          }`}
        >
          <Wallet className='w-4 h-4' />
          Portfolio
        </Link>
        <div className='text-xs uppercase tracking-wide text-cyan-300/80 border border-cyan-700/50 rounded px-2 py-1 glow'>FinTech Forecasting</div>
      </div>
    </div>
  )
}

export default Navbar


