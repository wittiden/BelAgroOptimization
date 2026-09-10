from uuid import uuid4, UUID
from datetime import datetime
import asyncio
import time
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import (
    OptimizationRunRequest,
    OptimizationJobStatus,
    OptimizationResultDto,
)
from app.api.mock_data import MOCK_STORE, DEMO_SCENARIO_ID, MOCK_RESULTS_BY_SCENARIO

router = APIRouter(prefix="/optimization", tags=["Optimization"])

# In-memory registry for optimization jobs
JOBS: dict[str, dict] = {}


def _run_optimization_task(job_id: str, scenario_id: str):
    """Background task simulating/executing Pyomo solver."""
    try:
        job = JOBS[job_id]
        job["status"] = "running"
        job["progress"] = 10
        job["logs"].append("Инициализация математической модели Pyomo...")
        time.sleep(0.6)

        job["progress"] = 30
        job["logs"].append("Загрузка параметров полей (5 полей, 900 га пашни)...")
        job["logs"].append("Формирование агротехнических ограничений (зерновые ≥35%, пар ≥5%, картофель ≤18%)...")
        time.sleep(0.7)

        job["progress"] = 55
        job["logs"].append("Построение баланса кормопроизводства и рационов скота...")
        job["logs"].append("Учет климатических факторов (засуха 2026: 430 мм)...")
        time.sleep(0.7)

        job["progress"] = 75
        job["logs"].append("Запуск симплекс-метода GLPK / MIP Solver...")
        time.sleep(0.8)

        job["progress"] = 90
        job["logs"].append("Оптимальное решение найдено! Статус: Optimal. Итераций: 412.")
        job["logs"].append("Формирование матриц распределения культур по полям...")
        time.sleep(0.5)

        now = datetime.now()
        job["status"] = "completed"
        job["progress"] = 100
        job["finished_at"] = now
        job["execution_time_sec"] = round(time.time() - job["start_timestamp"], 2)
        job["message"] = "Оптимизация успешно завершена"
        job["logs"].append(f"Расчет завершен за {job['execution_time_sec']} сек. Прибыль: 2,854,300 BYN.")

        # Update last profit in scenario
        profit = 2854300.0
        if scenario_id in MOCK_RESULTS_BY_SCENARIO:
            profit = MOCK_RESULTS_BY_SCENARIO[scenario_id]["total_profit_byn"]
        for s in MOCK_STORE["scenarios"]:
            if str(s["scenario_id"]) == str(scenario_id):
                s["last_profit"] = profit

    except Exception as e:
        if job_id in JOBS:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["message"] = str(e)
            JOBS[job_id]["logs"].append(f"Ошибка оптимизации: {e}")


@router.post("/run", response_model=OptimizationJobStatus)
def run_optimization(
    payload: OptimizationRunRequest,
    background_tasks: BackgroundTasks,
    db: Session | None = Depends(get_db)
):
    """Trigger an optimization job for a scenario in the background."""
    scenario_id = str(payload.scenario_id or DEMO_SCENARIO_ID)
    job_id = str(uuid4())
    now = datetime.now()

    job_data = {
        "job_id": job_id,
        "scenario_id": UUID(scenario_id),
        "status": "pending",
        "progress": 0,
        "message": "Задача поставлена в очередь",
        "logs": ["Задача создана, ожидание запуска решателя..."],
        "started_at": now,
        "finished_at": None,
        "execution_time_sec": None,
        "start_timestamp": time.time(),
    }
    JOBS[job_id] = job_data

    background_tasks.add_task(_run_optimization_task, job_id, scenario_id)

    return OptimizationJobStatus(**job_data)


@router.get("/status/{job_id}", response_model=OptimizationJobStatus)
def get_job_status(job_id: str):
    """Check the real-time execution status and solver logs."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Задача оптимизации не найдена")
    return OptimizationJobStatus(**job)


@router.get("/results/{scenario_id}", response_model=OptimizationResultDto)
def get_optimization_results(scenario_id: UUID, db: Session | None = Depends(get_db)):
    """Retrieve detailed optimization results (profits, rotation matrix, feed balance)."""
    s_id = str(scenario_id)
    if s_id in MOCK_RESULTS_BY_SCENARIO:
        return OptimizationResultDto(**MOCK_RESULTS_BY_SCENARIO[s_id])
    res = MOCK_STORE["latest_result"]
    return OptimizationResultDto(**res)


@router.get("/plots")
def list_plots():
    """List paths to generated Matplotlib plots."""
    return {
        "plots": [
            {"name": "Прибыль по годам", "url": "/plots/profit_by_year.png"},
            {"name": "Распределение культур", "url": "/plots/crop_distribution.png"},
            {"name": "Прибыль по культурам", "url": "/plots/crop_profit_breakdown.png"},
            {"name": "Прибыль от животноводства", "url": "/plots/livestock_profit_breakdown.png"},
            {"name": "Сводная таблица", "url": "/plots/profit_summary_table.png"},
        ]
    }
