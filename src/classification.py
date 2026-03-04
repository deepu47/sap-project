"""ABC/XYZ Inventory Classification and Service Level Mapping."""

from __future__ import annotations

import pandas as pd
import numpy as np


def classify_abc_xyz(
    sales_df: pd.DataFrame, 
    value_col: str = "demand_qty"
) -> pd.DataFrame:
    """
    Classify SKUs based on Value (ABC) and Predictability (XYZ).
    
    ABC:
    - A: Top 20% of SKUs driving ~80% of value.
    - B: Next 30% of SKUs driving ~15% of value.
    - C: Bottom 50% of SKUs driving ~5% of value.
    
    XYZ (Coefficient of Variation CV = StdDev / Mean):
    - X: CV < 0.5 (Highly Predictable)
    - Y: 0.5 <= CV <= 1.0 (Moderately Predictable)
    - Z: CV > 1.0 (Erratic/Lumpy)
    """
    
    # 1. Aggregate Value by SKU
    sku_stats = sales_df.groupby("sku")[value_col].agg(["sum", "mean", "std"]).reset_index()
    sku_stats.rename(columns={"sum": "total_value", "mean": "avg_demand", "std": "std_demand"}, inplace=True)
    
    # 2. ABC Classification (by cumulative value)
    sku_stats = sku_stats.sort_values("total_value", ascending=False)
    sku_stats["cum_value_pct"] = sku_stats["total_value"].cumsum() / sku_stats["total_value"].sum()
    
    def get_abc(pct):
        if pct <= 0.80: return "A"
        if pct <= 0.95: return "B"
        return "C"
        
    sku_stats["abc_class"] = sku_stats["cum_value_pct"].apply(get_abc)
    
    # 3. XYZ Classification (by Coefficient of Variation)
    # CV = Standard Deviation / Mean
    sku_stats["cv"] = sku_stats["std_demand"] / sku_stats["avg_demand"]
    # Handle zero/NaN cases (e.g., constant demand has std=0, single data point has std=NaN)
    sku_stats["cv"] = sku_stats["cv"].fillna(0)
    
    def get_xyz(cv):
        if cv < 0.5: return "X"
        if cv <= 1.0: return "Y"
        return "Z"
        
    sku_stats["xyz_class"] = sku_stats["cv"].apply(get_xyz)
    
    # 4. Final Segment (e.g., AX, BY, CZ)
    sku_stats["abc_xyz_segment"] = sku_stats["abc_class"] + sku_stats["xyz_class"]
    
    # 5. Map to Service Levels and Z-Scores (Per @inventory-demand-planning)
    service_level_map = {
        "AX": {"service_level": 0.975, "z_score": 1.96}, # High value, predictable
        "AY": {"service_level": 0.950, "z_score": 1.65}, # High value, moderate
        "AZ": {"service_level": 0.920, "z_score": 1.41}, # High value, erratic
        "BX": {"service_level": 0.950, "z_score": 1.65}, # Mid value, predictable
        "BY": {"service_level": 0.950, "z_score": 1.65}, # Mid value, moderate
        "BZ": {"service_level": 0.900, "z_score": 1.28}, # Mid value, erratic
        "CX": {"service_level": 0.920, "z_score": 1.41}, # Low value, predictable
        "CY": {"service_level": 0.900, "z_score": 1.28}, # Low value, moderate
        "CZ": {"service_level": 0.850, "z_score": 1.04}, # Low value, erratic
    }
    
    segment_data = pd.DataFrame.from_dict(service_level_map, orient="index").reset_index()
    segment_data.rename(columns={"index": "abc_xyz_segment"}, inplace=True)
    
    sku_metadata = sku_stats.merge(segment_data, on="abc_xyz_segment", how="left")
    
    return sku_metadata[["sku", "abc_xyz_segment", "service_level", "z_score"]]
