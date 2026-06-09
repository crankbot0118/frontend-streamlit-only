"""FastAPI backend for the Clone Automation dashboard.

Run locally with:
    uvicorn main:app --reload --port 8000
(from inside the ``backend/`` directory)
"""

import os
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from crud import (
    get_clone_run,
    get_clone_runs,
    get_execute_clone_options,
    get_run_filter_options,
    get_run_steps,
    mark_run_action,
    trigger_clone_run,
)
from database import get_db
from schemas import (
    CloneFunctionRunOut,
    CloneRunOut,
    CreateCloneRunIn,
    CreateCloneRunOut,
    ExecuteCloneOptionsOut,
    RunActionIn,
    RunActionOut,
    RunFiltersOut,
)

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
    "/api/v1/runs/filters",
    response_model=RunFiltersOut,
    summary="Run History filter options",
    description="Distinct client, target, and user values for filter dropdowns.",
)
def list_run_filters(db: Session = Depends(get_db)) -> RunFiltersOut:
    return get_run_filter_options(db)


@app.get(
    "/api/v1/execute-clone/options",
    response_model=ExecuteCloneOptionsOut,
    summary="Execute Clone form options",
    description="Users and environments for the Execute Clone page dropdowns.",
)
def list_execute_clone_options(
    db: Session = Depends(get_db),
) -> ExecuteCloneOptionsOut:
    return get_execute_clone_options(db)


@app.post(
    "/api/v1/execute-clone/trigger",
    response_model=CreateCloneRunOut,
    summary="Trigger a clone run",
    description="Validates source/target rules, then calls ``create_clone_run`` "
    "which locks the target and inserts the run plus 36 pending step rows.",
)
def create_clone_run_endpoint(
    body: CreateCloneRunIn,
    db: Session = Depends(get_db),
) -> CreateCloneRunOut:
    try:
        run = trigger_clone_run(
            db,
            body.user_id,
            body.source_env_id,
            body.target_env_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CreateCloneRunOut(
        clone_run_id=run["clone_run_id"],
        status=run["status"],
        source_name=run["source_name"],
        target_name=run["target_name"],
        user_name=run["user_name"],
        message=(
            f"Clone run #{run['clone_run_id']} created: "
            f"{run['source_name']} → {run['target_name']}."
        ),
    )


@app.get(
    "/api/v1/runs",
    response_model=list[CloneRunOut],
    summary="List clone runs",
    description="Fetches rows from clone_run_status sorted by execution time "
    "(start_date) in descending order — most recent runs first.",
)
def list_clone_runs(
    limit: int = 50,
    client: str | None = Query(None, description="Filter by client name"),
    target: str | None = Query(None, description="Filter by target name"),
    user: str | None = Query(None, description="Filter by user name"),
    start_date: date | None = Query(None, description="Filter by start date (calendar day)"),
    db: Session = Depends(get_db),
) -> list[CloneRunOut]:
    return get_clone_runs(
        db,
        limit,
        client=client,
        target=target,
        user=user,
        start_date=start_date,
    )


@app.get(
    "/api/v1/runs/{clone_run_id}",
    response_model=CloneRunOut,
    summary="Get a single clone run",
    description="Fetches one clone_run_status row (with client_name) by id.",
)
def get_single_run(
    clone_run_id: int, db: Session = Depends(get_db)
) -> CloneRunOut:
    run = get_clone_run(db, clone_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get(
    "/api/v1/runs/{clone_run_id}/log",
    summary="Download the log for a clone run",
    description="Serves the file referenced by clone_run_status.log_location. "
    "If the location is an http(s) URL the request is redirected to it; "
    "otherwise the local file is returned as a download.",
)
def download_run_log(clone_run_id: int, db: Session = Depends(get_db)):
    run = get_clone_run(db, clone_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    location = getattr(run, "log_location", None)
    if not location:
        raise HTTPException(status_code=404, detail="No log available for this run")

    if location.startswith(("http://", "https://")):
        return RedirectResponse(location)

    if os.path.isfile(location):
        filename = os.path.basename(location) or f"clone_run_{clone_run_id}.log"
        return FileResponse(location, media_type="text/plain", filename=filename)

    raise HTTPException(status_code=404, detail="Log file not found")


def _run_action(
    clone_run_id: int,
    new_status: str,
    label: str,
    db: Session,
    body: RunActionIn | None = None,
) -> RunActionOut:
    run = get_clone_run(db, clone_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    step_id = body.clone_function_run_id if body else None
    try:
        updated = mark_run_action(db, clone_run_id, new_status, step_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    acted_step = updated.get("acted_clone_function_run_id") if updated else step_id
    return RunActionOut(
        clone_run_id=clone_run_id,
        status=updated["status"] if updated else new_status,
        message=f"Run marked as {label}.",
        clone_function_run_id=acted_step,
    )


@app.post(
    "/api/v1/runs/{clone_run_id}/abort",
    response_model=RunActionOut,
    summary="Abort a failed clone run",
    description="Inserts ABORTED status rows for the run and the single failed "
    "function step. Only allowed when the latest run status is FAILED.",
)
def abort_clone_run(
    clone_run_id: int,
    body: RunActionIn | None = None,
    db: Session = Depends(get_db),
) -> RunActionOut:
    return _run_action(clone_run_id, "ABORTED", "ABORTED", db, body)


@app.post(
    "/api/v1/runs/{clone_run_id}/skip",
    response_model=RunActionOut,
    summary="Skip a failed clone run",
    description="Inserts SKIPPED status rows for the run and the single failed "
    "function step. Only allowed when the latest run status is FAILED.",
)
def skip_clone_run(
    clone_run_id: int,
    body: RunActionIn | None = None,
    db: Session = Depends(get_db),
) -> RunActionOut:
    return _run_action(clone_run_id, "SKIPPED", "SKIPPED", db, body)


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
