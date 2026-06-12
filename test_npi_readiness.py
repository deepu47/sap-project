from fastapi.testclient import TestClient
import pandas as pd

from src.api_service import app
from src.npi_readiness import analyze_ctb


client = TestClient(app)


def test_analyze_ctb_flags_shortages_and_risks():
    materials = pd.DataFrame(
        [
            {
                "build_id": "NPI-TEST",
                "build_name": "Pilot Build",
                "material_id": "COMP-1",
                "material_desc": "Custom board",
                "supplier_id": "SUP-1",
                "supplier_name": "Board Supplier",
                "demand_qty": 100,
                "on_hand_qty": 25,
                "open_po_qty": 50,
                "po_due_date": "2026-07-15",
                "build_date": "2026-07-01",
                "lead_time_weeks": 12,
                "single_source": True,
                "supplier_otd_pct": 90,
                "performance_target_pct": 95,
            },
            {
                "build_id": "NPI-TEST",
                "build_name": "Pilot Build",
                "material_id": "COMP-2",
                "material_desc": "Fastener",
                "supplier_id": "SUP-2",
                "supplier_name": "Fastener Supplier",
                "demand_qty": 100,
                "on_hand_qty": 80,
                "open_po_qty": 30,
                "po_due_date": "2026-06-25",
                "build_date": "2026-07-01",
                "lead_time_weeks": 4,
                "single_source": False,
                "supplier_otd_pct": 98,
                "performance_target_pct": 95,
            },
        ]
    )

    result = analyze_ctb(materials)

    assert result["summary"]["ctb_pct"] == 50.0
    assert result["summary"]["ctb_status"] == "Red"
    assert result["summary"]["total_shortage_qty"] == 25
    assert result["shortages"][0]["material_id"] == "COMP-1"
    assert "Long lead time > 10 weeks" in result["shortages"][0]["risk_flags"]
    assert "Late PO delivery" in result["shortages"][0]["risk_flags"]
    assert "Supplier performance below target" in result["shortages"][0]["risk_flags"]


def test_npi_ctb_endpoint_returns_dashboard_payload():
    response = client.get("/api/npi/ctb")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_components"] > 0
    assert "components" in payload
    assert "supplier_performance" in payload
