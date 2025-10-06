from typing import Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.var_model import VAR


def moving_average_forecast(y: np.ndarray, horizon: int, window: int = 10) -> np.ndarray:
    window = min(window, len(y))
    avg = float(np.mean(y[-window:]))
    return np.full(horizon, avg, dtype=float)


def var_close_forecast(hist_df: pd.DataFrame, horizon: int) -> np.ndarray:
    """Fit a simple VAR model on OHLC and forecast Close for horizon.
    Falls back to moving average if fit fails or not enough data.
    """
    try:
        cols = ['Open', 'High', 'Low', 'Close']
        df = hist_df[cols].astype(float).dropna()
        if len(df) < 15:
            return moving_average_forecast(df['Close'].values, horizon)
        model = VAR(df)
        # small lag to reduce instability on short series
        fit = model.fit(maxlags=min(5, max(1, len(df)//10)))
        fc = fit.forecast(y=df.values[-fit.k_ar:], steps=horizon)
        close_idx = cols.index('Close')
        return fc[:, close_idx].astype(float)
    except Exception:
        return moving_average_forecast(hist_df['Close'].values.astype(float), horizon)


