"""Enterprise API service exposing advanced forecasting and replenishment endpoints."""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import os

from src.prophet_forecast_by_sku import prophet_forecast_optimized
from src.hybrid_forecast import hybrid_forecast_optimized
from src.classification import classify_abc_xyz
from src.replenishment_logic import calculate_reorder_point_advanced, evaluate_fail_safe_routes
from src.dataset_service import get_orders_data, get_inventory_data, get_fulfillment_data

app = FastAPI(title="SAP EWM Advanced Forecast & Replenishment Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    sku: str
    historical_demand: List[dict[str, Any]]
    periods: int = 14
    model_type: str = "prophet"

class ReplenishRequest(BaseModel):
    forecast_data: List[dict[str, Any]]
    inventory_data: List[dict[str, Any]]
    network_data: List[dict[str, Any]]
    historical_demand: List[dict[str, Any]]  # For ABC/XYZ classification
    lead_time_data: Optional[List[dict[str, Any]]] = None # Optional SKU-Site LT data
    review_period_days: int = 1

@app.get("/health")
def health() -> dict[str, str]:
    """Service health endpoint."""
    return {"status": "ok"}

@app.post("/forecast/{sku}")
def forecast_sku(sku: str, req: ForecastRequest):
    df = pd.DataFrame(req.historical_demand)
    df["sku"] = sku
    try:
        if getattr(req, "model_type", "prophet").lower() == "hybrid":
            forecast = hybrid_forecast_optimized(df, periods=req.periods)
        else:
            forecast = prophet_forecast_optimized(df, periods=req.periods)
        return forecast.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/replenish")
def replenish(req: ReplenishRequest):
    """
    Advanced Replenishment endpoint using ABC/XYZ classification 
     and Inventory Position logic from @inventory-demand-planning.
    """
    try:
        # 1. Convert inputs to DataFrames
        forecast_df = pd.DataFrame(req.forecast_data)
        inventory_df = pd.DataFrame(req.inventory_data)
        network_df = pd.DataFrame(req.network_data)
        history_df = pd.DataFrame(req.historical_demand)
        
        # 2. Perform ABC/XYZ Classification to get Z-Scores
        sku_metadata = classify_abc_xyz(history_df)
        
        # 3. Handle Lead Time Data (use defaults if not provided)
        if req.lead_time_data:
            lt_df = pd.DataFrame(req.lead_time_data)
        else:
            # Create empty placeholder to trigger defaults in replenishment_logic
            lt_df = pd.DataFrame(columns=["sku", "site", "lt_avg", "sigma_lt"])

        # 4. Calculate Advanced Reorder Point (Enterprise Grade)
        reorder_df = calculate_reorder_point_advanced(
            forecast_df=forecast_df,
            sku_metadata_df=sku_metadata,
            lead_time_df=lt_df,
            review_period_days=req.review_period_days
        )
        
        # 5. Evaluate Routes using Inventory Position (IP)
        recs = evaluate_fail_safe_routes(
            reorder_df=reorder_df, 
            inventory_df=inventory_df, 
            network_locations_df=network_df, 
            target_date=pd.Timestamp.now()
        )
        
        return recs.to_dict(orient="records")
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/datasets/orders")
def api_get_orders():
    return get_orders_data()

@app.get("/api/datasets/inventory")
def api_get_inventory():
    return get_inventory_data()

@app.get("/api/datasets/fulfillment")
def api_get_fulfillment():
    return get_fulfillment_data()

# Mount frontend at root if directory exists
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
