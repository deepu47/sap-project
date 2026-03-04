"""Replenishment policy logic for EWM execution proposals."""

from __future__ import annotations

import pandas as pd
import numpy as np


def calculate_reorder_point_advanced(
    forecast_df: pd.DataFrame, 
    sku_metadata_df: pd.DataFrame,  # Contains ABC/XYZ and Service Level mappings
    lead_time_df: pd.DataFrame,      # SKU-Site specific LT and LT_std_dev (cols: sku, site, lt_avg, sigma_lt)
    review_period_days: int = 1      # How often we review (e.g., daily = 1)
) -> pd.DataFrame:
    """
    Enterprise-grade ROP calculation per @inventory-demand-planning.
    Formula: SS = Z * sqrt((LT + RP) * sigma_d^2 + d_avg^2 * sigma_lt^2)
    
    This formula accounts for:
    1. Demand Variability (sigma_d)
    2. Lead Time Variability (sigma_lt)
    3. Review Period (RP) - risk during the time until next check.
    4. Service Level (Z) - dynamically based on ABC/XYZ segmentation.
    """
    # 1. Calculate Demand Stats from Forecast
    # Group by sku, site to get average daily demand and std dev of demand
    demand_stats = forecast_df.groupby(["sku", "site"])["forecast_qty"].agg(["mean", "std"]).reset_index()
    demand_stats.rename(columns={"mean": "d_avg", "std": "sigma_d"}, inplace=True)
    
    # 2. Merge with SKU Metadata (Z-scores) and Lead Time data
    # Note: sku_metadata_df is generated from src/classification.py
    enriched = demand_stats.merge(sku_metadata_df, on="sku", how="left")
    
    # Ensure all required columns exist in enriched
    enriched = enriched.merge(lead_time_df, on=["sku", "site"], how="left")
    
    # Default values for missing LT data
    enriched["lt_avg"] = enriched["lt_avg"].fillna(3)
    enriched["sigma_lt"] = enriched["sigma_lt"].fillna(0.5)
    enriched["z_score"] = enriched["z_score"].fillna(1.65) # Fallback to 95%
    
    # 3. Calculate Advanced Safety Stock
    lt_plus_rp = enriched["lt_avg"] + review_period_days
    
    # Formula components:
    # A = (LT + RP) * sigma_d^2
    # B = d_avg^2 * sigma_lt^2
    term_a = lt_plus_rp * (enriched["sigma_d"].fillna(0) ** 2)
    term_b = (enriched["d_avg"] ** 2) * (enriched["sigma_lt"] ** 2)
    
    enriched["safety_stock"] = enriched["z_score"] * np.sqrt(term_a + term_b)

    # 4. Reorder Point = Demand during (LT + RP) + Safety Stock
    enriched["reorder_point"] = (enriched["d_avg"] * lt_plus_rp) + enriched["safety_stock"]
    
    return enriched


def evaluate_fail_safe_routes(
    reorder_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    network_locations_df: pd.DataFrame,
    target_date: pd.Timestamp
) -> pd.DataFrame:
    """
    Evaluate alternative DCs or cross-docking if primary site fails.
    Updated to use Inventory Position (IP) per @inventory-demand-planning.
    IP = On-Hand + On-Order - Backorders - Committed
    """
    # inventory_df should now contain: sku, site, on_hand_qty, on_order_qty, backorder_qty, committed_qty
    # Default missing inventory values to 0
    inv = inventory_df.fillna(0)
    if "on_order_qty" not in inv.columns: inv["on_order_qty"] = 0
    if "backorder_qty" not in inv.columns: inv["backorder_qty"] = 0
    if "committed_qty" not in inv.columns: inv["committed_qty"] = 0
    
    # Calculate Inventory Position
    inv["inventory_position"] = (
        inv["on_hand_qty"] + inv["on_order_qty"] - inv["backorder_qty"] - inv["committed_qty"]
    )

    status = reorder_df.merge(inv, on=["sku", "site"], how="left").fillna({"inventory_position": 0})
    
    # We trigger replenishment when Inventory Position drops below ROP
    status["needs_replenishment"] = status["inventory_position"] < status["reorder_point"]
    status["replenish_qty"] = status["reorder_point"] - status["inventory_position"]

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
            # Check source's OWN inventory position before shipping
            source_inv = inv[(inv["sku"] == sku) & (inv["site"] == source_site)]
            if not source_inv.empty:
                # In real SAP/EWM, we would check ATP (Available to Promise) 
                avail_qty = source_inv["inventory_position"].values[0]
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
