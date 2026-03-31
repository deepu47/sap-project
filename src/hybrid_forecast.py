import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import logging

def _normalize_hybrid_input(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize source columns into schema required by the hybrid forecast.
    Required columns: sku, date, demand_qty
    """
    rename_map: dict[str, str] = {}
    if "material" in df.columns:
        rename_map["material"] = "sku"
    if "ds" in df.columns:
        rename_map["ds"] = "date"
    if "y" in df.columns:
        rename_map["y"] = "demand_qty"

    normalized = df.rename(columns=rename_map).copy()

    required = {"sku", "date", "demand_qty"}
    missing = required - set(normalized.columns)
    if missing:
        raise ValueError(f"Missing required columns for hybrid forecasting: {sorted(missing)}")

    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    normalized["demand_qty"] = pd.to_numeric(normalized["demand_qty"], errors="coerce")
    normalized = normalized.dropna(subset=["sku", "date", "demand_qty"]).sort_values(["sku", "date"])
    return normalized.reset_index(drop=True)


def is_demand_anomalous(demand_series: pd.Series, z_threshold: float = 2.0, anomaly_window: int = 3) -> bool:
    """Detects if the recent demand has sudden anomalies or spikes.
    
    Checks if the mean of the last `anomaly_window` periods is significantly higher
    than the historical mean (by `z_threshold` standard deviations).
    """
    if len(demand_series) < max(10, anomaly_window * 2):
        return False  # Not enough data to confidently detect anomalies
        
    history = demand_series.iloc[:-anomaly_window]
    recent = demand_series.iloc[-anomaly_window:]
    
    mean = history.mean()
    std = history.std()
    
    if pd.isna(std) or std == 0:
        return False
        
    recent_mean = recent.mean()
    z_score = (recent_mean - mean) / std
    
    return z_score > z_threshold


def wma_forecast(demand_series: pd.Series, periods: int, weights: list[float] = None) -> list[float]:
    """Weighted Moving Average forecast.
    
    Iteratively predicts future periods using the provided weights.
    Weights should sum to 1.0, with the last weight applied to the most recent observation.
    """
    if weights is None:
        weights = [0.2, 0.3, 0.5]  # Default 3-period weights
        
    window = len(weights)
    if len(demand_series) < window:
        # Fallback to simple mean if not enough data
        return [demand_series.mean() if not demand_series.empty else 0.0] * periods
        
    history = list(demand_series.values)
    forecasts = []
    
    for _ in range(periods):
        # Calculate WMA for the next period
        recent_window = history[-window:]
        next_val = sum(w * val for w, val in zip(weights, recent_window))
        forecasts.append(next_val)
        # Append to history for the next iteration's calculation
        history.append(next_val)
        
    return forecasts


def holt_forecast(demand_series: pd.Series, periods: int) -> list[float]:
    """Holt's Exponential Smoothing forecast for anomalous demand.
    
    Accounts for trend in the data, providing a smoother transition 
    during demand spikes.
    """
    if len(demand_series) < 4:
        # Fallback to simple mean if not enough data for Holt's
        return [demand_series.mean() if not demand_series.empty else 0.0] * periods
        
    try:
        model = ExponentialSmoothing(
            demand_series.values,
            trend='add',
            seasonal=None,
            initialization_method='estimated'
        ).fit()
        forecasts = model.forecast(periods)
        return list(forecasts)
    except Exception as e:
        logging.warning(f"Holt's method failed: {e}. Falling back to WMA.")
        return wma_forecast(demand_series, periods)


def hybrid_forecast_optimized(
    df: pd.DataFrame,
    periods: int = 14,
    z_threshold: float = 2.0,
    anomaly_window: int = 3,
    wma_weights: list[float] = None
) -> pd.DataFrame:
    """
    Hybrid Forecasting pipeline:
    1. Checks for sudden recent spikes in demand.
    2. Routes to Holt's Exponential Smoothing if anomalous demand is detected.
    3. Routes to Weighted Moving Average for normal demand.
    """
    prepared = _normalize_hybrid_input(df)
    
    forecasts = []
    for sku in prepared["sku"].unique():
        sku_df = prepared[prepared["sku"] == sku]
        
        if len(sku_df) < 2:
            continue
            
        demand_series = sku_df["demand_qty"]
        last_date = sku_df["date"].max()
        
        # Determine which model to use
        is_spike = is_demand_anomalous(demand_series, z_threshold, anomaly_window)
        
        if is_spike:
            logging.info(f"SKU {sku} detected anomaly. Routing to Holt's Exponential Smoothing.")
            future_vals = holt_forecast(demand_series, periods)
        else:
            logging.info(f"SKU {sku} exhibits normal demand. Routing to Weighted Moving Average.")
            future_vals = wma_forecast(demand_series, periods, wma_weights)
            
        # Create future dates dataframe
        freq = pd.infer_freq(sku_df["date"]) or 'D' # Default to daily if no frequency
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq=freq)
        
        sku_forecast = pd.DataFrame({
            "sku": sku,
            "date": future_dates,
            "forecast_qty": future_vals,
            "forecast_qty_lower": [val * 0.9 for val in future_vals], # Simple heuristic for confidence intervals
            "forecast_qty_upper": [val * 1.1 for val in future_vals]
        })
        
        forecasts.append(sku_forecast)
        
    if not forecasts:
        return pd.DataFrame(
            columns=["sku", "date", "forecast_qty", "forecast_qty_lower", "forecast_qty_upper"]
        )

    return pd.concat(forecasts, ignore_index=True)
