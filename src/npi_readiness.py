"""Clear-to-build analysis for NPI material readiness."""

from __future__ import annotations

from typing import Any

import pandas as pd


LONG_LEAD_TIME_WEEKS = 10
DEFAULT_SUPPLIER_TARGET = 95.0


REQUIRED_COLUMNS = {
    "build_id",
    "material_id",
    "material_desc",
    "supplier_id",
    "supplier_name",
    "demand_qty",
    "on_hand_qty",
    "open_po_qty",
    "po_due_date",
    "build_date",
    "lead_time_weeks",
    "single_source",
    "supplier_otd_pct",
}


def analyze_ctb(materials_df: pd.DataFrame) -> dict[str, Any]:
    """Return build-level CTB metrics and component-level risk rows."""
    missing = REQUIRED_COLUMNS - set(materials_df.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"Missing CTB input columns: {missing_cols}")

    df = materials_df.copy()
    numeric_columns = [
        "demand_qty",
        "on_hand_qty",
        "open_po_qty",
        "lead_time_weeks",
        "supplier_otd_pct",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    if "performance_target_pct" not in df.columns:
        df["performance_target_pct"] = DEFAULT_SUPPLIER_TARGET
    df["performance_target_pct"] = pd.to_numeric(
        df["performance_target_pct"], errors="coerce"
    ).fillna(DEFAULT_SUPPLIER_TARGET)

    df["po_due_date"] = pd.to_datetime(df["po_due_date"], errors="coerce")
    df["build_date"] = pd.to_datetime(df["build_date"], errors="coerce")
    df["single_source"] = df["single_source"].map(_to_bool)

    df["available_supply"] = df["on_hand_qty"] + df["open_po_qty"]
    df["shortage_qty"] = (df["demand_qty"] - df["available_supply"]).clip(lower=0)
    df["ctb_status"] = df["shortage_qty"].apply(lambda qty: "Green" if qty <= 0 else "Red")

    df["risk_flags"] = df.apply(_risk_flags, axis=1)
    df["risk_count"] = df["risk_flags"].apply(len)
    df["po_due_date"] = df["po_due_date"].dt.strftime("%Y-%m-%d")
    df["build_date"] = df["build_date"].dt.strftime("%Y-%m-%d")

    total_components = len(df)
    green_components = int((df["ctb_status"] == "Green").sum())
    ctb_pct = round((green_components / total_components) * 100, 1) if total_components else 0
    avg_supplier_performance = round(float(df["supplier_otd_pct"].mean()), 1) if total_components else 0
    total_shortage_qty = round(float(df["shortage_qty"].sum()), 1)
    high_risk_components = int((df["risk_count"] >= 2).sum())
    readiness_score = _readiness_score(ctb_pct, avg_supplier_performance, int(df["risk_count"].sum()))

    component_columns = [
        "build_id",
        "build_name",
        "material_id",
        "material_desc",
        "supplier_id",
        "supplier_name",
        "demand_qty",
        "on_hand_qty",
        "open_po_qty",
        "available_supply",
        "shortage_qty",
        "ctb_status",
        "po_due_date",
        "build_date",
        "lead_time_weeks",
        "single_source",
        "supplier_otd_pct",
        "performance_target_pct",
        "risk_flags",
        "risk_count",
    ]
    present_columns = [column for column in component_columns if column in df.columns]

    return {
        "summary": {
            "build_id": str(df["build_id"].iloc[0]) if total_components else None,
            "build_name": str(df.get("build_name", pd.Series(["NPI Build"])).iloc[0])
            if total_components
            else None,
            "build_date": str(df["build_date"].iloc[0]) if total_components else None,
            "ctb_pct": ctb_pct,
            "ctb_status": "Green" if ctb_pct == 100 else "Red",
            "readiness_score": readiness_score,
            "total_components": total_components,
            "green_components": green_components,
            "red_components": total_components - green_components,
            "total_shortage_qty": total_shortage_qty,
            "high_risk_components": high_risk_components,
            "avg_supplier_performance": avg_supplier_performance,
        },
        "components": df[present_columns].to_dict(orient="records"),
        "shortages": df[df["shortage_qty"] > 0]
        .sort_values(["shortage_qty", "risk_count"], ascending=False)[present_columns]
        .to_dict(orient="records"),
        "high_risk": df[df["risk_count"] >= 2]
        .sort_values(["risk_count", "shortage_qty"], ascending=False)[present_columns]
        .to_dict(orient="records"),
        "supplier_performance": _supplier_performance(df),
    }


def _risk_flags(row: pd.Series) -> list[str]:
    flags = []
    if row["lead_time_weeks"] > LONG_LEAD_TIME_WEEKS:
        flags.append("Long lead time > 10 weeks")
    if row["single_source"]:
        flags.append("Single source supplier")
    if pd.notna(row["po_due_date"]) and pd.notna(row["build_date"]) and row["po_due_date"] > row["build_date"]:
        flags.append("Late PO delivery")
    if row["supplier_otd_pct"] < row["performance_target_pct"]:
        flags.append("Supplier performance below target")
    return flags


def _readiness_score(ctb_pct: float, supplier_performance: float, risk_count: int) -> int:
    weighted_score = (ctb_pct * 0.65) + (supplier_performance * 0.35)
    penalty = min(risk_count * 3, 35)
    return max(0, min(100, round(weighted_score - penalty)))


def _supplier_performance(df: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = (
        df.groupby(["supplier_id", "supplier_name"], dropna=False)
        .agg(
            supplier_otd_pct=("supplier_otd_pct", "mean"),
            component_count=("material_id", "count"),
            shortage_qty=("shortage_qty", "sum"),
            risk_count=("risk_count", "sum"),
        )
        .reset_index()
        .sort_values(["supplier_otd_pct", "risk_count"], ascending=[True, False])
    )
    grouped["supplier_otd_pct"] = grouped["supplier_otd_pct"].round(1)
    grouped["shortage_qty"] = grouped["shortage_qty"].round(1)
    return grouped.to_dict(orient="records")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}
