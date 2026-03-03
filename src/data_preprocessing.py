"""Data preprocessing utilities for SAP EWM demand history."""

from __future__ import annotations

import pandas as pd
import numpy as np


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
    
    # Handle abnormal demand spikes (clip to 99th percentile per SKU)
    def clip_outliers(group):
        upper_limit = group["demand_qty"].quantile(0.99)
        group["demand_qty"] = np.where(group["demand_qty"] > upper_limit, upper_limit, group["demand_qty"])
        return group
        
    cleaned = cleaned.groupby("sku", group_keys=False).apply(clip_outliers, include_groups=False)
    
    return cleaned.sort_values(["sku", "site", "date"]).reset_index(drop=True)
