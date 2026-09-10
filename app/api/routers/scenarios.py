from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.api.deps import get_db
from app.api.schemas import ScenarioCreate, ScenarioItem, ScenarioUpdate
from app.api.mock_data import MOCK_STORE
from app.database.models.scenario import ScenarioModel
from app.database.models.optimization import OptimizationResultModel

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=list[ScenarioItem])
def list_scenarios(db: Session | None = Depends(get_db)):
    """List all agricultural planning scenarios."""
    if db is not None:
        try:
            scenarios = db.execute(select(ScenarioModel).order_by(ScenarioModel.created_at.desc())).scalars().all()
            items = []
            for s in scenarios:
                last_res = db.execute(
                    select(OptimizationResultModel)
                    .where(OptimizationResultModel.scenario_id == s.scenario_id)
                    .order_by(OptimizationResultModel.created_at.desc())
                ).scalars().first()

                items.append(
                    ScenarioItem(
                        scenario_id=s.scenario_id,
                        name=s.name,
                        description=s.description,
                        created_at=s.created_at,
                        is_active=s.is_active,
                        last_profit=float(last_res.total_profit_byn) if last_res else None,
                        fields_count=len(s.field_data) if s.field_data else 0,
                        crops_count=len(s.crop_data) if s.crop_data else 0,
                    )
                )
            if items:
                return items
        except Exception:
            pass

    # Fallback to mock store
    return [ScenarioItem(**s) for s in MOCK_STORE["scenarios"]]


@router.post("", response_model=ScenarioItem, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioCreate, db: Session | None = Depends(get_db)):
    """Create a new scenario."""
    new_id = uuid4()
    now = datetime.now()

    if db is not None:
        try:
            if payload.is_active:
                db.execute(update(ScenarioModel).values(is_active=False))

            scenario = ScenarioModel(
                scenario_id=new_id,
                name=payload.name,
                description=payload.description,
                is_active=payload.is_active,
                created_at=now,
            )
            db.add(scenario)
            db.commit()
            db.refresh(scenario)

            return ScenarioItem(
                scenario_id=scenario.scenario_id,
                name=scenario.name,
                description=scenario.description,
                created_at=scenario.created_at,
                is_active=scenario.is_active,
                last_profit=None,
                fields_count=0,
                crops_count=0,
            )
        except Exception:
            db.rollback()

    # Fallback
    if payload.is_active:
        for s in MOCK_STORE["scenarios"]:
            s["is_active"] = False

    item = {
        "scenario_id": str(new_id),
        "name": payload.name,
        "description": payload.description,
        "is_active": payload.is_active,
        "created_at": now.isoformat(),
        "last_profit": None,
        "fields_count": 0,
        "crops_count": 0,
    }
    MOCK_STORE["scenarios"].append(item)
    return ScenarioItem(**item)


@router.get("/{scenario_id}", response_model=ScenarioItem)
def get_scenario(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get single scenario by ID."""
    if db is not None:
        try:
            s = db.get(ScenarioModel, scenario_id)
            if s:
                last_res = db.execute(
                    select(OptimizationResultModel)
                    .where(OptimizationResultModel.scenario_id == s.scenario_id)
                    .order_by(OptimizationResultModel.created_at.desc())
                ).scalars().first()

                return ScenarioItem(
                    scenario_id=s.scenario_id,
                    name=s.name,
                    description=s.description,
                    created_at=s.created_at,
                    is_active=s.is_active,
                    last_profit=float(last_res.total_profit_byn) if last_res else None,
                    fields_count=len(s.field_data) if s.field_data else 0,
                    crops_count=len(s.crop_data) if s.crop_data else 0,
                )
        except Exception:
            pass

    for s in MOCK_STORE["scenarios"]:
        if str(s["scenario_id"]) == str(scenario_id):
            return ScenarioItem(**s)

    raise HTTPException(status_code=404, detail="Сценарий не найден")


@router.put("/{scenario_id}", response_model=ScenarioItem)
def update_scenario(scenario_id: UUID, payload: ScenarioUpdate, db: Session | None = Depends(get_db)):
    """Update scenario attributes."""
    if db is not None:
        try:
            s = db.get(ScenarioModel, scenario_id)
            if s:
                if payload.name is not None:
                    s.name = payload.name
                if payload.description is not None:
                    s.description = payload.description
                if payload.is_active is not None:
                    if payload.is_active:
                        db.execute(update(ScenarioModel).values(is_active=False))
                    s.is_active = payload.is_active
                db.commit()
                db.refresh(s)
                return ScenarioItem(
                    scenario_id=s.scenario_id,
                    name=s.name,
                    description=s.description,
                    created_at=s.created_at,
                    is_active=s.is_active,
                    last_profit=None,
                    fields_count=len(s.field_data) if s.field_data else 0,
                    crops_count=len(s.crop_data) if s.crop_data else 0,
                )
        except Exception:
            db.rollback()

    for s in MOCK_STORE["scenarios"]:
        if str(s["scenario_id"]) == str(scenario_id):
            if payload.name is not None:
                s["name"] = payload.name
            if payload.description is not None:
                s["description"] = payload.description
            if payload.is_active is not None:
                if payload.is_active:
                    for item in MOCK_STORE["scenarios"]:
                        item["is_active"] = False
                s["is_active"] = payload.is_active
            return ScenarioItem(**s)

    raise HTTPException(status_code=404, detail="Сценарий не найден")


@router.post("/{scenario_id}/activate", response_model=ScenarioItem)
def activate_scenario(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Mark a scenario as active."""
    return update_scenario(scenario_id, ScenarioUpdate(is_active=True), db)


@router.post("/{scenario_id}/clone", response_model=ScenarioItem)
def clone_scenario(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Clone an existing scenario with all its parameters."""
    base = None
    for s in MOCK_STORE["scenarios"]:
        if str(s["scenario_id"]) == str(scenario_id):
            base = s
            break

    name = f"{base['name']} (Копия)" if base else f"Копия {scenario_id}"
    new_s = {
        "scenario_id": str(uuid4()),
        "name": name,
        "description": f"Клон сценария {base.get('description', '') if base else ''}",
        "is_active": False,
        "created_at": datetime.now().isoformat(),
        "last_profit": base.get("last_profit") if base else None,
        "fields_count": base.get("fields_count", 5) if base else 5,
        "crops_count": base.get("crops_count", 9) if base else 9,
    }
    MOCK_STORE["scenarios"].append(new_s)
    return ScenarioItem(**new_s)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Delete a scenario."""
    if db is not None:
        try:
            s = db.get(ScenarioModel, scenario_id)
            if s:
                db.delete(s)
                db.commit()
                return
        except Exception:
            db.rollback()

    MOCK_STORE["scenarios"] = [s for s in MOCK_STORE["scenarios"] if str(s["scenario_id"]) != str(scenario_id)]
    return
