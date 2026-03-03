"""Minimal API service exposing forecasting and replenishment endpoints."""

from __future__ import annotations

<<<<<<< HEAD
from fastapi import FastAPI

app = FastAPI(title="SAP EWM Forecast & Replenishment Service")

=======
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import os

from src.forecast_model import prophet_forecast_by_sku
from src.replenishment_logic import calculate_reorder_point, evaluate_fail_safe_routes

app = FastAPI(title="SAP EWM Forecast & Replenishment Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    sku: str
    historical_demand: list[dict[str, Any]]
    periods: int = 14

class ReplenishRequest(BaseModel):
    forecast_data: list[dict[str, Any]]
    inventory_data: list[dict[str, Any]]
    network_data: list[dict[str, Any]]
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b

@app.get("/health")
def health() -> dict[str, str]:
    """Service health endpoint."""
    return {"status": "ok"}
<<<<<<< HEAD
=======

@app.post("/forecast/{sku}")
def forecast_sku(sku: str, req: ForecastRequest):
    df = pd.DataFrame(req.historical_demand)
    df["sku"] = sku
    try:
        forecast = prophet_forecast_by_sku(df, periods=req.periods)
        return forecast.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/replenish")
def replenish(req: ReplenishRequest):
    forecast_df = pd.DataFrame(req.forecast_data)
    inventory_df = pd.DataFrame(req.inventory_data)
    network_df = pd.DataFrame(req.network_data)
    
    try:
        reorder_df = calculate_reorder_point(forecast_df)
        recs = evaluate_fail_safe_routes(reorder_df, inventory_df, network_df, target_date=pd.Timestamp.now())
        return recs.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount frontend at root if directory exists
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b
