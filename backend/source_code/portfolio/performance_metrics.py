"""
Portfolio Performance Metrics
Calculates portfolio returns, volatility, Sharpe ratio, and compares with baseline
"""

from typing import Dict, Any, List
import numpy as np
from datetime import datetime


class PerformanceMetrics:
    """Calculates portfolio performance metrics"""
    
    def __init__(self):
        """Initialize performance metrics calculator"""
        pass
    
    def calculate_returns(
        self,
        initial_value: float,
        current_value: float,
        days: int = 1
    ) -> Dict[str, float]:
        """
        Calculate portfolio returns
        
        Args:
            initial_value: Initial portfolio value
            current_value: Current portfolio value
            days: Number of days (for annualization)
            
        Returns:
            Dictionary with return metrics
        """
        if initial_value == 0:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'annualized_return': 0.0,
                'daily_return': 0.0
            }
        
        total_return = current_value - initial_value
        total_return_pct = (total_return / initial_value) * 100
        
        # Annualized return
        if days > 0:
            annualized_return = ((current_value / initial_value) ** (365.0 / days) - 1) * 100
            daily_return = total_return_pct / days
        else:
            annualized_return = 0.0
            daily_return = 0.0
        
        return {
            'total_return': float(total_return),
            'total_return_pct': float(total_return_pct),
            'annualized_return': float(annualized_return),
            'daily_return': float(daily_return)
        }
    
    def calculate_volatility(
        self,
        returns: List[float]
    ) -> float:
        """
        Calculate portfolio volatility (standard deviation of returns)
        
        Args:
            returns: List of daily returns
            
        Returns:
            Volatility as float
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        volatility = float(np.std(returns_array))
        
        # Annualized volatility
        annualized_volatility = volatility * np.sqrt(252)  # Trading days
        
        return float(annualized_volatility)
    
    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02  # 2% annual risk-free rate
    ) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns: List of daily returns
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        
        # Average return
        avg_return = np.mean(returns_array)
        
        # Annualized return
        annualized_return = avg_return * 252
        
        # Volatility
        volatility = np.std(returns_array)
        annualized_volatility = volatility * np.sqrt(252)
        
        if annualized_volatility == 0:
            return 0.0
        
        # Sharpe ratio = (Return - Risk-free rate) / Volatility
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
        
        return float(sharpe_ratio)
    
    def compare_with_baseline(
        self,
        portfolio_returns: List[float],
        baseline_returns: List[float]
    ) -> Dict[str, Any]:
        """
        Compare portfolio performance with buy-and-hold baseline
        
        Args:
            portfolio_returns: Portfolio daily returns
            baseline_returns: Buy-and-hold baseline returns
            
        Returns:
            Comparison metrics
        """
        if not portfolio_returns or not baseline_returns:
            return {
                'portfolio_total_return': 0.0,
                'baseline_total_return': 0.0,
                'outperformance': 0.0,
                'outperformance_pct': 0.0
            }
        
        # Calculate cumulative returns
        portfolio_cumulative = (1 + np.array(portfolio_returns)).prod() - 1
        baseline_cumulative = (1 + np.array(baseline_returns)).prod() - 1
        
        outperformance = portfolio_cumulative - baseline_cumulative
        outperformance_pct = (outperformance / baseline_cumulative * 100) if baseline_cumulative != 0 else 0.0
        
        return {
            'portfolio_total_return': float(portfolio_cumulative),
            'baseline_total_return': float(baseline_cumulative),
            'outperformance': float(outperformance),
            'outperformance_pct': float(outperformance_pct)
        }
    
    def calculate_all_metrics(
        self,
        portfolio_history: List[Dict[str, Any]],
        initial_value: float
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics for a portfolio
        
        Args:
            portfolio_history: List of portfolio value snapshots over time
            initial_value: Initial portfolio value
            
        Returns:
            Dictionary with all performance metrics
        """
        if not portfolio_history or len(portfolio_history) < 2:
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'current_value': initial_value
            }
        
        # Extract values and calculate returns
        values = [entry.get('value', initial_value) for entry in portfolio_history]
        current_value = values[-1]
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                daily_return = (values[i] - values[i-1]) / values[i-1]
                returns.append(daily_return)
        
        # Calculate metrics
        return_metrics = self.calculate_returns(initial_value, current_value, len(portfolio_history))
        volatility = self.calculate_volatility(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        return {
            **return_metrics,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'current_value': float(current_value),
            'initial_value': float(initial_value),
            'days': len(portfolio_history)
        }

