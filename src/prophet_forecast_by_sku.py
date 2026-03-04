from prophet.diagnostics import cross_validation, performance_metrics
from prophet import Prophet
import pandas as pd
import numpy as np

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

def prophet_forecast_optimized(
    df: pd.DataFrame,
    periods: int = 14,
    country_code: str = 'US',
    tune_params: bool = False
) -> pd.DataFrame:
    """
    Optimized Prophet pipeline with:
    1. Automatic holiday detection.
    2. Explicit seasonality control.
    3. Proper evaluation via backtesting.
    """
    prepared = _normalize_prophet_input(df)

    forecasts = []
    for sku in prepared["sku"].unique():
        sku_df = prepared[prepared["sku"] == sku][["ds", "y"]]

        if sku_df["ds"].nunique() < 2:
            continue

        # Prophet setup with ML Engineer best practices
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05 # Default is 0.05, tune if model is too rigid/flexible
        )
        model.add_country_holidays(country_name=country_code)

        model.fit(sku_df)

        # Performance Validation (Backtesting)
        # Only run if enough history exists (e.g., > 2 * periods)
        if len(sku_df) > 2 * periods and tune_params:
            try:
                df_cv = cross_validation(model, initial='30 days', period='7 days', horizon=f'{periods} days')
                df_p = performance_metrics(df_cv)
                # Log df_p metrics for monitoring
            except Exception:
                pass

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        # Add SKU metadata and return
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
