from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import DashboardSummaryDto
from app.api.mock_data import MOCK_STORE, DEMO_SCENARIO_ID, MOCK_RESULTS_BY_SCENARIO

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryDto)
def get_dashboard_summary(db: Session | None = Depends(get_db)):
    """Retrieve high-level enterprise KPIs and active scenario summary."""
    active_s = next((s for s in MOCK_STORE["scenarios"] if s.get("is_active")), MOCK_STORE["scenarios"][0])
    total_land = sum(f["area_ha"] for f in MOCK_STORE["fields"])
    s_id = str(active_s["scenario_id"])
    res = MOCK_RESULTS_BY_SCENARIO.get(s_id, MOCK_STORE["latest_result"])

    return DashboardSummaryDto(
        active_scenario_id=UUID(active_s["scenario_id"]),
        active_scenario_name=active_s["name"],
        total_land_ha=total_land,
        fields_count=len(MOCK_STORE["fields"]),
        crops_count=len(MOCK_STORE["crops"]),
        livestock_types_count=len(MOCK_STORE["livestock"]),
        last_optimized_at=datetime.fromisoformat(res["created_at"]),
        last_total_profit=res["total_profit_byn"],
        last_avg_profit=res["avg_annual_profit_byn"],
        solver_status=res["solver_status"],
    )
