"""Forecast model training and inference helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd
<<<<<<< HEAD
from prophet import Prophet
=======
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b


def _normalize_prophet_input(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize source columns into Prophet-required schema.

    Supported source schemas:
    - material/date/demand_qty
    - sku/date/demand_qty
    - already normalized ds/y with material or sku identifier
    """
    rename_map: dict[str, str] = {}
    if "material" in df.columns:
        rename_map["material"] = "sku"
    if "date" in df.columns:
        rename_map["date"] = "ds"
    if "demand_qty" in df.columns:
        rename_map["demand_qty"] = "y"

    normalized = df.rename(columns=rename_map).copy()

    required = {"sku", "ds", "y"}
    missing = required - set(normalized.columns)
    if missing:
        raise ValueError(f"Missing required columns for Prophet forecasting: {sorted(missing)}")

    normalized["ds"] = pd.to_datetime(normalized["ds"], errors="coerce")
    normalized["y"] = pd.to_numeric(normalized["y"], errors="coerce")
    normalized = normalized.dropna(subset=["sku", "ds", "y"]).sort_values(["sku", "ds"])
    return normalized.reset_index(drop=True)


def prophet_forecast_by_sku(
    df: pd.DataFrame,
    periods: int = 14,
    freq: str = "D",
    model_kwargs: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Train one Prophet model per SKU and forecast future demand.

    Strategy mirrors:
        for sku in df['material'].unique():
            sku_df = df[df['material'] == sku]
            model = Prophet()
            model.fit(sku_df)
            future = model.make_future_dataframe(periods=14)
            forecast = model.predict(future)
    """
    prepared = _normalize_prophet_input(df)
    options = model_kwargs or {}

    forecasts: list[pd.DataFrame] = []
    for sku in prepared["sku"].unique():
        sku_df = prepared[prepared["sku"] == sku][["ds", "y"]]
        if sku_df["ds"].nunique() < 2:
            # Prophet requires enough historical signal; skip sparse SKU slices.
            continue

        model = Prophet(**options)
        model.fit(sku_df)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)

        sku_forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        sku_forecast.insert(0, "sku", sku)
        sku_forecast = sku_forecast.rename(
            columns={
                "ds": "date",
                "yhat": "forecast_qty",
                "yhat_lower": "forecast_qty_lower",
                "yhat_upper": "forecast_qty_upper",
            }
        )
        forecasts.append(sku_forecast)

    if not forecasts:
        return pd.DataFrame(
            columns=["sku", "date", "forecast_qty", "forecast_qty_lower", "forecast_qty_upper"]
        )

    return pd.concat(forecasts, ignore_index=True)
<<<<<<< HEAD
=======


def evaluate_forecast(actual_df: pd.DataFrame, forecast_df: pd.DataFrame) -> dict[str, float]:
    """Calculate MAE and RMSE comparing actual demand vs forecast."""
    # actual_df expected to have 'date', 'sku', 'demand_qty'
    # forecast_df expected to have 'date', 'sku', 'forecast_qty'
    merged = pd.merge(actual_df, forecast_df, on=["sku", "date"], how="inner")
    if merged.empty:
        return {"mae": 0.0, "rmse": 0.0}
    
    mae = mean_absolute_error(merged["demand_qty"], merged["forecast_qty"])
    rmse = np.sqrt(mean_squared_error(merged["demand_qty"], merged["forecast_qty"]))
    return {"mae": float(mae), "rmse": float(rmse)}
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b
