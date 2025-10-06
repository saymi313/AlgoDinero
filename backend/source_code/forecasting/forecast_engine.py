from pydantic import BaseModel
from typing import Dict, Any
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.neural_network import MLPRegressor
from .model_traditional import moving_average_forecast, var_close_forecast
from .model_neural import gru_forecast, lstm_forecast, transformer_forecast
from .evaluation import summarize_metrics


class ForecastRequest(BaseModel):
    ticker: str
    horizon: int = 24
    days: int = 120


class ForecastEngine:
    def run_forecast(self, req: ForecastRequest) -> Dict[str, Any]:
        hist_df = self._load_history(req.ticker, req.days)
        y = hist_df['Close'].values.astype(float)

        ma_forecast = moving_average_forecast(y, req.horizon)
        arima_forecast = self._arima(y, req.horizon)
        mlp_forecast = self._mlp(y, req.horizon)
        var_forecast = var_close_forecast(hist_df, req.horizon)
        gru_fc = gru_forecast(y, req.horizon)
        lstm_fc = lstm_forecast(y, req.horizon)
        tr_fc = transformer_forecast(y, req.horizon)

        ensemble = np.vstack([ma_forecast, arima_forecast, mlp_forecast, var_forecast, gru_fc, lstm_fc, tr_fc]).mean(axis=0)

        metrics = summarize_metrics({
            'moving_average': ma_forecast,
            'arima': arima_forecast,
            'mlp': mlp_forecast,
            'var': var_forecast,
            'gru': gru_fc,
            'lstm': lstm_fc,
            'transformer': tr_fc
        }, y)

        return {
            'ticker': req.ticker,
            'horizon': req.horizon,
            'predictions': ensemble.tolist(),
            'components': {
                'moving_average': ma_forecast.tolist(),
                'arima': arima_forecast.tolist(),
                'mlp': mlp_forecast.tolist(),
                'var': var_forecast.tolist(),
                'gru': gru_fc.tolist(),
                'lstm': lstm_fc.tolist(),
                'transformer': tr_fc.tolist()
            },
            'metrics': metrics
        }

    def get_visualization_data(self, hist_df: pd.DataFrame, ticker: str, horizon: int) -> Dict[str, Any]:
        y = hist_df['Close'].values.astype(float)
        ma_forecast = moving_average_forecast(y, horizon)
        arima_forecast = self._arima(y, horizon)
        mlp_forecast = self._mlp(y, horizon)
        var_forecast = var_close_forecast(hist_df, horizon)
        gru_fc = gru_forecast(y, horizon)
        lstm_fc = lstm_forecast(y, horizon)
        tr_fc = transformer_forecast(y, horizon)
        ensemble = np.vstack([ma_forecast, arima_forecast, mlp_forecast, var_forecast, gru_fc, lstm_fc, tr_fc]).mean(axis=0)

        hist = [
            {
                'date': str(d),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            }
            for d, row in hist_df.set_index('Date').iterrows()
        ]

        future_index = pd.date_range(hist_df['Date'].iloc[-1], periods=horizon+1, freq='D')[1:]
        forecast = [{ 'date': str(d.date()), 'close': float(c) } for d, c in zip(future_index, ensemble)]

        return { 'ticker': ticker, 'historical': hist, 'forecast': forecast, 'components': {
            'moving_average': ma_forecast.tolist(),
            'arima': arima_forecast.tolist(),
            'mlp': mlp_forecast.tolist(),
            'var': var_forecast.tolist(),
            'gru': gru_fc.tolist(),
            'lstm': lstm_fc.tolist(),
            'transformer': tr_fc.tolist()
        } }

    def _load_history(self, ticker: str, days: int) -> pd.DataFrame:
        from price_fetcher import PriceFetcher
        fetcher = PriceFetcher()
        return fetcher.fetch_historical_prices(ticker, days)

    def _arima(self, y: np.ndarray, horizon: int) -> np.ndarray:
        try:
            model = ARIMA(y, order=(1,1,1))
            fit = model.fit()
            fc = fit.forecast(steps=horizon)
            return np.array(fc)
        except Exception:
            return moving_average_forecast(y, horizon)

    def _mlp(self, y: np.ndarray, horizon: int) -> np.ndarray:
        try:
            X, t = [], []
            window = 5
            for i in range(len(y) - window):
                X.append(y[i:i+window])
                t.append(y[i+window])
            if len(X) < 5:
                return moving_average_forecast(y, horizon)
            model = MLPRegressor(hidden_layer_sizes=(32,16), max_iter=500, random_state=42)
            model.fit(np.array(X), np.array(t))
            seed = y[-window:].copy()
            out = []
            for _ in range(horizon):
                pred = float(model.predict(seed.reshape(1, -1))[0])
                out.append(pred)
                seed = np.roll(seed, -1)
                seed[-1] = pred
            return np.array(out)
        except Exception:
            return moving_average_forecast(y, horizon)



