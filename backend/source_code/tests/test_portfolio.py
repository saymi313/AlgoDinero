"""
Tests for portfolio management functionality
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio.portfolio_manager import PortfolioManager
from portfolio.trading_strategy import TradingStrategy
from portfolio.performance_metrics import PerformanceMetrics


class TestPortfolio(unittest.TestCase):
    """Test portfolio management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.portfolio_manager = PortfolioManager(initial_cash=100000.0)
        self.strategy = TradingStrategy()
        self.metrics = PerformanceMetrics()
    
    def test_create_portfolio(self):
        """Test portfolio creation"""
        portfolio = self.portfolio_manager.create_portfolio()
        
        self.assertIn('portfolio_id', portfolio)
        self.assertEqual(portfolio['cash'], 100000.0)
        self.assertEqual(portfolio['initial_value'], 100000.0)
        self.assertIn('holdings', portfolio)
    
    def test_trading_strategy_signal(self):
        """Test trading signal generation"""
        signal = self.strategy.generate_signal(
            current_price=100.0,
            predicted_price=103.0,  # 3% increase
            current_holdings={'quantity': 0}
        )
        
        self.assertIn('action', signal)
        self.assertIn('reason', signal)
        self.assertEqual(signal['action'], 'buy')
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        returns = self.metrics.calculate_returns(100000.0, 110000.0, days=365)
        
        self.assertIn('total_return', returns)
        self.assertIn('total_return_pct', returns)
        self.assertEqual(returns['total_return_pct'], 10.0)
    
    def test_volatility_calculation(self):
        """Test volatility calculation"""
        returns = [0.01, -0.02, 0.015, -0.01, 0.02]
        volatility = self.metrics.calculate_volatility(returns)
        
        self.assertIsInstance(volatility, float)
        self.assertGreaterEqual(volatility, 0)
    
    def test_portfolio_execute_trade(self):
        """Test executing a trade"""
        portfolio = self.portfolio_manager.create_portfolio()
        portfolio_id = portfolio['portfolio_id']
        
        result = self.portfolio_manager.execute_trade(
            portfolio_id=portfolio_id,
            ticker='AAPL',
            action='buy',
            quantity=10,
            price=150.0
        )
        
        self.assertTrue(result['success'])
        self.assertIn('transaction_id', result)
    
    def test_trading_strategy_edge_cases(self):
        """Test trading strategy with edge cases"""
        # No change in price
        signal = self.strategy.generate_signal(
            current_price=100.0,
            predicted_price=100.0,
            current_holdings={'quantity': 0}
        )
        self.assertEqual(signal['action'], 'hold')
        
        # Small change (below threshold)
        signal = self.strategy.generate_signal(
            current_price=100.0,
            predicted_price=100.5,  # 0.5% increase (below 1% threshold)
            current_holdings={'quantity': 0}
        )
        self.assertEqual(signal['action'], 'hold')
    
    def test_performance_metrics_edge_cases(self):
        """Test performance metrics with edge cases"""
        # Zero initial value
        returns = self.metrics.calculate_returns(0.0, 1000.0, days=365)
        self.assertIn('total_return', returns)
        
        # Negative return
        returns = self.metrics.calculate_returns(100000.0, 90000.0, days=365)
        self.assertLess(returns['total_return_pct'], 0)
        
        # Empty returns list
        volatility = self.metrics.calculate_volatility([])
        self.assertEqual(volatility, 0.0)
        
        # Single return value
        volatility = self.metrics.calculate_volatility([0.01])
        self.assertEqual(volatility, 0.0)


if __name__ == '__main__':
    unittest.main()

