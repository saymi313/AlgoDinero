from typing import Dict
import numpy as np


def rmse(pred: np.ndarray, truth: np.ndarray) -> float:
    n = min(len(pred), len(truth))
    return float(np.sqrt(np.mean((pred[:n] - truth[-n:]) ** 2)))


def mae(pred: np.ndarray, truth: np.ndarray) -> float:
    n = min(len(pred), len(truth))
    return float(np.mean(np.abs(pred[:n] - truth[-n:])))


def mape(pred: np.ndarray, truth: np.ndarray) -> float:
    n = min(len(pred), len(truth))
    denom = np.clip(np.abs(truth[-n:]), 1e-8, None)
    return float(np.mean(np.abs((pred[:n] - truth[-n:]) / denom)) * 100)


def summarize_metrics(models: Dict[str, np.ndarray], truth: np.ndarray) -> Dict[str, Dict[str, float]]:
    summary = {}
    for name, yhat in models.items():
        summary[name] = {
            'RMSE': rmse(yhat, truth),
            'MAE': mae(yhat, truth),
            'MAPE': mape(yhat, truth),
        }
    return summary


