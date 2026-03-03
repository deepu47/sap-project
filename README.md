
# Scalable Multi-SKU Demand Forecasting & Predictive Replenishment in SAP S/4HANA EWM using SAP BTP AI Core

This repository provides a starter implementation for building a scalable, multi-SKU forecasting and replenishment workflow for **SAP S/4HANA EWM**, powered by **SAP BTP AI Core**.

# Demand Forecasting & Predictive Replenishment in SAP S/4HANA EWM using SAP BTP AI Core


This is a starter implementation for building a scalable, multi-SKU forecasting and replenishment workflow for **SAP S/4HANA EWM**, powered by **SAP BTP AI Core**.


## Repository Structure

```text
sap-ml-ewm-replenishment/
│
├── data/
│   ├── raw/                # SAP extracted data
│   ├── processed/          # Cleaned time series
│
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   ├── prophet_model_training.ipynb
│
├── src/
│   ├── data_preprocessing.py
│   ├── forecast_model.py
│   ├── replenishment_logic.py
│   ├── api_service.py
│
├── deployment/
│   ├── Dockerfile
│   ├── requirements.txt
│
├── architecture/
│   ├── system_diagram.png
│
└── README.md
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r deployment/requirements.txt
   ```
2. Prepare and clean demand history data via `src/data_preprocessing.py`.
3. Train forecasting model(s) using notebook or `src/forecast_model.py` (includes per-SKU Prophet training loop).
4. Generate replenishment recommendations via `src/replenishment_logic.py`.
5. Serve forecast/replenishment endpoints through `src/api_service.py`.

## Notes

- `architecture/system_diagram.png` is a placeholder for your system architecture diagram.
- Notebook files are initialized as placeholders and can be expanded for analysis and experimentation.
- This is a scaffold and should be adapted to your SAP landscape, SKU volume, and deployment standards.

## Free Cloud Deployment (e.g., Render)

To host this interactive demo and API on a free platform like **Render**, follow these simple steps:

1. Push this repository to GitHub.
2. Create an account on [Render](https://render.com) and click **New > Web Service**.
3. Connect your GitHub repository.
4. Set the following build and run parameters:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r deployment/requirements.txt`
   - **Start Command**: `uvicorn src.api_service:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**.

Render will automatically install the FastAPI backend, integrate Prophet, and serve the HTML dashboard at the root URL provided to you. You can then upload live CSV exports from your actual SAP EWM system directly through the dashboard UI.
