"""FastAPI backend for the Clone Automation dashboard.

Configuration is loaded from the repo-root ``.env`` (see ``.env.example``).
"""

import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.errors import ConfigurationError
from config.logging import setup_logging

log = setup_logging("api")

try:
    from config.settings import api_security, load_env

    load_env()
    _API = api_security()
except ConfigurationError as exc:
    log.critical("Configuration failed: %s", exc)
    raise

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from crud import (
    get_clone_run,
    get_clone_runs,
    get_execute_clone_options,
    get_function_failure_history,
    get_function_step_detail,
    get_function_step_log_location,
    get_run_filter_options,
    get_run_steps,
    get_step_failure_summary,
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
    FunctionStepDetailOut,
    FunctionFailureHistoryOut,
    RunActionIn,
    RunActionOut,
    RunFiltersOut,
    StepFailureSummaryOut,
)
from security import (
    ALLOWED_ORIGINS,
    API_MAX_RUN_LIMIT,
    ENABLE_DOCS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SEC,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    is_allowed_log_url,
    resolve_local_log_path,
    verify_api_key,
)

app = FastAPI(
    title="Clone Automation API",
    version="0.1.0",
    dependencies=[Depends(verify_api_key)],
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            log.exception(
                "Unhandled error %s %s (%.0fms)",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        log.info(
            "%s %s -> %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)
app.add_middleware(RateLimitMiddleware, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SEC)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(SQLAlchemyError)
async def handle_db_error(request: Request, exc: SQLAlchemyError):
    log.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is unavailable. Check DB_* settings and connectivity."},
    )


@app.exception_handler(ConfigurationError)
async def handle_config_error(request: Request, exc: ConfigurationError):
    log.error("Configuration error while handling %s: %s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.on_event("startup")
async def on_startup() -> None:
    log.info(
        "Clone Automation API started (host=%s port=%s docs=%s)",
        _API.host,
        _API.port,
        ENABLE_DOCS,
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
        log.warning("Clone trigger rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log.info(
        "Clone run #%s created: %s -> %s by %s",
        run["clone_run_id"],
        run["source_name"],
        run["target_name"],
        run["user_name"],
    )
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
    description="Fetches rows from clone_run_status sorted by last_update "
    "in descending order — most recently updated runs first, regardless of status.",
)
def list_clone_runs(
    limit: int = Query(50, ge=1, le=API_MAX_RUN_LIMIT),
    client: str | None = Query(None, description="Filter by client name"),
    target: str | None = Query(None, description="Filter by target name"),
    user: str | None = Query(None, description="Filter by user name"),
    start_date: date | None = Query(None, description="Filter runs on or after this date"),
    end_date: date | None = Query(None, description="Filter runs on or before this date"),
    db: Session = Depends(get_db),
) -> list[CloneRunOut]:
    return get_clone_runs(
        db,
        limit,
        client=client,
        target=target,
        user=user,
        start_date=start_date,
        end_date=end_date,
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


def _file_download_response(path: os.PathLike, filename: str) -> FileResponse:
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
        if not is_allowed_log_url(location):
            raise HTTPException(status_code=404, detail="Log not available")
        return RedirectResponse(location)

    path = resolve_local_log_path(location)
    filename = os.path.basename(str(path)) or f"clone_run_{clone_run_id}.log"
    return _file_download_response(path, filename)


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
        log.warning("Run action %s rejected for run %s: %s", label, clone_run_id, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    acted_step = updated.get("acted_clone_function_run_id") if updated else step_id
    log.info("Run #%s marked %s (step=%s)", clone_run_id, label, acted_step)
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


@app.get(
    "/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}",
    response_model=FunctionStepDetailOut,
    summary="Get function-step details and attempt history",
    description="Returns one clone_function_run_status row plus all prior "
    "attempts for the same function within the clone run. Attempt numbers "
    "follow the PK formula base_pk = clone_run_id + 1 + (function_id * 2).",
)
def get_function_step(
    clone_run_id: int,
    clone_function_run_id: int,
    db: Session = Depends(get_db),
) -> FunctionStepDetailOut:
    detail = get_function_step_detail(db, clone_run_id, clone_function_run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Function step not found")
    return detail


@app.get(
    "/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}/log",
    summary="Download the log for a function step attempt",
    description="Serves the file referenced by step_func_log_location for the "
    "given clone_function_run_id.",
)
def download_function_step_log(
    clone_run_id: int,
    clone_function_run_id: int,
    db: Session = Depends(get_db),
):
    location = get_function_step_log_location(db, clone_run_id, clone_function_run_id)
    if not location:
        raise HTTPException(status_code=404, detail="No step log available")

    if location.startswith(("http://", "https://")):
        if not is_allowed_log_url(location):
            raise HTTPException(status_code=404, detail="Log not available")
        return RedirectResponse(location)

    path = resolve_local_log_path(location)
    filename = (
        os.path.basename(str(path))
        or f"clone_run_{clone_run_id}_step_{clone_function_run_id}.log"
    )
    return _file_download_response(path, filename)


@app.get(
    "/api/v1/analytics/step-failures",
    response_model=list[StepFailureSummaryOut],
    summary="Failure counts by clone step",
    description="Uses ``idx_cfrs_status`` to aggregate FAILED rows across all runs.",
)
def list_step_failure_summary(
    limit: int = Query(50, ge=1, le=API_MAX_RUN_LIMIT),
    db: Session = Depends(get_db),
) -> list[StepFailureSummaryOut]:
    return get_step_failure_summary(db, limit)


@app.get(
    "/api/v1/analytics/step-failures/{function_id}",
    response_model=list[FunctionFailureHistoryOut],
    summary="Recent failures for one clone step",
    description="Uses ``idx_cfrs_function_id`` to list FAILED attempts for a step.",
)
def list_function_failure_history(
    function_id: int,
    limit: int = Query(50, ge=1, le=API_MAX_RUN_LIMIT),
    db: Session = Depends(get_db),
) -> list[FunctionFailureHistoryOut]:
    return get_function_failure_history(db, function_id, limit)
