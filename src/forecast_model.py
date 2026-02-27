"""Forecast model training and inference helpers."""

from __future__ import annotations

import pandas as pd


def naive_forecast(df: pd.DataFrame, horizon_days: int = 7) -> pd.DataFrame:
    """Create a baseline forecast by repeating the latest observed demand per SKU/site."""
    if df.empty:
        return pd.DataFrame(columns=["sku", "site", "date", "forecast_qty"])

    latest = (
        df.sort_values("date")
        .groupby(["sku", "site"], as_index=False)
        .tail(1)[["sku", "site", "date", "demand_qty"]]
    )

    rows = []
    for _, row in latest.iterrows():
        for day in range(1, horizon_days + 1):
            rows.append(
                {
                    "sku": row["sku"],
                    "site": row["site"],
                    "date": row["date"] + pd.Timedelta(days=day),
                    "forecast_qty": float(row["demand_qty"]),
                }
            )
    return pd.DataFrame(rows)
