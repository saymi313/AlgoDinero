import React from 'react'
import { TrendingUp, TrendingDown, Minus, Play, Square } from 'lucide-react'

function TradingPanel({ ticker, onTickerChange, prediction, onTrade, loading, autoMode, onAutoModeChange }) {
  const [quantity, setQuantity] = React.useState('')
  const [action, setAction] = React.useState('buy')

  const handleTrade = () => {
    if (!ticker) return
    
    // In auto mode, we need prediction. In manual mode, prediction is optional
    if (autoMode && !prediction) return
    
    const tradeData = {
      ticker,
      action: autoMode ? (prediction?.signal?.action || 'hold') : action, // Use signal action in auto mode
      quantity: quantity ? parseInt(quantity) : null,
      predicted_price: prediction?.predicted_price || prediction?.close || null,
      current_price: prediction?.current_price || null,
      autoMode: autoMode
    }
    
    onTrade(tradeData)
  }
  
  // Auto-execute trade when in auto mode and prediction changes
  // Use ref to prevent duplicate executions
  const lastExecutedSignal = React.useRef(null)
  const isExecuting = React.useRef(false)
  
  // Reset signal tracking when auto mode is toggled off
  React.useEffect(() => {
    if (!autoMode) {
      lastExecutedSignal.current = null
      isExecuting.current = false
    }
  }, [autoMode])
  
  React.useEffect(() => {
    // Only auto-execute if auto mode is ON, we have a prediction, and signal is not 'hold'
    if (autoMode && prediction && prediction.signal && prediction.signal.action !== 'hold' && !isExecuting.current) {
      // Create a unique key for this signal to avoid duplicate executions
      const signalKey = `${ticker}-${prediction.signal.action}-${prediction.predicted_price}`
      
      // Only execute if this is a new signal (not already executed)
      if (lastExecutedSignal.current !== signalKey) {
        lastExecutedSignal.current = signalKey
        isExecuting.current = true
        
        // Auto-execute based on signal
        const tradeData = {
          ticker,
          action: prediction.signal.action,
          quantity: null, // Auto quantity
          predicted_price: prediction.predicted_price || prediction.close,
          current_price: prediction.current_price || null,
          autoMode: true
        }
        
        // Execute trade and reset flag after a delay
        onTrade(tradeData)
        setTimeout(() => {
          isExecuting.current = false
        }, 2000) // Reset after 2 seconds to allow for trade completion
      }
    }
  }, [autoMode, prediction, ticker]) // Removed onTrade from deps to prevent loops

  const getSignalColor = (signal) => {
    if (signal === 'buy') return 'text-green-400'
    if (signal === 'sell') return 'text-red-400'
    return 'text-gray-400'
  }

  const getSignalIcon = (signal) => {
    if (signal === 'buy') return <TrendingUp className="w-4 h-4" />
    if (signal === 'sell') return <TrendingDown className="w-4 h-4" />
    return <Minus className="w-4 h-4" />
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Trading Panel</h3>
        <button
          onClick={() => onAutoModeChange(!autoMode)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            autoMode
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
          }`}
        >
          {autoMode ? (
            <>
              <Play className="w-4 h-4" />
              Auto ON
            </>
          ) : (
            <>
              <Square className="w-4 h-4" />
              Auto OFF
            </>
          )}
        </button>
      </div>
      
      {autoMode && (
        <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded text-sm text-green-300">
          <div className="font-semibold mb-1">Auto Mode Active</div>
          <div className="text-xs text-green-400">
            Trades will execute automatically based on prediction signals. Manual action selection is disabled.
          </div>
        </div>
      )}
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-300 mb-2">Ticker</label>
          <select
            value={ticker}
            onChange={(e) => onTickerChange(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="AAPL">AAPL — Apple</option>
            <option value="TSLA">TSLA — Tesla</option>
            <option value="BTC-USD">BTC-USD — Bitcoin</option>
            <option value="ETH-USD">ETH-USD — Ethereum</option>
            <option value="GLD">GLD — SPDR Gold Trust</option>
            <option value="EURUSD=X">EURUSD — Euro / USD</option>
          </select>
        </div>

        {prediction && (
          <div className="bg-gray-700/50 rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-300">Prediction Signal</span>
              <span className={`text-sm font-medium flex items-center gap-1 ${getSignalColor(prediction.signal?.action || 'hold')}`}>
                {getSignalIcon(prediction.signal?.action || 'hold')}
                {(prediction.signal?.action || 'hold').toUpperCase()}
              </span>
            </div>
            <div className="text-xs text-gray-400">
              {prediction.signal?.reason || 'No signal available'}
            </div>
            {prediction.signal?.predicted_return && (
              <div className="mt-2 text-sm text-gray-300">
                Predicted Return: {prediction.signal.predicted_return > 0 ? '+' : ''}
                {(prediction.signal.predicted_return * 100).toFixed(2)}%
              </div>
            )}
          </div>
        )}

        {!autoMode && (
          <div>
            <label className="block text-sm text-gray-300 mb-2">Action</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>
        )}

        <div>
          <label className="block text-sm text-gray-300 mb-2">
            Quantity (leave empty for auto)
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Auto"
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          />
        </div>

        <button
          onClick={handleTrade}
          disabled={(loading && autoMode) || !ticker || (autoMode && !prediction)}
          className="w-full bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading && autoMode ? (
            'Executing...'
          ) : autoMode ? (
            `Execute ${prediction?.signal?.action?.toUpperCase() || 'TRADE'}`
          ) : (
            `Execute ${action.toUpperCase()}`
          )}
        </button>
      </div>
    </div>
  )
}

export default TradingPanel

