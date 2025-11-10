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


def time_series_rmse(pred: np.ndarray, truth: np.ndarray) -> float:
    """Time-series aware RMSE calculation"""
    return rmse(pred, truth)


def time_series_mae(pred: np.ndarray, truth: np.ndarray) -> float:
    """Time-series aware MAE calculation"""
    return mae(pred, truth)


def directional_accuracy(pred: np.ndarray, truth: np.ndarray) -> float:
    """
    Calculate directional accuracy (percentage of correct direction predictions)
    
    Args:
        pred: Predicted values
        truth: Actual values
        
    Returns:
        Directional accuracy as percentage (0-100)
    """
    if len(pred) < 2 or len(truth) < 2:
        return 0.0
    
    n = min(len(pred), len(truth))
    pred_diffs = np.diff(pred[:n])
    truth_diffs = np.diff(truth[:n])
    
    # Count correct direction predictions
    correct = np.sum((pred_diffs > 0) == (truth_diffs > 0))
    total = len(pred_diffs)
    
    return float((correct / total) * 100) if total > 0 else 0.0


def evaluate_time_series(
    predictions: Dict[str, np.ndarray],
    actual: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """
    Comprehensive time-series evaluation
    
    Args:
        predictions: Dictionary of model predictions
        actual: Actual values
        
    Returns:
        Dictionary with comprehensive metrics for each model
    """
    results = {}
    
    for model_name, pred in predictions.items():
        results[model_name] = {
            'RMSE': rmse(pred, actual),
            'MAE': mae(pred, actual),
            'MAPE': mape(pred, actual),
            'Directional_Accuracy': directional_accuracy(pred, actual)
        }
    
    return results


