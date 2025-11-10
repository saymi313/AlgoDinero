import React from 'react'
import Navbar from '../components/Navbar.jsx'
import InstrumentSelector from '../components/InstrumentSelector.jsx'
import ForecastOptions from '../components/ForecastOptions.jsx'
import ChartDisplay from '../components/ChartDisplay.jsx'
import MetricsCard from '../components/MetricsCard.jsx'
import Footer from '../components/Footer.jsx'
import NewsPanel from '../components/NewsPanel.jsx'

const API_BASE = 'http://127.0.0.1:8001'

function Home() {
  const [ticker, setTicker] = React.useState('AAPL')
  const [horizon, setHorizon] = React.useState(24)
  const [loading, setLoading] = React.useState(false)
  const [historical, setHistorical] = React.useState([])
  const [forecast, setForecast] = React.useState([])
  const [components, setComponents] = React.useState(null)
  const [metrics, setMetrics] = React.useState(null)
  const [sentiment, setSentiment] = React.useState([])
  const [news, setNews] = React.useState([])
  const [errors, setErrors] = React.useState([])

  async function curate() {
    setLoading(true)
    try {
      await fetch(`${API_BASE}/api/curate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days: 120 })
      })
      // no-op toast replacement
    } catch (e) {
      console.error('Curate failed', e)
    } finally { setLoading(false) }
  }

  async function visualize() {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/visualize`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days: 120, horizon: Number(horizon) })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Request failed')
      setHistorical(data.historical || [])
      setForecast(data.forecast || [])
      setComponents(data.components || null)
      setSentiment(data.sentiment || [])
      setNews(data.news || [])
      setErrors(data.errors || [])
    } catch (e) {
      console.error('Visualize failed', e)
    } finally { setLoading(false) }
  }

  async function runForecast() {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/forecast`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days: 120, horizon: Number(horizon) })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data?.detail || 'Request failed')
      setMetrics(data.metrics || null)
    } catch (e) {
      console.error('Forecast failed', e)
    } finally { setLoading(false) }
  }

  return (
    <div className='space-y-6'>
      <Navbar />
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <div className='md:col-span-2'>
          <InstrumentSelector ticker={ticker} onChange={setTicker} onCurate={curate} loading={loading} />
        </div>
        <div className='md:col-span-2'>
          <ForecastOptions horizon={horizon} setHorizon={setHorizon} onVisualize={visualize} onForecast={runForecast} loading={loading} />
        </div>
      </div>
      <ChartDisplay historical={historical} forecast={forecast} components={components} sentiment={sentiment} errors={errors} loading={loading} />
      {metrics && <MetricsCard metrics={metrics} />}
      <NewsPanel news={news} />
      <Footer />
    </div>
  )
}

export default Home


