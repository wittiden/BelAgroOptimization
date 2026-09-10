from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import (
    FieldDataDto, FieldUpdateDto,
    CropDataDto, CropDataUpdateDto,
    LivestockDataDto, LivestockUpdateDto,
    FeedDataDto, FeedUpdateDto,
    WeatherDataDto, WeatherYearSummaryDto,
)
from app.api.mock_data import MOCK_STORE

router = APIRouter(prefix="/scenarios/{scenario_id}", tags=["Parameters & Data"])


# ==========================================
# ПОЛЯ (FIELDS)
# ==========================================

@router.get("/fields", response_model=list[FieldDataDto])
def get_fields(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get fields parameters for the scenario."""
    return [FieldDataDto(**f) for f in MOCK_STORE["fields"]]


@router.put("/fields/{field_id}", response_model=FieldDataDto)
def update_field(scenario_id: UUID, field_id: UUID, payload: FieldUpdateDto, db: Session | None = Depends(get_db)):
    """Update field area, soil type or fertility."""
    for f in MOCK_STORE["fields"]:
        if str(f["field_id"]) == str(field_id) or str(f["field_data_id"]) == str(field_id):
            if payload.area_ha is not None:
                f["area_ha"] = payload.area_ha
            if payload.soil_type is not None:
                f["soil_type"] = payload.soil_type
            if payload.soil_fertility is not None:
                f["soil_fertility"] = payload.soil_fertility
            return FieldDataDto(**f)

    # If matching by code or index
    if MOCK_STORE["fields"]:
        f = MOCK_STORE["fields"][0]
        if payload.area_ha is not None:
            f["area_ha"] = payload.area_ha
        return FieldDataDto(**f)

    raise HTTPException(status_code=404, detail="Поле не найдено")


# ==========================================
# КУЛЬТУРЫ (CROPS)
# ==========================================

@router.get("/crops", response_model=list[CropDataDto])
def get_crops(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get crop parameters and agronomy constraints."""
    return [CropDataDto(**c) for c in MOCK_STORE["crops"]]


@router.put("/crops/{crop_code}", response_model=CropDataDto)
def update_crop(scenario_id: UUID, crop_code: str, payload: CropDataUpdateDto, db: Session | None = Depends(get_db)):
    """Update yield, price, cost or fertilizer response for a crop."""
    for c in MOCK_STORE["crops"]:
        if c["code"] == crop_code or str(c["crop_data_id"]) == crop_code:
            for k, v in payload.model_dump(exclude_unset=True).items():
                if v is not None:
                    c[k] = v
            return CropDataDto(**c)

    raise HTTPException(status_code=404, detail="Культура не найдена")


# ==========================================
# ЖИВОТНОВОДСТВО (LIVESTOCK)
# ==========================================

@router.get("/livestock", response_model=list[LivestockDataDto])
def get_livestock(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get livestock limits, costs, and productivity parameters."""
    return [LivestockDataDto(**l) for l in MOCK_STORE["livestock"]]


@router.put("/livestock/{animal_type}", response_model=LivestockDataDto)
def update_livestock(scenario_id: UUID, animal_type: str, payload: LivestockUpdateDto, db: Session | None = Depends(get_db)):
    """Update livestock parameters."""
    for l in MOCK_STORE["livestock"]:
        if l["animal_type"] == animal_type or str(l["livestock_data_id"]) == animal_type:
            for k, v in payload.model_dump(exclude_unset=True).items():
                if v is not None:
                    l[k] = v
            return LivestockDataDto(**l)

    raise HTTPException(status_code=404, detail="Вид животных не найден")


# ==========================================
# КОРМА (FEEDS)
# ==========================================

@router.get("/feeds", response_model=list[FeedDataDto])
def get_feeds(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get feed requirements and seasonal price multipliers."""
    return [FeedDataDto(**f) for f in MOCK_STORE["feeds"]]


@router.put("/feeds/{feed_type}", response_model=FeedDataDto)
def update_feed(scenario_id: UUID, feed_type: str, payload: FeedUpdateDto, db: Session | None = Depends(get_db)):
    """Update feed prices or norms."""
    for f in MOCK_STORE["feeds"]:
        if f["feed_type"] == feed_type or str(f["feed_data_id"]) == feed_type:
            for k, v in payload.model_dump(exclude_unset=True).items():
                if v is not None:
                    f[k] = v
            return FeedDataDto(**f)

    raise HTTPException(status_code=404, detail="Вид корма не найден")


# ==========================================
# ПОГОДА (WEATHER)
# ==========================================

@router.get("/weather", response_model=list[WeatherYearSummaryDto])
def get_weather(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Get annual weather conditions for the scenario."""
    return [WeatherYearSummaryDto(**w) for w in MOCK_STORE["weather"]]
