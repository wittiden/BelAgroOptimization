from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import scenarios, data, optimization, dashboard

app = FastAPI(
    title="BelAgroOptimization API",
    description="REST API для управления сценариями и оптимизацией аграрного производства Беларуси (Pyomo + GLPK)",
    version="1.0.0",
)

# CORS configuration for local development and Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure plots folder exists and mount it for static serving
plots_dir = Path("./plots")
plots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/plots", StaticFiles(directory=str(plots_dir)), name="plots")

# Include Routers
app.include_router(dashboard.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(optimization.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "BelAgroOptimization API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
