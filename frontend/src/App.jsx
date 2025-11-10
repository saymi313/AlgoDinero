import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Monitoring from './pages/Monitoring.jsx'
import Portfolio from './pages/Portfolio.jsx'

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <div className='min-h-screen bg-gray-900 text-white'>
        <div className='max-w-7xl mx-auto px-4 py-6'>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/portfolio" element={<Portfolio />} />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App


