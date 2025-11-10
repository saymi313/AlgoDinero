"""
Portfolio Manager
Manages portfolio holdings, transactions, and trading operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .trading_strategy import TradingStrategy
from .performance_metrics import PerformanceMetrics
from database.mongo_connector import MongoConnector


class PortfolioManager:
    """Manages financial portfolio operations"""
    
    def __init__(self, initial_cash: float = 100000.0):
        """
        Initialize portfolio manager
        
        Args:
            initial_cash: Initial cash amount
        """
        self.initial_cash = initial_cash
        self.strategy = TradingStrategy()
        self.metrics = PerformanceMetrics()
        self.mongo = MongoConnector()
    
    def create_portfolio(
        self,
        portfolio_id: Optional[str] = None,
        initial_cash: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a new portfolio
        
        Args:
            portfolio_id: Optional portfolio ID (generated if not provided)
            initial_cash: Initial cash amount
            
        Returns:
            Portfolio data dictionary
        """
        if portfolio_id is None:
            portfolio_id = str(uuid.uuid4())
        
        if initial_cash is None:
            initial_cash = self.initial_cash
        
        portfolio = {
            'portfolio_id': portfolio_id,
            'cash': float(initial_cash),
            'holdings': {},  # {ticker: {'quantity': float, 'avg_price': float}}  # quantity is float to support decimal quantities (e.g., 0.5 Bitcoin)
            'total_value': float(initial_cash),
            'initial_value': float(initial_cash),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Save to MongoDB (non-blocking - don't fail if MongoDB is unavailable)
        try:
            self.mongo.save_portfolio(portfolio)
        except Exception as e:
            # Log but don't fail portfolio creation if MongoDB save fails
            print(f"Warning: Could not save portfolio to MongoDB: {e}")
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: str, skip_price_fetch: bool = False) -> Dict[str, Any]:
        """Get portfolio by ID"""
        portfolio = self.mongo.get_portfolio(portfolio_id)
        
        if not portfolio:
            return {}
        
        # Calculate current total value (skip price fetch for faster response)
        portfolio = self._update_portfolio_value(portfolio, skip_price_fetch=skip_price_fetch)
        
        return portfolio
    
    def _update_portfolio_value(self, portfolio: Dict[str, Any], skip_price_fetch: bool = False) -> Dict[str, Any]:
        """Update portfolio total value based on current holdings"""
        try:
            total_value = float(portfolio.get('cash', 0.0))
            holdings = dict(portfolio.get('holdings', {}))  # Create copy to avoid reference issues
            
            # If skip_price_fetch is True, use avg_price for holdings value (faster)
            if skip_price_fetch:
                for ticker, holding in holdings.items():
                    quantity = holding.get('quantity', 0)
                    if quantity > 0:
                        avg_price = float(holding.get('avg_price', 0.0))
                        holdings[ticker] = {
                            'quantity': quantity,
                            'avg_price': avg_price,
                            'current_price': avg_price,
                            'value': float(quantity * avg_price)
                        }
                        total_value += holdings[ticker]['value']
            else:
                # Only fetch prices if we have holdings and not skipping
                if holdings:
                    from price_fetcher import PriceFetcher
                    fetcher = PriceFetcher()
                    
                    for ticker, holding in holdings.items():
                        quantity = holding.get('quantity', 0)
                        if quantity > 0:
                            # Get current price with timeout protection
                            try:
                                # Use minimal days (1) for faster fetch
                                price_df = fetcher.fetch_historical_prices(ticker, 1)
                                if not price_df.empty and len(price_df) > 0:
                                    current_price = float(price_df['Close'].iloc[-1])
                                    avg_price = float(holding.get('avg_price', current_price))
                                    holdings[ticker] = {
                                        'quantity': quantity,
                                        'avg_price': avg_price,
                                        'current_price': current_price,
                                        'value': float(quantity * current_price)
                                    }
                                    total_value += holdings[ticker]['value']
                                else:
                                    # Fallback to avg_price if fetch returns empty
                                    avg_price = float(holding.get('avg_price', 0.0))
                                    holdings[ticker] = {
                                        'quantity': quantity,
                                        'avg_price': avg_price,
                                        'current_price': avg_price,
                                        'value': float(quantity * avg_price)
                                    }
                                    total_value += holdings[ticker]['value']
                            except Exception as e:
                                # If price fetch fails, use last known price or avg_price
                                print(f"Warning: Could not fetch price for {ticker}: {e}")
                                avg_price = float(holding.get('avg_price', 0.0))
                                holdings[ticker] = {
                                    'quantity': quantity,
                                    'avg_price': avg_price,
                                    'current_price': avg_price,
                                    'value': float(quantity * avg_price)
                                }
                                total_value += holdings[ticker]['value']
            
            # Ensure holdings are set back in portfolio
            portfolio['holdings'] = holdings
            portfolio['total_value'] = float(total_value)
            portfolio['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated portfolio to MongoDB (non-blocking)
            try:
                self.mongo.save_portfolio(portfolio)
            except Exception:
                pass  # Don't fail if save fails
            
        except Exception as e:
            print(f"Error updating portfolio value: {e}")
            import traceback
            traceback.print_exc()
        
        return portfolio
    
    def execute_trade(
        self,
        portfolio_id: str,
        ticker: str,
        action: str,  # 'buy' or 'sell'
        quantity: Optional[float] = None,  # Changed to float to support decimal quantities
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Ticker symbol
            action: 'buy' or 'sell'
            quantity: Number of shares (calculated if None)
            price: Price per share (fetched if None)
            
        Returns:
            Transaction result
        """
        # Get portfolio - use skip_price_fetch=True for faster retrieval during trade
        portfolio = self.get_portfolio(portfolio_id, skip_price_fetch=True)
        
        if not portfolio or not portfolio.get('portfolio_id'):
            return {
                'success': False,
                'message': 'Portfolio not found'
            }
        
        # Get current price if not provided
        if price is None:
            try:
                from price_fetcher import PriceFetcher
                fetcher = PriceFetcher()
                price_df = fetcher.fetch_historical_prices(ticker, 1)
                if price_df.empty:
                    return {'success': False, 'message': 'Could not fetch current price'}
                price = float(price_df['Close'].iloc[-1])
            except Exception as e:
                return {'success': False, 'message': f'Error fetching price: {str(e)}'}
        
        holdings = portfolio.get('holdings', {})
        current_holding = holdings.get(ticker, {'quantity': 0, 'avg_price': 0.0})
        cash = portfolio.get('cash', 0.0)
        
        if action == 'buy':
            # Calculate quantity if not provided
            if quantity is None:
                position_info = self.strategy.calculate_position_size(
                    portfolio.get('total_value', cash),
                    ticker,
                    price
                )
                quantity = position_info['shares']
            
            total_cost = quantity * price
            
            if cash < total_cost:
                return {
                    'success': False,
                    'message': f'Insufficient cash. Need ${total_cost:.2f}, have ${cash:.2f}'
                }
            
            # Update holdings
            current_quantity = current_holding.get('quantity', 0)
            current_avg_price = current_holding.get('avg_price', 0.0)
            
            new_quantity = current_quantity + quantity
            if new_quantity > 0:
                new_avg_price = ((current_quantity * current_avg_price) + total_cost) / new_quantity
            else:
                new_avg_price = price
            
            holdings[ticker] = {
                'quantity': new_quantity,
                'avg_price': float(new_avg_price)
            }
            
            cash -= total_cost
            
        elif action == 'sell':
            current_quantity = current_holding.get('quantity', 0)
            
            if quantity is None:
                quantity = current_quantity  # Sell all
            
            if current_quantity < quantity:
                return {
                    'success': False,
                    'message': f'Insufficient holdings. Have {current_quantity}, trying to sell {quantity}'
                }
            
            total_proceeds = quantity * price
            
            # Update holdings
            new_quantity = current_quantity - quantity
            if new_quantity > 0:
                holdings[ticker] = {
                    'quantity': new_quantity,
                    'avg_price': current_holding.get('avg_price', price)
                }
            else:
                holdings.pop(ticker, None)
            
            cash += total_proceeds
        
        else:
            return {'success': False, 'message': f'Invalid action: {action}'}
        
        # Update portfolio - ensure we create new dict to avoid reference issues
        portfolio['cash'] = float(cash)
        portfolio['holdings'] = dict(holdings)  # Create new dict copy
        portfolio = self._update_portfolio_value(portfolio, skip_price_fetch=True)  # Skip price fetch for faster save
        
        # Save transaction
        transaction = {
            'portfolio_id': portfolio_id,
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': float(price),
            'value': float(quantity * price),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save transaction first
        try:
            self.mongo.save_transaction(transaction)
        except Exception as e:
            print(f"Warning: Failed to save transaction: {e}")
        
        # Save portfolio - ensure it's saved before returning
        try:
            saved_id = self.mongo.save_portfolio(portfolio)
            if not saved_id:
                print(f"Warning: Portfolio save returned empty ID - MongoDB may not be connected")
        except Exception as e:
            print(f"Warning: Failed to save portfolio: {e}")
        
        # Verify portfolio was updated correctly
        print(f"Trade executed: {action} {quantity} {ticker} @ ${price}")
        print(f"Portfolio after trade - Cash: ${portfolio.get('cash', 0):.2f}, Holdings: {portfolio.get('holdings', {})}, Total Value: ${portfolio.get('total_value', 0):.2f}")
        
        # Ensure portfolio dict is clean (no ObjectId or other MongoDB-specific types)
        # Make sure holdings is properly formatted
        holdings_dict = {}
        for ticker_key, holding_data in portfolio.get('holdings', {}).items():
            holdings_dict[ticker_key] = {
                'quantity': float(holding_data.get('quantity', 0)),  # Changed to float to support decimal quantities
                'avg_price': float(holding_data.get('avg_price', 0.0)),
                'current_price': float(holding_data.get('current_price', holding_data.get('avg_price', 0.0))),
                'value': float(holding_data.get('value', 0.0))
            }
        
        clean_portfolio = {
            'portfolio_id': portfolio.get('portfolio_id'),
            'cash': float(portfolio.get('cash', 0)),
            'holdings': holdings_dict,  # Use cleaned holdings dict
            'total_value': float(portfolio.get('total_value', 0)),
            'initial_value': float(portfolio.get('initial_value', 0)),
            'created_at': portfolio.get('created_at'),
            'updated_at': portfolio.get('updated_at')
        }
        
        print(f"Returning clean portfolio - Holdings keys: {list(clean_portfolio['holdings'].keys())}, Holdings: {clean_portfolio['holdings']}")
        
        return {
            'success': True,
            'transaction': transaction,
            'portfolio': clean_portfolio,
            'message': f'Successfully {action} {quantity} shares of {ticker} at ${price:.2f}'
        }
    
    def trade_based_on_prediction(
        self,
        portfolio_id: str,
        ticker: str,
        predicted_price: float,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute trade based on prediction signal
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Ticker symbol
            predicted_price: Predicted future price
            current_price: Current price (fetched if None)
            
        Returns:
            Trade execution result
        """
        portfolio = self.get_portfolio(portfolio_id)
        
        if not portfolio:
            return {'success': False, 'message': 'Portfolio not found'}
        
        # Get current price
        if current_price is None:
            try:
                from price_fetcher import PriceFetcher
                fetcher = PriceFetcher()
                price_df = fetcher.fetch_historical_prices(ticker, 1)
                if price_df.empty:
                    return {'success': False, 'message': 'Could not fetch current price'}
                current_price = float(price_df['Close'].iloc[-1])
            except Exception as e:
                return {'success': False, 'message': f'Error fetching price: {str(e)}'}
        
        # Get current holdings
        holdings = portfolio.get('holdings', {})
        current_holding = holdings.get(ticker, {'quantity': 0})
        
        # Generate signal
        signal = self.strategy.generate_signal(
            current_price,
            predicted_price,
            current_holding
        )
        
        # Check if should execute
        if not self.strategy.should_execute_trade(signal, current_holding):
            return {
                'success': True,
                'action': 'hold',
                'signal': signal,
                'message': 'No trade executed based on signal'
            }
        
        # Execute trade
        action = signal.get('action')
        result = self.execute_trade(portfolio_id, ticker, action, price=current_price)
        
        if result.get('success'):
            result['signal'] = signal
        
        return result
    
    def get_portfolio_performance(
        self,
        portfolio_id: str
    ) -> Dict[str, Any]:
        """
        Get portfolio performance metrics
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Performance metrics
        """
        portfolio = self.get_portfolio(portfolio_id, skip_price_fetch=False)  # Get current prices
        
        if not portfolio:
            return {'success': False, 'message': 'Portfolio not found'}
        
        # Get transaction history
        transactions = self.mongo.get_transactions(portfolio_id, limit=1000)
        
        # Build portfolio history by reconstructing portfolio state at each transaction
        portfolio_history = []
        initial_value = portfolio.get('initial_value', portfolio.get('total_value', 100000))
        
        # Add initial point
        portfolio_history.append({
            'date': portfolio.get('created_at', datetime.utcnow().isoformat()),
            'value': initial_value
        })
        
        # Sort transactions by date
        sorted_transactions = sorted(
            transactions,
            key=lambda x: x.get('timestamp') or x.get('created_at', '')
        )
        
        # Reconstruct portfolio state at each transaction point
        # This gives us the actual portfolio value at each point in time
        cash = initial_value
        holdings = {}  # {ticker: {'quantity': float, 'avg_price': float}}  # quantity is float to support decimal quantities
        
        for transaction in sorted_transactions:
            tx_date = transaction.get('timestamp') or transaction.get('created_at')
            if not tx_date:
                continue
            
            ticker = transaction.get('ticker')
            action = transaction.get('action')
            quantity = transaction.get('quantity', 0)
            price = transaction.get('price', 0.0)
            value = transaction.get('value', quantity * price)
            
            # Update holdings based on transaction
            if action == 'buy':
                cash -= value
                if ticker not in holdings:
                    holdings[ticker] = {'quantity': 0, 'avg_price': 0.0}
                current_qty = holdings[ticker]['quantity']
                current_avg = holdings[ticker]['avg_price']
                new_qty = current_qty + quantity
                if new_qty > 0:
                    new_avg = ((current_qty * current_avg) + value) / new_qty
                else:
                    new_avg = price
                holdings[ticker] = {'quantity': new_qty, 'avg_price': new_avg}
            elif action == 'sell':
                cash += value
                if ticker in holdings:
                    holdings[ticker]['quantity'] -= quantity
                    if holdings[ticker]['quantity'] <= 0:
                        holdings.pop(ticker, None)
            
            # Calculate portfolio value at this point
            # For historical accuracy, use transaction price for the traded ticker
            # For other holdings, use their avg_price (best estimate at that time)
            portfolio_value = cash
            for tick, holding in holdings.items():
                qty = holding.get('quantity', 0)
                if qty > 0:
                    # Use transaction price if it's for this ticker (most accurate)
                    # Otherwise use avg_price as best estimate
                    if tick == ticker:
                        current_price = price
                    else:
                        current_price = holding.get('avg_price', 0.0)
                    portfolio_value += qty * current_price
            
            portfolio_history.append({
                'date': tx_date,
                'value': portfolio_value
            })
        
        # Add current value (with updated holdings valuation from get_portfolio)
        # This uses current market prices, so it reflects actual gains/losses
        final_value = portfolio.get('total_value', initial_value)
        
        # Only add current point if it's different from the last transaction point
        # or if there are no transactions (to show initial state)
        if len(portfolio_history) == 0 or portfolio_history[-1]['value'] != final_value:
            portfolio_history.append({
                'date': datetime.utcnow().isoformat(),
                'value': final_value
            })
        
        # Calculate metrics - always calculate even with 1 data point (just show current vs initial)
        # For proper metrics, we need at least 2 points, but we can still show total return
        if len(portfolio_history) < 2:
            # Single data point - calculate simple return
            total_return = final_value - initial_value
            total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0.0
            
            # Calculate days since creation
            try:
                created_date = datetime.fromisoformat(portfolio.get('created_at', datetime.utcnow().isoformat()).replace('Z', '+00:00'))
                days = max(1, (datetime.utcnow() - created_date.replace(tzinfo=None)).days)
            except:
                days = 1
            
            # Annualized return
            if days > 0 and initial_value > 0:
                annualized_return = ((final_value / initial_value) ** (365.0 / days) - 1) * 100
            else:
                annualized_return = 0.0
            
            metrics = {
                'total_return': float(total_return),
                'total_return_pct': float(total_return_pct),
                'annualized_return': float(annualized_return),
                'daily_return': float(total_return_pct / days) if days > 0 else 0.0,
                'volatility': 0.0,  # Need at least 2 points for volatility
                'sharpe_ratio': 0.0,  # Need at least 2 points for Sharpe
                'current_value': float(final_value),
                'initial_value': float(initial_value),
                'days': days
            }
        else:
            # Multiple data points - use full metrics calculation
            metrics = self.metrics.calculate_all_metrics(
                portfolio_history,
                initial_value
            )
            # Ensure current_value is set correctly
            metrics['current_value'] = float(final_value)
            metrics['initial_value'] = float(initial_value)
        
        print(f"Performance metrics for {portfolio_id}: Total Return: {metrics.get('total_return_pct', 0):.2f}%, Current Value: ${metrics.get('current_value', 0):.2f}, Initial Value: ${metrics.get('initial_value', 0):.2f}")
        
        return {
            'success': True,
            'portfolio_id': portfolio_id,
            'metrics': metrics,
            'portfolio': portfolio,
            'history': portfolio_history  # Include history in response
        }

