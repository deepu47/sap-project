"""Data preprocessing utilities for SAP EWM demand history."""

from __future__ import annotations

import pandas as pd


def clean_demand_history(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize raw demand history into model-ready format."""
    required_columns = {"sku", "site", "date", "demand_qty"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = df.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["demand_qty"] = pd.to_numeric(cleaned["demand_qty"], errors="coerce").fillna(0)
    cleaned = cleaned.dropna(subset=["date", "sku", "site"])
    return cleaned.sort_values(["sku", "site", "date"]).reset_index(drop=True)
