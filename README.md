# SAP ML Replenishment and NPI CTB Dashboard

This project is a FastAPI and Chart.js demo for SAP-style supply chain intelligence. It combines demand forecasting, predictive replenishment, fail-safe routing, and an AI-ready NPI material readiness dashboard that determines whether a prototype build is Clear-to-Build (CTB).

## Business Use Cases

### Demand Forecasting and Replenishment

The replenishment workflow forecasts SKU demand, calculates dynamic reorder points, and recommends alternate supply routes when a target distribution center does not have enough inventory.

### NPI Material Readiness and CTB

Engineering prototype builds are often delayed by unavailable components, late supplier commitments, and long-lead-time parts. The NPI CTB dashboard analyzes SAP-like material readiness data and highlights build risk before the build date.

The CTB logic calculates:

```text
Available Supply = On Hand + Open PO

CTB Status =
IF Available Supply >= Demand
    Green
ELSE
    Red
```

It also flags:

- Long lead time greater than 10 weeks
- Single-source suppliers
- PO delivery dates later than the build date
- Supplier on-time delivery below target

The dashboard shows:

- CTB percentage
- Total material shortage quantity
- High-risk components
- Build readiness score
- Supplier performance

## Repository Structure

```text
sap-project/
|-- architecture/
|   |-- architecture_diagram.html
|-- data/
|   |-- Fulfillment.csv
|   |-- Inventory.csv
|   |-- NPI_Material_Readiness.csv
|   |-- Orders_and_shipments.csv
|-- deployment/
|   |-- requirements.txt
|-- frontend/
|   |-- dashboard.css
|   |-- index.html
|   |-- main.js
|-- src/
|   |-- api_service.py
|   |-- classification.py
|   |-- data_preprocessing.py
|   |-- dataset_service.py
|   |-- forecast_model.py
|   |-- hybrid_forecast.py
|   |-- npi_readiness.py
|   |-- prophet_forecast_by_sku.py
|   |-- replenishment_logic.py
|-- test_npi_readiness.py
|-- test_workflow.py
|-- README.md
```

## Local Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```bash
   pip install -r deployment/requirements.txt
   ```

3. Start the FastAPI app:

   ```bash
   uvicorn src.api_service:app --reload
   ```

4. Open the dashboard:

   ```text
   http://127.0.0.1:8000
   ```

5. Use the dataset dropdown to switch between:

   - Orders & Shipments
   - Inventory
   - Fulfillment
   - NPI CTB Readiness

## API Endpoints

### Health

```http
GET /health
```

### Forecast a SKU

```http
POST /forecast/{sku}
```

Request body:

```json
{
  "sku": "SKU-1A",
  "historical_demand": [
    { "date": "2026-01-01", "demand_qty": 12 },
    { "date": "2026-01-02", "demand_qty": 15 }
  ],
  "periods": 14,
  "model_type": "prophet"
}
```

### Generate Replenishment Recommendations

```http
POST /replenish
```

### Load Demo Datasets

```http
GET /api/datasets/orders
GET /api/datasets/inventory
GET /api/datasets/fulfillment
GET /api/datasets/npi-material-readiness
```

### Run NPI CTB Analysis

```http
GET /api/npi/ctb
```

This analyzes `data/NPI_Material_Readiness.csv`.

To analyze custom material readiness records:

```http
POST /api/npi/ctb
```

Request body:

```json
{
  "materials": [
    {
      "build_id": "NPI-1001",
      "build_name": "EVT Alpha Build",
      "material_id": "COMP-1001",
      "material_desc": "Main logic board",
      "supplier_id": "SUP-101",
      "supplier_name": "Apex Circuits",
      "demand_qty": 120,
      "on_hand_qty": 80,
      "open_po_qty": 50,
      "po_due_date": "2026-07-02",
      "build_date": "2026-07-10",
      "lead_time_weeks": 14,
      "single_source": true,
      "supplier_otd_pct": 91,
      "performance_target_pct": 95
    }
  ]
}
```

## NPI CTB Data Model

The sample NPI dataset is stored in `data/NPI_Material_Readiness.csv`.

Required columns:

| Column | Description |
| --- | --- |
| `build_id` | Prototype build identifier |
| `build_name` | Human-readable build name |
| `material_id` | Component or material number |
| `material_desc` | Component description |
| `supplier_id` | Supplier identifier |
| `supplier_name` | Supplier name |
| `demand_qty` | Required build quantity |
| `on_hand_qty` | Current available inventory |
| `open_po_qty` | Quantity expected from open purchase orders |
| `po_due_date` | Supplier committed delivery date |
| `build_date` | Prototype build date |
| `lead_time_weeks` | Component lead time in weeks |
| `single_source` | Whether the component has only one approved supplier |
| `supplier_otd_pct` | Supplier on-time delivery percentage |
| `performance_target_pct` | Target supplier performance percentage |

## Testing

Run the NPI readiness tests:

```bash
python -m pytest test_npi_readiness.py
```

Run the original workflow test:

```bash
python test_workflow.py
```

If Prophet is unavailable in your local environment, the frontend demo has fallback behavior for forecast continuity, but the backend forecast endpoint still needs the dependencies in `deployment/requirements.txt` for full operation.

## Deploying on Render

Render can host this project as a Python Web Service. The FastAPI backend serves the frontend from the `frontend/` directory, so you only need one Render service.

### 1. Push the Project to GitHub

Commit the project and push it to a GitHub repository connected to your Render account.

If your Git repository root contains the `sap-project/` folder, keep that in mind for the Render root directory setting below.

### 2. Create a Render Web Service

1. Go to the Render dashboard.
2. Select **New +**.
3. Select **Web Service**.
4. Connect your GitHub repository.
5. Select the branch you want to deploy.

### 3. Configure the Render Service

Use these settings:

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root Directory | `sap-project` if the repo root is `sap-ml project`; otherwise leave blank if `README.md`, `src/`, and `deployment/` are already at the repo root |
| Build Command | `pip install -r deployment/requirements.txt` |
| Start Command | `uvicorn src.api_service:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Starter or higher |

