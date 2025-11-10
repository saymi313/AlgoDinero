"""
Trading Strategy
Simple signal-based trading strategy using forecast predictions
"""

from typing import Dict, Any, Optional
from datetime import datetime


class TradingStrategy:
    """Simple signal-based trading strategy"""
    
    def __init__(
        self,
        buy_threshold: float = 0.02,  # 2% predicted increase
        sell_threshold: float = -0.02,  # 2% predicted decrease
        position_size_pct: float = 0.1  # 10% of portfolio per trade
    ):
        """
        Initialize trading strategy
        
        Args:
            buy_threshold: Minimum predicted price increase to buy (as decimal)
            sell_threshold: Maximum predicted price decrease to sell (as decimal)
            position_size_pct: Position size as percentage of portfolio
        """
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.position_size_pct = position_size_pct
    
    def generate_signal(
        self,
        current_price: float,
        predicted_price: float,
        current_holdings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trading signal based on prediction
        
        Args:
            current_price: Current market price
            predicted_price: Predicted future price
            current_holdings: Current portfolio holdings for this ticker
            
        Returns:
            Dictionary with trading signal
        """
        if current_price == 0:
            return {
                'action': 'hold',
                'reason': 'Invalid current price'
            }
        
        # Calculate predicted return
        predicted_return = (predicted_price - current_price) / current_price
        
        # Determine action
        if predicted_return >= self.buy_threshold:
            action = 'buy'
            reason = f'Predicted increase: {predicted_return*100:.2f}%'
        elif predicted_return <= self.sell_threshold:
            action = 'sell'
            reason = f'Predicted decrease: {predicted_return*100:.2f}%'
        else:
            action = 'hold'
            reason = f'Predicted change: {predicted_return*100:.2f}% (within thresholds)'
        
        return {
            'action': action,
            'reason': reason,
            'predicted_return': float(predicted_return),
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'confidence': abs(predicted_return)  # Higher absolute return = higher confidence
        }
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        ticker: str,
        price: float
    ) -> Dict[str, Any]:
        """
        Calculate position size for a trade
        
        Args:
            portfolio_value: Total portfolio value
            ticker: Ticker symbol
            price: Current price
            
        Returns:
            Dictionary with position size details
        """
        position_value = portfolio_value * self.position_size_pct
        shares = (position_value / price) if price > 0 else 0.0  # Changed to float to support decimal quantities (e.g., 0.5 Bitcoin)
        actual_value = shares * price
        
        return {
            'ticker': ticker,
            'shares': float(shares),  # Return as float to support decimal quantities
            'price': float(price),
            'value': float(actual_value),
            'position_size_pct': self.position_size_pct
        }
    
    def should_execute_trade(
        self,
        signal: Dict[str, Any],
        current_holdings: Dict[str, Any]
    ) -> bool:
        """
        Determine if trade should be executed based on signal and current holdings
        
        Args:
            signal: Trading signal from generate_signal
            current_holdings: Current holdings for the ticker
            
        Returns:
            True if trade should be executed
        """
        action = signal.get('action', 'hold')
        
        if action == 'hold':
            return False
        
        # Don't buy if already holding
        if action == 'buy' and current_holdings.get('quantity', 0) > 0:
            return False
        
        # Don't sell if not holding
        if action == 'sell' and current_holdings.get('quantity', 0) == 0:
            return False
        
        return True

