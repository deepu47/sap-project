# Scalable Multi-SKU Demand Forecasting & Predictive Replenishment in SAP S/4HANA EWM using SAP BTP AI Core

This repository provides a starter implementation for building a scalable, multi-SKU forecasting and replenishment workflow for **SAP S/4HANA EWM**, powered by **SAP BTP AI Core**.

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
3. Train forecasting model(s) using notebook or `src/forecast_model.py`.
4. Generate replenishment recommendations via `src/replenishment_logic.py`.
5. Serve forecast/replenishment endpoints through `src/api_service.py`.

## Notes

- `architecture/system_diagram.png` is a placeholder for your system architecture diagram.
- Notebook files are initialized as placeholders and can be expanded for analysis and experimentation.
- This is a scaffold and should be adapted to your SAP landscape, SKU volume, and deployment standards.