Render provides the `$PORT` environment variable automatically. The app must bind to `0.0.0.0` and use `$PORT`, not a hard-coded local port.

### 4. Optional Environment Variables

This project does not require environment variables for the included CSV demo data.

You can add these later if connecting to external services:

| Variable | Purpose |
| --- | --- |
| `SAP_API_BASE_URL` | SAP or OData API base URL |
| `SAP_CLIENT_ID` | SAP integration client ID |
| `SAP_CLIENT_SECRET` | SAP integration client secret |
| `OPENAI_API_KEY` | Optional GenAI explanations or risk narratives |
| `DATABASE_URL` | SQL database connection string |

### 5. Deploy

Click **Create Web Service**. Render will:

1. Clone the repository.
2. Install dependencies from `deployment/requirements.txt`.
3. Start the app with Uvicorn.
4. Provide a public URL like:

   ```text
   https://your-service-name.onrender.com
   ```

Open that URL in a browser. The dashboard should load directly because `src/api_service.py` mounts the `frontend/` directory at `/`.

### 6. Verify the Deployment

After the service is live, test these URLs:

```text
https://your-service-name.onrender.com/health
https://your-service-name.onrender.com/api/npi/ctb
https://your-service-name.onrender.com
```

Expected health response:

```json
{
  "status": "ok"
}
```

For the NPI CTB endpoint, the sample dataset currently returns a Red build status because some components are short or late.

### 7. Troubleshooting Render Deployments

#### Build Fails While Installing Prophet

`prophet` can be heavier than the other dependencies. If the Render build fails while compiling or installing Prophet:

1. Confirm the service is using Python 3.10 or 3.11 if available.
2. Upgrade pip in the build command:

   ```bash
   pip install --upgrade pip && pip install -r deployment/requirements.txt
   ```

3. If the app only needs the CTB dashboard and not Prophet forecasting, remove `prophet==1.1.5` from `deployment/requirements.txt` and redeploy.

#### App Starts Locally but Not on Render

Check that the start command is exactly:

```bash
uvicorn src.api_service:app --host 0.0.0.0 --port $PORT
```

Common mistakes are using `localhost`, using port `8000`, or starting from the wrong root directory.

#### Frontend Loads but API Calls Fail

The frontend uses relative URLs such as `/api/npi/ctb`, so API calls should work when the FastAPI app serves the frontend. If you split the frontend and backend into separate services later, enable CORS for the frontend domain and update the fetch base URL.

#### Data Changes Do Not Show Up

The dataset loader uses in-memory caching. Restart the Render service after changing CSV files so the app reloads the latest data.

## Production Notes

- Replace CSV files with SQL views or SAP OData extracts for production use.
- Store secrets in Render environment variables, not in source files.
- Add authentication before exposing supplier or build readiness data publicly.
- Consider a scheduled ETL job to refresh material, PO, supplier, and inventory tables.
- Add GenAI summarization only after deterministic CTB rules are validated, so the model explains risks rather than deciding them.

