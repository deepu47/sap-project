"""Minimal API service exposing forecasting and replenishment endpoints."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="SAP EWM Forecast & Replenishment Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Service health endpoint."""
    return {"status": "ok"}
