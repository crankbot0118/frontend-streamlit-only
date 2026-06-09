"""FastAPI backend for the Clone Automation dashboard.

Run locally with:
    uvicorn main:app --reload --port 8000
(from inside the ``backend/`` directory)
"""

from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from crud import get_clone_runs, get_run_steps
from database import get_db
from schemas import CloneFunctionRunOut, CloneRunOut

app = FastAPI(title="Clone Automation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness/health check. Returns HTTP 200 when the service is up."""
    return {
        "status": "ok",
        "service": "clone-automation-api",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get(
    "/api/v1/runs",
    response_model=list[CloneRunOut],
    summary="List clone runs",
    description="Fetches rows from clone_run_status sorted by execution time "
    "(start_date) in descending order — most recent runs first.",
)
def list_clone_runs(limit: int = 50, db: Session = Depends(get_db)) -> list[CloneRunOut]:
    return get_clone_runs(db, limit)


@app.get(
    "/api/v1/runs/{clone_run_id}/steps",
    response_model=list[CloneFunctionRunOut],
    summary="Get steps for a clone run",
    description="Fetches clone_function_run_status rows (latest attempt per "
    "function) for a given clone_run_id, ordered by function_id.",
)
def list_run_steps(
    clone_run_id: int, db: Session = Depends(get_db)
) -> list[CloneFunctionRunOut]:
    return get_run_steps(db, clone_run_id)
