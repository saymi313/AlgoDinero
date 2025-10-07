#!/usr/bin/env python3
"""
Script to train and upload FinTech forecasting models to Hugging Face Hub
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from pathlib import Path

# Add the source_code directory to the path
sys.path.append(str(Path(__file__).parent))

from huggingface_hub import HfApi, create_repo
from price_fetcher import PriceFetcher
from forecasting.model_neural import GRUForecaster, LSTMForecaster, TinyTransformer
from forecasting.model_traditional import moving_average_forecast, var_close_forecast

# Hugging Face credentials
HF_USERNAME = "usairamsaeed"
HF_TOKEN = "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"

def prepare_training_data():
    """Fetch and prepare training data for multiple stocks"""
    fetcher = PriceFetcher()
    
    # Train on multiple stocks for better generalization
    tickers = ['AAPL', 'TSLA', 'BTC-USD', 'ETH-USD', 'MSFT', 'GOOGL']
    all_data = []
    
    print("Fetching training data...")
    for ticker in tickers:
        try:
            df = fetcher.fetch_historical_prices(ticker, 365)  # 1 year of data
            if df is not None and len(df) > 50:
                df['ticker'] = ticker
                all_data.append(df[['Date', 'Close', 'ticker']])
                print(f"✓ {ticker}: {len(df)} days")
        except Exception as e:
            print(f"✗ {ticker}: {e}")
    
    if not all_data:
        raise ValueError("No training data available")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df

def train_gru_model(data_df):
    """Train GRU model"""
    print("Training GRU model...")
    
    try:
        import torch
        import torch.nn as nn
        
        # Prepare data
        all_prices = []
        for ticker in data_df['ticker'].unique():
            ticker_data = data_df[data_df['ticker'] == ticker]['Close'].values
            if len(ticker_data) > 50:
                all_prices.extend(ticker_data)
        
        if len(all_prices) < 100:
            raise ValueError("Insufficient data for GRU training")
        
        y = np.array(all_prices)
        series = (y - y.mean()) / (y.std() + 1e-8)
        
        window = 20
        X, t = [], []
        for i in range(len(series) - window):
            X.append(series[i:i+window])
            t.append(series[i+window])
        
        X = np.array(X).reshape(-1, window, 1).astype('float32')
        t = np.array(t).reshape(-1, 1).astype('float32')
        
        device = torch.device('cpu')
        model = GRUForecaster()
        model.to(device)
        
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.MSELoss()
        
        X_t = torch.from_numpy(X).to(device)
        t_t = torch.from_numpy(t).to(device)
        
        # Train
        model.train()
        for epoch in range(100):
            opt.zero_grad()
            pred = model(X_t)
            loss = loss_fn(pred, t_t)
            loss.backward()
            opt.step()
            if epoch % 20 == 0:
                print(f"  Epoch {epoch}, Loss: {loss.item():.4f}")
        
        # Save model
        model.eval()
        model_data = {
            'model_state_dict': model.state_dict(),
            'mean': float(y.mean()),
            'std': float(y.std()),
            'window': window,
            'input_size': 1,
            'hidden_size': 32
        }
        
        return model_data, "gru"
        
    except ImportError:
        print("PyTorch not available, skipping GRU model")
        return None, "gru"
    except Exception as e:
        print(f"GRU training failed: {e}")
        return None, "gru"

def train_lstm_model(data_df):
    """Train LSTM model"""
    print("Training LSTM model...")
    
    try:
        import torch
        import torch.nn as nn
        
        # Prepare data
        all_prices = []
        for ticker in data_df['ticker'].unique():
            ticker_data = data_df[data_df['ticker'] == ticker]['Close'].values
            if len(ticker_data) > 50:
                all_prices.extend(ticker_data)
        
        if len(all_prices) < 100:
            raise ValueError("Insufficient data for LSTM training")
        
        y = np.array(all_prices)
        series = (y - y.mean()) / (y.std() + 1e-8)
        
        window = 20
        X, t = [], []
        for i in range(len(series) - window):
            X.append(series[i:i+window])
            t.append(series[i+window])
        
        X = np.array(X).reshape(-1, window, 1).astype('float32')
        t = np.array(t).reshape(-1, 1).astype('float32')
        
        device = torch.device('cpu')
        model = LSTMForecaster()
        model.to(device)
        
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.MSELoss()
        
        X_t = torch.from_numpy(X).to(device)
        t_t = torch.from_numpy(t).to(device)
        
        # Train
        model.train()
        for epoch in range(100):
            opt.zero_grad()
            pred = model(X_t)
            loss = loss_fn(pred, t_t)
            loss.backward()
            opt.step()
            if epoch % 20 == 0:
                print(f"  Epoch {epoch}, Loss: {loss.item():.4f}")
        
        # Save model
        model.eval()
        model_data = {
            'model_state_dict': model.state_dict(),
            'mean': float(y.mean()),
            'std': float(y.std()),
            'window': window,
            'input_size': 1,
            'hidden_size': 32
        }
        
        return model_data, "lstm"
        
    except ImportError:
        print("PyTorch not available, skipping LSTM model")
        return None, "lstm"
    except Exception as e:
        print(f"LSTM training failed: {e}")
        return None, "lstm"

def train_transformer_model(data_df):
    """Train Transformer model"""
    print("Training Transformer model...")
    
    try:
        import torch
        import torch.nn as nn
        
        # Prepare data
        all_prices = []
        for ticker in data_df['ticker'].unique():
            ticker_data = data_df[data_df['ticker'] == ticker]['Close'].values
            if len(ticker_data) > 50:
                all_prices.extend(ticker_data)
        
        if len(all_prices) < 100:
            raise ValueError("Insufficient data for Transformer training")
        
        y = np.array(all_prices)
        series = (y - y.mean()) / (y.std() + 1e-8)
        
        window = 24
        X, t = [], []
        for i in range(len(series) - window):
            X.append(series[i:i+window])
            t.append(series[i+window])
        
        X = np.array(X).reshape(-1, window, 1).astype('float32')
        t = np.array(t).reshape(-1, 1).astype('float32')
        
        device = torch.device('cpu')
        model = TinyTransformer()
        model.to(device)
        
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.MSELoss()
        
        X_t = torch.from_numpy(X).to(device)
        t_t = torch.from_numpy(t).to(device)
        
        # Train
        model.train()
        for epoch in range(120):
            opt.zero_grad()
            pred = model(X_t)
            loss = loss_fn(pred, t_t)
            loss.backward()
            opt.step()
            if epoch % 30 == 0:
                print(f"  Epoch {epoch}, Loss: {loss.item():.4f}")
        
        # Save model
        model.eval()
        model_data = {
            'model_state_dict': model.state_dict(),
            'mean': float(y.mean()),
            'std': float(y.std()),
            'window': window,
            'd_model': 32,
            'nhead': 4,
            'num_layers': 2
        }
        
        return model_data, "transformer"
        
    except ImportError:
        print("PyTorch not available, skipping Transformer model")
        return None, "transformer"
    except Exception as e:
        print(f"Transformer training failed: {e}")
        return None, "transformer"

def create_model_card(model_name, model_type):
    """Create model card content"""
    return f"""---
