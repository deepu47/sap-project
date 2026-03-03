<<<<<<< HEAD
# Scalable Multi-SKU Demand Forecasting & Predictive Replenishment in SAP S/4HANA EWM using SAP BTP AI Core

This repository provides a starter implementation for building a scalable, multi-SKU forecasting and replenishment workflow for **SAP S/4HANA EWM**, powered by **SAP BTP AI Core**.
=======
# Demand Forecasting & Predictive Replenishment in SAP S/4HANA EWM using SAP BTP AI Core


This is a starter implementation for building a scalable, multi-SKU forecasting and replenishment workflow for **SAP S/4HANA EWM**, powered by **SAP BTP AI Core**.
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b

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
<<<<<<< HEAD
=======
├── test_workflow.py
>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b
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

<<<<<<< HEAD
=======
## Implementation Overview

We successfully implemented a system designed for SAP S/4HANA EWM, powered by SAP BTP AI Core. The solution forecasts multi-SKU demand using `prophet` machine learning models and generates predictive replenishment proposals. It features a fail-safe routing algorithm that optimizes distribution depending on local network availability and lead times.

### Key Components

- **Data Preprocessing** (`src/data_preprocessing.py`): Includes missing value handling and anomalous demand clipping logic (capping outliers at the 99th percentile) to ensure model stability.
- **Forecasting Engine** (`src/forecast_model.py`): A scalable Prophet-based pipeline for predicting demand, complete with Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) performance evaluation.
- **Predictive Replenishment & Fail-Safe Routing** (`src/replenishment_logic.py`): Calculates dynamic reorder points factoring in lead time variability and sweeps alternative source Distribution Centers (DCs) or external vendors whenever a primary DC faces a shortage.
- **Integration API** (`src/api_service.py`): A FastAPI interface conforming to standard request formats, allowing straightforward S/4HANA OData proxy consumption.

## Testing & Validation

Testing was conducted using a local script mimicking backend ERP demands. 

**Validation Results**:
- **Predictive Replenishment Outcome**: In testing, a simulated inventory node (`DC1`) dropped below the dynamically calculated reorder point. The fail-safe router successfully scanned the network data and selected `DC2`, which fulfilled the deficit at optimal cost.

Example output response from the routing engine:
```json
[
  {
    "sku": "SKU-1A",
    "target_site": "DC1",
    "source_site": "DC2",
    "replenish_qty": 52.375,
    "transit_time_days": 1,
    "cost": 50
  }
]
```

>>>>>>> 8fec0cefb6f1b08040dcf66922934602af8d592b
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
