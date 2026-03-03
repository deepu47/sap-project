"""Replenishment policy logic for EWM execution proposals."""

from __future__ import annotations

import pandas as pd
<<<<<<< HEAD


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
=======
import numpy as np


def calculate_reorder_point(
    forecast_df: pd.DataFrame, 
    lead_time_days: int = 3, 
    service_level_z: float = 1.65, 
    lead_time_std_dev: float = 0.5
) -> pd.DataFrame:
    """Calculate dynamic reorder point based on forecast and lead time variability."""
    # Group by sku, site to get average daily demand and std dev of demand
    demand_stats = forecast_df.groupby(["sku", "site"])["forecast_qty"].agg(["mean", "std"]).reset_index()
    demand_stats.rename(columns={"mean": "avg_daily_demand", "std": "std_dev_demand"}, inplace=True)
    
    # Calculate Safety Stock = Z * sqrt(lead_time * std_dev_demand^2 + avg_daily_demand^2 * lead_time_std_dev^2)
    demand_stats["safety_stock"] = service_level_z * np.sqrt(
        (lead_time_days * (demand_stats["std_dev_demand"].fillna(0) ** 2)) +
        ((demand_stats["avg_daily_demand"] ** 2) * (lead_time_std_dev ** 2))
    )
    
    demand_stats["reorder_point"] = (demand_stats["avg_daily_demand"] * lead_time_days) + demand_stats["safety_stock"]
    return demand_stats


def evaluate_fail_safe_routes(
    reorder_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    network_locations_df: pd.DataFrame,
    target_date: pd.Timestamp
) -> pd.DataFrame:
    """Evaluate alternative DCs or cross-docking if primary site fails."""
    # reorder_df: sku, site, avg_daily_demand, safety_stock, reorder_point
    # inventory_df: sku, site, on_hand_qty
    # network_locations_df: source_site, target_site, transit_time_days, cost
    
    status = reorder_df.merge(inventory_df, on=["sku", "site"], how="left").fillna({"on_hand_qty": 0})
    status["needs_replenishment"] = status["on_hand_qty"] < status["reorder_point"]
    status["replenish_qty"] = status["reorder_point"] - status["on_hand_qty"]
    
    shortages = status[status["needs_replenishment"]].copy()
    recommendations = []
    
    for _, row in shortages.iterrows():
        sku = row["sku"]
        target_site = row["site"]
        qty_needed = row["replenish_qty"]
        
        options = network_locations_df[network_locations_df["target_site"] == target_site].copy()
        best_option = None
        
        for _, opt in options.sort_values(["transit_time_days", "cost"]).iterrows():
            source_site = opt["source_site"]
            source_inv = inventory_df[(inventory_df["sku"] == sku) & (inventory_df["site"] == source_site)]
            if not source_inv.empty:
                avail_qty = source_inv["on_hand_qty"].values[0]
                if avail_qty >= qty_needed:
                    best_option = {
                        "sku": sku,
                        "target_site": target_site,
                        "source_site": source_site,
                        "replenish_qty": qty_needed,
                        "transit_time_days": opt["transit_time_days"],
                        "cost": opt["cost"]
                    }
                    break
        
        if best_option:
            recommendations.append(best_option)
        else:
            # Fallback - expedite from external vendor or backorder
            recommendations.append({
                "sku": sku,
                "target_site": target_site,
                "source_site": "EXTERNAL_VENDOR_EXPEDITED",
                "replenish_qty": qty_needed,
                "transit_time_days": 1, 
                "cost": 9999
            })
            
    return pd.DataFrame(recommendations)
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b