license: mit
tags:
- fintech
- forecasting
- time-series
- financial
- {model_type}
---

# {model_name.replace('_', ' ').title()} - Financial Time Series Forecasting Model

## Model Description

This is a {model_type.upper()} neural network model trained for financial time series forecasting. The model is part of the AlgoDinero FinTech Data Curation project and is designed to predict future stock prices and cryptocurrency values.

## Model Architecture

- **Model Type**: {model_type.upper()}
- **Input**: Time series of closing prices
- **Output**: Forecasted prices for future time steps
- **Training Data**: Multi-asset financial data (stocks and cryptocurrencies)

## Usage

```python
import torch
import numpy as np
from huggingface_hub import hf_hub_download

# Download model
model_path = hf_hub_download(repo_id="usairamsaeed/{model_name}", filename="model.pkl")

# Load model
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

# Use with your forecasting pipeline
```

## Training Details

- **Training Period**: 365 days of historical data
- **Assets**: AAPL, TSLA, BTC-USD, ETH-USD, MSFT, GOOGL
- **Data Preprocessing**: Normalized using z-score normalization
- **Training Method**: Adam optimizer with MSE loss

## Model Performance

This model is part of an ensemble forecasting system that combines multiple approaches:
- Moving Average
- ARIMA
- VAR
- MLP
- GRU
- LSTM  
- Transformer

