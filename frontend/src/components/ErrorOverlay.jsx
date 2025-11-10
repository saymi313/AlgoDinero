import React from 'react'

function ErrorOverlay({ errors, showErrors, onToggle }) {
  if (!errors || errors.length === 0) {
    return null
  }

  return (
    <div className="mb-3 flex items-center gap-4">
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={showErrors}
          onChange={(e) => onToggle(e.target.checked)}
          className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-cyan-600 focus:ring-cyan-500"
        />
        <span className="text-sm text-gray-300">Show Error Overlay</span>
      </label>
      {showErrors && (
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500/30 border border-green-500"></div>
            <span>Under-predicted</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500/30 border border-red-500"></div>
            <span>Over-predicted</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default ErrorOverlay

