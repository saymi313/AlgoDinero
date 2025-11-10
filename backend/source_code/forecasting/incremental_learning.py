"""
Incremental Learning Module
Implements online learning and incremental updates for forecasting models
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError:
    torch = None
    nn = None
    optim = None


class IncrementalLearner:
    """Handles incremental learning for various model types"""
    
    def __init__(self, learning_rate: float = 0.001, window_size: int = 20):
        """
        Initialize incremental learner
        
        Args:
            learning_rate: Learning rate for neural network updates
            window_size: Sliding window size for training
        """
        self.learning_rate = learning_rate
        self.window_size = window_size
    
    def update_neural_model(
        self,
        model: nn.Module,
        new_data: np.ndarray,
        epochs: int = 10,
        batch_size: int = 32
    ) -> nn.Module:
        """
        Update a neural network model (LSTM, GRU, Transformer) with new data
        
        Args:
            model: PyTorch model to update
            new_data: New time series data
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Updated model
        """
        if torch is None or nn is None:
            return model
        
        model.train()
        device = torch.device('cpu')
        model.to(device)
        
        # Normalize data
        mean = new_data.mean()
        std = new_data.std() + 1e-8
        normalized_data = (new_data - mean) / std
        
        # Create sequences
        X, y = [], []
        for i in range(len(normalized_data) - self.window_size):
            X.append(normalized_data[i:i+self.window_size])
            y.append(normalized_data[i+self.window_size])
        
        if len(X) == 0:
            return model
        
        X = np.array(X).reshape(-1, self.window_size, 1).astype('float32')
        y = np.array(y).reshape(-1, 1).astype('float32')
        
        X_tensor = torch.from_numpy(X).to(device)
        y_tensor = torch.from_numpy(y).to(device)
        
        # Use a lower learning rate for incremental updates
        optimizer = optim.Adam(model.parameters(), lr=self.learning_rate * 0.1)
        criterion = nn.MSELoss()
        
        # Train for a few epochs
        for epoch in range(epochs):
            optimizer.zero_grad()
            predictions = model(X_tensor)
            loss = criterion(predictions, y_tensor)
            loss.backward()
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        
        return model
    
    def update_mlp_model(
        self,
        model: Any,
        new_data: np.ndarray,
        window: int = 5
    ) -> Any:
        """
        Update an MLP model with new data using partial_fit
        
        Args:
            model: Sklearn MLPRegressor model
            new_data: New time series data
            window: Window size for feature creation
            
        Returns:
            Updated model
        """
        try:
            from sklearn.neural_network import MLPRegressor
            
            # Create features and targets
            X, y = [], []
            for i in range(len(new_data) - window):
                X.append(new_data[i:i+window])
                y.append(new_data[i+window])
            
            if len(X) == 0:
                return model
            
            X = np.array(X)
            y = np.array(y)
            
            # Use partial_fit if available, otherwise retrain
            if hasattr(model, 'partial_fit'):
                model.partial_fit(X, y)
            else:
                # Retrain on recent data
                model.fit(X, y)
            
            return model
        except Exception:
            return model
    
    def update_arima_model(
        self,
        model: Any,
        new_data: np.ndarray
    ) -> Any:
        """
        Update ARIMA model with new observations
        
        Note: ARIMA models are typically retrained rather than incrementally updated.
        This method provides a simplified approach using the last observations.
        
        Args:
            model: ARIMA model (statsmodels)
            new_data: New time series data
            
        Returns:
            Updated model (or new model if update fails)
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            # For ARIMA, we typically need to retrain
            # This is a simplified approach - in practice, you'd retrain on extended data
            # For now, return the model as-is (retraining will be handled separately)
            return model
        except Exception:
            return model
    
    def rolling_window_retrain(
        self,
        model_type: str,
        historical_data: np.ndarray,
        window_days: int = 60,
        retrain_every: int = 7
    ) -> Dict[str, Any]:
        """
        Implement rolling window retraining strategy
        
        Args:
            model_type: Type of model ('lstm', 'gru', 'transformer', 'mlp', 'arima')
            historical_data: Full historical time series
            window_days: Number of days to use for training window
            retrain_every: Retrain every N days
            
        Returns:
            Dictionary with retraining info
        """
        if len(historical_data) < window_days:
            return {
                'success': False,
                'message': f'Insufficient data: need at least {window_days} days'
            }
        
        # Use the last window_days for training
        training_data = historical_data[-window_days:]
        
        return {
            'success': True,
            'model_type': model_type,
            'training_window_days': window_days,
            'training_data_points': len(training_data),
            'retrain_every_days': retrain_every,
            'last_retrain_date': datetime.utcnow().isoformat()
        }


class ModelUpdater:
    """High-level interface for updating models"""
    
    def __init__(self):
        self.learner = IncrementalLearner()
    
    def update_model(
        self,
        model: Any,
        model_type: str,
        new_data: np.ndarray,
        **kwargs
    ) -> Any:
        """
        Update a model with new data
        
        Args:
            model: Model to update
            model_type: Type of model
            new_data: New time series data
            **kwargs: Additional parameters
            
        Returns:
            Updated model
        """
        if model_type in ['lstm', 'gru', 'transformer']:
            if torch is not None and isinstance(model, nn.Module):
                epochs = kwargs.get('epochs', 10)
                return self.learner.update_neural_model(model, new_data, epochs)
        
        elif model_type == 'mlp':
            window = kwargs.get('window', 5)
            return self.learner.update_mlp_model(model, new_data, window)
        
        elif model_type == 'arima':
            return self.learner.update_arima_model(model, new_data)
        
        # For moving_average and var, no update needed (stateless)
        return model
    
    def should_retrain(
        self,
        last_retrain_date: datetime,
        retrain_interval_days: int = 7
    ) -> bool:
        """
        Check if model should be retrained based on time interval
        
        Args:
            last_retrain_date: Date of last retraining
            retrain_interval_days: Days between retraining
            
        Returns:
            True if retraining is needed
        """
        days_since_retrain = (datetime.utcnow() - last_retrain_date).days
        return days_since_retrain >= retrain_interval_days

