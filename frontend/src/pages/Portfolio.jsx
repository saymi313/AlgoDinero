import React from 'react'
import Navbar from '../components/Navbar.jsx'
import PortfolioChart from '../components/PortfolioChart.jsx'
import TradingPanel from '../components/TradingPanel.jsx'
import PerformanceMetrics from '../components/PerformanceMetrics.jsx'
import Footer from '../components/Footer.jsx'

const API_BASE = 'http://127.0.0.1:8001'

function Portfolio() {
  const [portfolioId, setPortfolioId] = React.useState('')
  const [portfolio, setPortfolio] = React.useState(null)
  const [ticker, setTicker] = React.useState('AAPL')
  const [prediction, setPrediction] = React.useState(null)
  const [performance, setPerformance] = React.useState(null)
  const [transactions, setTransactions] = React.useState([])
  const [loading, setLoading] = React.useState(false) // For portfolio operations
  const [predictionLoading, setPredictionLoading] = React.useState(false) // For prediction fetching
  const [portfolioHistory, setPortfolioHistory] = React.useState([])
  const [priceData, setPriceData] = React.useState(null)
  const [autoMode, setAutoMode] = React.useState(false) // Auto execution mode
  const [existingPortfolios, setExistingPortfolios] = React.useState([])
  const [showPortfolioList, setShowPortfolioList] = React.useState(false)
  
  // Use ref to track abort controller for prediction requests
  const predictionAbortControllerRef = React.useRef(null)
  
  // Load existing portfolios on component mount
  const loadExistingPortfolios = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/list`)
      const data = await res.json()
      if (res.ok && data.portfolios) {
        setExistingPortfolios(data.portfolios || [])
      }
    } catch (e) {
      console.error('Failed to load existing portfolios', e)
    }
  }
  
  // Load existing portfolios on mount
  React.useEffect(() => {
    loadExistingPortfolios()
  }, [])

  const createPortfolio = async () => {
    setLoading(true)
    try {
      // Add timeout to prevent hanging
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const res = await fetch(`${API_BASE}/api/portfolio/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initial_cash: 100000 }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }))
        throw new Error(errorData.detail || errorData.message || `HTTP ${res.status}`)
      }
      
      const data = await res.json()
      if (res.ok && data.portfolio_id) {
        const newPortfolioId = data.portfolio_id
        setPortfolioId(newPortfolioId)
        // Clear any previous data before setting new portfolio
        setPerformance(null)
        setTransactions([])
        setPortfolioHistory([])
        setPrediction(null)
        setPriceData(null)
        // Set the new portfolio data
        setPortfolio(data)
        // Fetch performance and transactions after creating (use the new portfolio ID)
            try {
              const perfRes = await fetch(`${API_BASE}/api/portfolio/${newPortfolioId}/performance`)
              const perfData = await perfRes.json()
              if (perfRes.ok) {
                setPerformance(perfData)
              }
            } catch (e) {
              console.error('Failed to fetch performance after creation', e)
            }
            
            try {
              const txRes = await fetch(`${API_BASE}/api/portfolio/${newPortfolioId}/history`)
              const txData = await txRes.json()
              if (txRes.ok) {
                setTransactions(txData.transactions || [])
              }
            } catch (e) {
              console.error('Failed to fetch transactions after creation', e)
            }
            
            // Refresh the existing portfolios list
            loadExistingPortfolios()
      } else {
        alert(`Failed to create portfolio: ${data.detail || data.message || 'Unknown error'}`)
        console.error('Portfolio creation failed:', data)
      }
    } catch (e) {
      console.error('Failed to create portfolio', e)
      if (e.name === 'AbortError') {
        alert('Request timed out. Please check if the backend server is running.')
      } else {
        alert(`Failed to create portfolio: ${e.message || 'Network error'}`)
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchPortfolio = async () => {
    if (!portfolioId) return
    
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/${portfolioId}`)
      const data = await res.json()
      if (res.ok) {
        setPortfolio(data)
      }
    } catch (e) {
      console.error('Failed to fetch portfolio', e)
    } finally {
      setLoading(false)
    }
  }

  const fetchPrediction = async () => {
    // Abort any previous request
    if (predictionAbortControllerRef.current) {
      predictionAbortControllerRef.current.abort()
    }
    
    // Create new abort controller for this request
    const controller = new AbortController()
    predictionAbortControllerRef.current = controller
    
    setPredictionLoading(true)
    try {
      // Add timeout to prevent hanging
      const timeoutId = setTimeout(() => {
        if (!controller.signal.aborted) {
          controller.abort()
        }
      }, 30000) // 30 second timeout
      
      // Only fetch forecast (it includes historical data too, no need for visualize)
      const forecastRes = await fetch(`${API_BASE}/api/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, days: 60, horizon: 1 }), // Reduced days for faster response
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      // Check if request was aborted
      if (controller.signal.aborted) {
        return // Silently return if aborted (component unmounted or new request started)
      }
      
      if (!forecastRes.ok) {
        throw new Error(`Forecast failed: ${forecastRes.status}`)
      }
      
      const forecastData = await forecastRes.json()
      
      // Check again if aborted before processing
      if (controller.signal.aborted) {
        return
      }
      
      // Fetch visualization data separately for chart (with timeout)
      const visualizeController = new AbortController()
      const visualizeTimeout = setTimeout(() => {
        if (!visualizeController.signal.aborted) {
          visualizeController.abort()
        }
      }, 30000)
      
      try {
        const visualizeRes = await fetch(`${API_BASE}/api/visualize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker, days: 60, horizon: 1 }),
          signal: visualizeController.signal
        })
        clearTimeout(visualizeTimeout)
        
        // Check if aborted before processing
        if (controller.signal.aborted || visualizeController.signal.aborted) {
          return
        }
        
        if (visualizeRes.ok) {
          const visualizeData = await visualizeRes.json()
          if (visualizeData.historical) {
            setPriceData({
              historical: visualizeData.historical || [],
              forecast: visualizeData.forecast || []
            })
          }
        }
      } catch (e) {
        // Only log if not aborted
        if (e.name !== 'AbortError') {
          console.warn('Visualize fetch failed (non-critical):', e)
        }
        // Continue without visualization data
      }
      
      // Final check before setting state
      if (controller.signal.aborted) {
        return
      }
      
      if (forecastData.predictions && forecastData.predictions.length > 0) {
        // Extract current price from forecast data
        let currentPrice = null
        if (forecastData.historical && forecastData.historical.length > 0) {
          const lastHistorical = forecastData.historical[forecastData.historical.length - 1]
          currentPrice = lastHistorical.close || lastHistorical.Close || null
        }
        
        const predictedPrice = forecastData.predictions[0]
        
        // Calculate predicted return if we have current price
        let predictedReturn = null
        let signalAction = 'hold'
        if (currentPrice && currentPrice > 0) {
          predictedReturn = (predictedPrice - currentPrice) / currentPrice
          // Simple signal: buy if predicted increase > 2%, sell if predicted decrease > 2%
          if (predictedReturn >= 0.02) {
            signalAction = 'buy'
          } else if (predictedReturn <= -0.02) {
            signalAction = 'sell'
          }
        }
        
        setPrediction({
          predicted_price: predictedPrice,
          current_price: currentPrice,
          signal: {
            action: signalAction,
            predicted_return: predictedReturn,
            reason: currentPrice 
              ? `Predicted ${predictedReturn > 0 ? 'increase' : 'decrease'} of ${Math.abs(predictedReturn * 100).toFixed(2)}%`
              : 'Based on forecast'
          }
        })
      }
    } catch (e) {
      // Only log/show error if not aborted (aborted requests are expected)
      if (e.name === 'AbortError') {
        // Silently handle abort - this is expected when component unmounts or new request starts
        return
      }
      console.error('Failed to fetch prediction', e)
      // Only show alert for actual errors, not aborts
      alert('Failed to fetch prediction. Please try again.')
    } finally {
      // Only reset loading if this is still the current request
      if (predictionAbortControllerRef.current === controller) {
        setPredictionLoading(false)
        predictionAbortControllerRef.current = null
      }
    }
  }

  const fetchPerformance = async () => {
    if (!portfolioId) return
    
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/${portfolioId}/performance`)
      const data = await res.json()
      if (res.ok) {
        setPerformance(data)
      } else {
        console.error('Failed to fetch performance:', data)
      }
    } catch (e) {
      console.error('Failed to fetch performance', e)
    }
  }

  const fetchTransactions = async () => {
    if (!portfolioId) return
    
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/${portfolioId}/history`)
      const data = await res.json()
      if (res.ok) {
        setTransactions(data.transactions || [])
      }
    } catch (e) {
      console.error('Failed to fetch transactions', e)
    }
  }

  const handleTrade = async (tradeData) => {
    if (!portfolioId) {
      alert('Please create a portfolio first')
      return
    }
    
    // Only show loading state in auto mode
    if (tradeData.autoMode) {
      setLoading(true)
    }
    try {
      // Add timeout to prevent hanging
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 15000) // 15 second timeout
      
      // Use the regular trade endpoint for manual trades
      // This allows users to execute trades regardless of signal
      const res = await fetch(`${API_BASE}/api/portfolio/trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: portfolioId,
          ticker: tradeData.ticker,
          action: tradeData.action, // Use user-selected action
          quantity: tradeData.quantity || null, // Use user-specified quantity or auto
          price: tradeData.current_price || prediction?.current_price || null // Use current price
        }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }))
        throw new Error(errorData.detail || errorData.message || `HTTP ${res.status}`)
      }
      
      const data = await res.json()
      console.log('Trade response:', data)
      
      if (data.success) {
        // Immediately update portfolio from response - this should have the latest holdings
        if (data.portfolio) {
          console.log('Portfolio from trade response:', data.portfolio)
          console.log('Holdings from trade response:', data.portfolio.holdings)
          setPortfolio({ ...data.portfolio }) // Create new object to force re-render
          
          // Also update transactions immediately if available
          if (data.transaction) {
            setTransactions(prev => {
              // Check if transaction already exists to avoid duplicates
              const exists = prev.some(tx => 
                tx.ticker === data.transaction.ticker &&
                tx.action === data.transaction.action &&
                tx.timestamp === data.transaction.timestamp
              )
              if (exists) return prev
              return [...prev, data.transaction]
            })
          }
        }
        
        // Add delay to ensure MongoDB has saved the transaction
        await new Promise(resolve => setTimeout(resolve, 1000)) // Increased to 1 second
        
        // Always refresh all portfolio data after trade (both auto and manual mode)
        // This ensures holdings, performance metrics, and history are updated
        setLoading(true) // Show loading during refresh
        try {
          const refreshController = new AbortController()
          const refreshTimeout = setTimeout(() => refreshController.abort(), 15000) // 15 second timeout for refresh
          
          const [portfolioRes, performanceRes, historyRes] = await Promise.all([
            fetch(`${API_BASE}/api/portfolio/${portfolioId}?skip_price_fetch=false`, { signal: refreshController.signal })
              .then(r => {
                if (!r.ok) throw new Error(`Portfolio fetch failed: ${r.status}`)
                return r.json()
              })
              .catch(e => {
                console.error('Failed to fetch portfolio:', e)
                return null
              }),
            fetch(`${API_BASE}/api/portfolio/${portfolioId}/performance`, { signal: refreshController.signal })
              .then(r => {
                if (!r.ok) throw new Error(`Performance fetch failed: ${r.status}`)
                return r.json()
              })
              .catch(e => {
                console.error('Failed to fetch performance:', e)
                return null
              }),
            fetch(`${API_BASE}/api/portfolio/${portfolioId}/history`, { signal: refreshController.signal })
              .then(r => {
                if (!r.ok) throw new Error(`History fetch failed: ${r.status}`)
                return r.json()
              })
              .catch(e => {
                console.error('Failed to fetch history:', e)
                return null
              })
          ])
          
          clearTimeout(refreshTimeout)
          
          // Update portfolio state - prioritize refresh data, but verify it has holdings
          if (portfolioRes && portfolioRes.portfolio_id) {
            console.log('Portfolio from refresh:', portfolioRes)
            console.log('Holdings from refresh:', portfolioRes.holdings)
            // Only update if refresh has valid data, otherwise keep trade response data
            if (portfolioRes.holdings !== undefined) {
              setPortfolio({ ...portfolioRes }) // Create new object to force re-render
            } else {
              console.warn('Refresh portfolio missing holdings, keeping trade response data')
            }
          } else if (data.portfolio) {
            // Fallback to portfolio from trade response if refresh failed
            console.log('Using portfolio from trade response (refresh failed):', data.portfolio)
            setPortfolio({ ...data.portfolio }) // Create new object to force re-render
          }
          
          // Update performance state - force update
          if (performanceRes && performanceRes.success !== false) {
            console.log('Updating performance from refresh:', performanceRes)
            setPerformance({ ...performanceRes }) // Create new object to force re-render
            if (performanceRes.history && performanceRes.history.length > 0) {
              setPortfolioHistory([...performanceRes.history]) // Create new array to force re-render
            }
          }
          
          // Update transactions state - force update
          if (historyRes && historyRes.transactions) {
            console.log('Updating transactions from refresh:', historyRes.transactions.length, 'transactions')
            setTransactions([...historyRes.transactions]) // Create new array to force re-render
          } else if (data.transaction) {
            // Fallback: add new transaction to existing list
            console.log('Adding transaction from trade response:', data.transaction)
            setTransactions(prev => {
              const exists = prev.some(tx => 
                tx.ticker === data.transaction.ticker &&
                tx.action === data.transaction.action &&
                tx.timestamp === data.transaction.timestamp
              )
              if (exists) return prev
              return [...prev, data.transaction]
            })
          }
          
        } catch (e) {
          console.error('Failed to refresh after trade', e)
          // Even if refresh fails, update with data from trade response
          if (data.portfolio) {
            setPortfolio(data.portfolio)
          }
          if (data.transaction) {
            setTransactions(prev => [...prev, data.transaction])
          }
        } finally {
          setLoading(false) // Always reset loading state
        }
        
        // Only show alert in manual mode (auto mode should be silent)
        if (!tradeData.autoMode) {
          alert(data.message || 'Trade executed successfully')
        }
      } else {
        if (!tradeData.autoMode) {
          alert(data.message || data.detail || 'Trade failed')
        }
      }
    } catch (e) {
      console.error('Trade failed', e)
      if (!tradeData.autoMode) {
        if (e.name === 'AbortError') {
          alert('Trade request timed out. Please check your connection and try again.')
        } else {
          alert('Trade execution failed: ' + (e.message || 'Unknown error'))
        }
      }
    } finally {
      // Always reset loading state
      setLoading(false)
    }
  }

  // Use ref to track if this is initial load (to avoid infinite loops)
  const isInitialLoad = React.useRef(true)
  
  const fetchAllPortfolioData = React.useCallback(async (showLoading = false) => {
    if (!portfolioId) return
    
    if (showLoading) {
      setLoading(true)
    }
    try {
      // Fetch in parallel with timeouts
      const controller1 = new AbortController()
      const controller2 = new AbortController()
      const controller3 = new AbortController()
      
      const timeout1 = setTimeout(() => controller1.abort(), 10000)
      const timeout2 = setTimeout(() => controller2.abort(), 10000)
      const timeout3 = setTimeout(() => controller3.abort(), 10000)
      
      // Fetch performance first (it includes history), then portfolio and transactions
      // This ensures we have proper history before rendering chart
      const [performanceRes, portfolioRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/api/portfolio/${portfolioId}/performance`, { signal: controller2.signal })
          .then(res => res.json())
          .catch(e => {
            clearTimeout(timeout2)
            if (e.name !== 'AbortError') console.error('Failed to fetch performance', e)
            return null
          }),
        fetch(`${API_BASE}/api/portfolio/${portfolioId}?skip_price_fetch=false`, { signal: controller1.signal })
          .then(res => res.json())
          .catch(e => {
            clearTimeout(timeout1)
            if (e.name !== 'AbortError') console.error('Failed to fetch portfolio', e)
            return null
          }),
        fetch(`${API_BASE}/api/portfolio/${portfolioId}/history`, { signal: controller3.signal })
          .then(res => res.json())
          .catch(e => {
            clearTimeout(timeout3)
            if (e.name !== 'AbortError') console.error('Failed to fetch transactions', e)
            return null
          })
      ])
      
      clearTimeout(timeout1)
      clearTimeout(timeout2)
      clearTimeout(timeout3)
      
      // Set performance and history FIRST (before portfolio) to avoid showing flat line
      if (performanceRes && performanceRes.success !== false) {
        setPerformance(performanceRes)
        // Use history from performance endpoint (includes all transaction points)
        if (performanceRes.history && performanceRes.history.length > 0) {
          setPortfolioHistory(performanceRes.history)
        } else if (performanceRes.portfolio) {
          // Fallback: build minimal history only if no transaction history exists
          const initialValue = performanceRes.portfolio.initial_value || performanceRes.portfolio.total_value || 100000
          const currentValue = performanceRes.portfolio.total_value || initialValue
          const minimalHistory = []
          if (performanceRes.portfolio.created_at) {
            minimalHistory.push({
              date: performanceRes.portfolio.created_at,
              value: initialValue
            })
          }
          if (currentValue !== initialValue || minimalHistory.length === 0) {
            minimalHistory.push({
              date: performanceRes.portfolio.updated_at || new Date().toISOString(),
              value: currentValue
            })
          }
          setPortfolioHistory(minimalHistory)
        }
      }
      
      // Set portfolio after history is set
      if (portfolioRes && portfolioRes.portfolio_id) {
        setPortfolio(portfolioRes)
      }
      
      if (historyRes && historyRes.transactions) {
        setTransactions(historyRes.transactions || [])
      }
      
      isInitialLoad.current = false
    } catch (e) {
      console.error('Failed to fetch portfolio data', e)
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }, [portfolioId])

  React.useEffect(() => {
    if (portfolioId) {
      // Initial load with loading indicator
      fetchAllPortfolioData(true)
    } else {
      // Reset initial load flag when portfolioId is cleared
      isInitialLoad.current = true
    }
  }, [portfolioId, fetchAllPortfolioData])

      React.useEffect(() => {
        // Only fetch prediction if we have a portfolio (to avoid unnecessary loading on page load)
        if (ticker && portfolioId) {
          fetchPrediction()
        }
        
        // Cleanup: abort any pending requests when component unmounts or dependencies change
        return () => {
          if (predictionAbortControllerRef.current) {
            predictionAbortControllerRef.current.abort()
            predictionAbortControllerRef.current = null
          }
        }
      }, [ticker, portfolioId])

  // Use history from performance endpoint if available
  // This effect ensures history is set from performance data (which has transaction-based history)
  React.useEffect(() => {
    // Priority: Use history from performance endpoint (most accurate, includes all transactions)
    if (performance && performance.history && performance.history.length > 0) {
      // Only update if history actually changed
      const currentHistory = JSON.stringify(portfolioHistory)
      const newHistory = JSON.stringify(performance.history)
      if (currentHistory !== newHistory) {
        setPortfolioHistory(performance.history)
      }
      return
    }
    
    // Fallback: Only build basic history if we have portfolio but NO performance data yet
    // This prevents showing flat line before performance data loads
    if (portfolio && portfolio.portfolio_id && (!performance || !performance.history)) {
      // Wait a bit to see if performance data is still loading
      // Only set minimal history if we're sure performance won't arrive
      const history = []
      const initialValue = portfolio.initial_value || portfolio.total_value || 100000
      
      // Add initial point
      if (portfolio.created_at) {
        history.push({
          date: portfolio.created_at,
          value: initialValue
        })
      }
      
      // Add current point
      const currentValue = portfolio.total_value || initialValue
      if (currentValue !== initialValue || history.length === 0) {
        history.push({
          date: portfolio.updated_at || new Date().toISOString(),
          value: currentValue
        })
      }
      
      // Only update if we don't have history yet (to avoid overwriting performance history)
      if (portfolioHistory.length === 0) {
        setPortfolioHistory(history)
      }
    } else if (!portfolio || !portfolio.portfolio_id) {
      // Clear history if no portfolio
      if (portfolioHistory.length > 0) {
        setPortfolioHistory([])
      }
    }
  }, [portfolio, performance]) // Removed portfolioHistory from deps to prevent loops

  return (
    <div className="space-y-6">
      <Navbar />
      
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Portfolio Management</h1>
            {!portfolioId ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setShowPortfolioList(!showPortfolioList)
                    if (!showPortfolioList) {
                      loadExistingPortfolios()
                    }
                  }}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded"
                >
                  {showPortfolioList ? 'Hide' : 'Load'} Existing Portfolios
                </button>
                <button
                  onClick={createPortfolio}
                  disabled={loading}
                  className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Create New Portfolio'}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Portfolio ID:</span>
                <input
                  type="text"
                  value={portfolioId}
                  onChange={(e) => setPortfolioId(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm w-64"
                />
                <button
                  onClick={() => {
                    setPortfolioId('')
                    setPortfolio(null)
                    setPerformance(null)
                    setTransactions([])
                    setPortfolioHistory([])
                    setPrediction(null)
                    setPriceData(null)
                  }}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded text-sm"
                >
                  Clear
                </button>
                <button
                  onClick={() => fetchAllPortfolioData(true)}
                  disabled={loading}
                  className="bg-cyan-600 hover:bg-cyan-700 text-white px-3 py-2 rounded text-sm disabled:opacity-50"
                >
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
            )}
          </div>
          
          {showPortfolioList && existingPortfolios.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Existing Portfolios</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {existingPortfolios.map((p) => (
                  <div
                    key={p.portfolio_id}
                    className="flex items-center justify-between p-3 bg-gray-700/50 rounded border border-gray-600 hover:border-cyan-500 cursor-pointer transition-colors"
                    onClick={() => {
                      setPortfolioId(p.portfolio_id)
                      setShowPortfolioList(false)
                      // Portfolio will be loaded by useEffect when portfolioId changes
                    }}
                  >
                    <div className="flex-1">
                      <div className="text-sm font-medium text-white">
                        Portfolio: {p.portfolio_id.substring(0, 8)}...
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        Created: {new Date(p.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-cyan-400">
                        ${p.total_value?.toFixed(2) || 0}
                      </div>
                      <div className="text-xs text-gray-400">
                        {p.holdings_count || 0} holdings
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {showPortfolioList && existingPortfolios.length === 0 && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-center text-gray-400">
                No existing portfolios found. Create a new portfolio to get started.
              </div>
            </div>
          )}

      {portfolio && (
        <>
          {transactions.length === 0 && (
            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 text-blue-300 text-sm">
              <div className="font-semibold mb-2">💡 How to use the Portfolio:</div>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Select a ticker from the dropdown (e.g., AAPL, TSLA, BTC-USD)</li>
                <li>Wait for the prediction to load (shows current price and predicted price)</li>
                <li>Click "Buy" or "Sell" based on the prediction signal</li>
                <li>Watch your portfolio value update in real-time on the chart</li>
                <li>View your holdings, transactions, and performance metrics below</li>
                <li>Click "Refresh" button to update portfolio values with current market prices</li>
              </ol>
            </div>
          )}
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="mb-3">
                <h2 className="text-xl font-semibold text-white mb-2">Portfolio Value & Stock Price Chart</h2>
                <p className="text-sm text-gray-400">
                  Displays your portfolio value over time alongside the selected stock's price forecast, showing how your investments perform relative to market movements.
                </p>
              </div>
              <PortfolioChart 
                portfolioHistory={portfolioHistory} 
                priceData={priceData}
                loading={loading} 
              />
            </div>
            <TradingPanel
              ticker={ticker}
              onTickerChange={setTicker}
              prediction={prediction}
              onTrade={handleTrade}
              loading={loading || predictionLoading}
              autoMode={autoMode}
              onAutoModeChange={setAutoMode}
            />
          </div>

          <PerformanceMetrics metrics={performance} loading={loading} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Holdings</h3>
              {portfolio.holdings && Object.keys(portfolio.holdings).length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-2 px-3 text-gray-300">Ticker</th>
                        <th className="text-right py-2 px-3 text-gray-300">Quantity</th>
                        <th className="text-right py-2 px-3 text-gray-300">Avg Price</th>
                        <th className="text-right py-2 px-3 text-gray-300">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(portfolio.holdings).map(([ticker, holding]) => (
                        <tr key={ticker} className="border-b border-gray-700/50">
                          <td className="py-2 px-3 text-white font-medium">{ticker}</td>
                          <td className="py-2 px-3 text-right text-gray-300">{holding.quantity?.toFixed(4) || 0}</td>
                          <td className="py-2 px-3 text-right text-gray-300">
                            ${holding.avg_price?.toFixed(2) || 0}
                          </td>
                          <td className="py-2 px-3 text-right text-gray-300">
                            ${holding.value?.toFixed(2) || (holding.quantity * holding.avg_price).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8">No holdings</div>
              )}
              <div className="mt-4 pt-4 border-t border-gray-700">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-400">Cash</span>
                  <span className="text-lg font-semibold text-white">
                    ${portfolio.cash?.toFixed(2) || 0}
                  </span>
                </div>
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-400">Total Value</span>
                  <span className="text-lg font-semibold text-cyan-400">
                    ${portfolio.total_value?.toFixed(2) || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">Transaction History</h3>
              {transactions.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {transactions.map((tx, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-gray-700/30 rounded border-l-4 border-cyan-500"
                    >
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-sm font-medium ${
                          tx.action === 'buy' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {tx.action.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(tx.timestamp || tx.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300">
                        {tx.quantity?.toFixed(4) || tx.quantity} {tx.ticker} @ ${tx.price?.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        Value: ${tx.value?.toFixed(2) || 0}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8">No transactions</div>
              )}
            </div>
          </div>
        </>
      )}

      <Footer />
    </div>
  )
}

export default Portfolio