The ensemble approach provides robust predictions by combining the strengths of different forecasting methods.

## Limitations

- Model performance depends on market conditions
- Historical performance does not guarantee future results
- Use for educational/research purposes
- Not intended for actual trading decisions

## Citation

```
@misc{{algoDinero{model_type.title()},
  title={{AlgoDinero {model_type.upper()} Financial Forecasting Model}},
  author={{Usair Ahmad Saeed}},
  year={{2025}},
  publisher={{Hugging Face}},
  howpublished={{\\url{{https://huggingface.co/usairamsaeed/{model_name}}}}}
}}
```
"""

def upload_model_to_hf(model_data, model_name, model_type):
    """Upload model to Hugging Face Hub"""
    if model_data is None:
        print(f"Skipping {model_name} - no model data")
        return
    
    print(f"Uploading {model_name} to Hugging Face...")
    
    try:
        api = HfApi(token=HF_TOKEN)
        
        # Create repository
        repo_id = f"{HF_USERNAME}/{model_name}"
        try:
            create_repo(repo_id=repo_id, token=HF_TOKEN, exist_ok=True)
            print(f"✓ Created repository: {repo_id}")
        except Exception as e:
            print(f"Repository might already exist: {e}")
        
        # Prepare files
        temp_dir = Path("temp_models")
        temp_dir.mkdir(exist_ok=True)
        
        # Save model
        model_file = temp_dir / "model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save model card
        card_content = create_model_card(model_name, model_type)
        card_file = temp_dir / "README.md"
        with open(card_file, 'w', encoding='utf-8') as f:
            f.write(card_content)
        
        # Upload files
        api.upload_folder(
            folder_path=temp_dir,
            repo_id=repo_id,
            token=HF_TOKEN,
            commit_message=f"Upload {model_name} model - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        print(f"✓ Successfully uploaded {model_name}")
        print(f"  Repository: https://huggingface.co/{repo_id}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"✗ Failed to upload {model_name}: {e}")

def main():
    """Main function to train and upload all models"""
    print("=== AlgoDinero Model Training and Upload ===")
    print(f"Username: {HF_USERNAME}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Prepare training data
    try:
        data_df = prepare_training_data()
        print(f"Total training samples: {len(data_df)}")
        print()
    except Exception as e:
        print(f"Failed to prepare training data: {e}")
        return
    
    # Train and upload models
    models_to_train = [
        (train_gru_model, "algoDinero_gru_forecaster", "gru"),
        (train_lstm_model, "algoDinero_lstm_forecaster", "lstm"),
        (train_transformer_model, "algoDinero_transformer_forecaster", "transformer")
    ]
    
    for train_func, model_name, model_type in models_to_train:
        try:
            model_data, _ = train_func(data_df)
            upload_model_to_hf(model_data, model_name, model_type)
            print()
        except Exception as e:
            print(f"Error processing {model_name}: {e}")
            print()
    
    print("=== Upload Complete ===")
    print("Models uploaded to:")
    print("- https://huggingface.co/usairamsaeed/algoDinero_gru_forecaster")
    print("- https://huggingface.co/usairamsaeed/algoDinero_lstm_forecaster") 
    print("- https://huggingface.co/usairamsaeed/algoDinero_transformer_forecaster")

if __name__ == "__main__":
    main()
