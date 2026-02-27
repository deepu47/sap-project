"""Replenishment policy logic for EWM execution proposals."""

from __future__ import annotations

import pandas as pd


def recommend_replenishment(
    forecast_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    service_level_buffer: float = 0.15,
) -> pd.DataFrame:
    """Return replenishment quantity suggestions by SKU/site."""
    demand = forecast_df.groupby(["sku", "site"], as_index=False)["forecast_qty"].sum()
    stock = inventory_df.groupby(["sku", "site"], as_index=False)["on_hand_qty"].sum()

    merged = demand.merge(stock, on=["sku", "site"], how="left").fillna({"on_hand_qty": 0})
    merged["required_qty"] = merged["forecast_qty"] * (1 + service_level_buffer)
    merged["replenish_qty"] = (merged["required_qty"] - merged["on_hand_qty"]).clip(lower=0)
    return merged[["sku", "site", "forecast_qty", "on_hand_qty", "replenish_qty"]]
