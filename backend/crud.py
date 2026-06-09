"""Read helpers for clone run data."""

from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

# Latest ``clone_run_status`` row per ``clone_run_id`` (append-only status history).
_LATEST_RUNS_CTE = """
    SELECT DISTINCT ON (clone_run_id)
        clone_run_id,
        client_id,
        user_id,
        user_name,
        source_env_id,
        target_env_id,
        source_name,
        target_name,
        status,
        start_date,
        last_update,
        log_location
    FROM clone_run_status
    ORDER BY clone_run_id, last_update DESC NULLS LAST, clone_run_id DESC
"""


def get_run_filter_options(db: Session) -> dict[str, list[str]]:
    """Distinct client, target, and user values for Run History filter dropdowns."""
    clients = db.execute(
        text(
            f"""
            SELECT DISTINCT c.client_name
            FROM ({_LATEST_RUNS_CTE}) cr
            JOIN clients c ON c.client_id = cr.client_id
            WHERE c.client_name IS NOT NULL
            ORDER BY c.client_name
            """
        )
    ).scalars().all()
    targets = db.execute(
        text(
            f"""
            SELECT DISTINCT target_name
            FROM ({_LATEST_RUNS_CTE}) latest_runs
            WHERE target_name IS NOT NULL
            ORDER BY target_name
            """
        )
    ).scalars().all()
    users = db.execute(
        text(
            f"""
            SELECT DISTINCT user_name
            FROM ({_LATEST_RUNS_CTE}) latest_runs
            WHERE user_name IS NOT NULL
            ORDER BY user_name
            """
        )
    ).scalars().all()
    return {
        "clients": list(clients),
        "targets": list(targets),
        "users": list(users),
    }


def get_clone_runs(
    db: Session,
    limit: int = 50,
    client: str | None = None,
    target: str | None = None,
    user: str | None = None,
    start_date: date | None = None,
) -> list[dict]:
    """Fetch rows from ``clone_run_status`` ordered by execution time, newest
    first.

    Sorted by ``start_date`` descending (runs that have not started yet are
    pushed to the end), with ``clone_run_id`` descending as a tiebreaker.
    Joins ``clients`` to include ``client_name``.
    """
    conditions: list[str] = []
    params: dict = {"limit": limit}
    if client:
        conditions.append("c.client_name = :client")
        params["client"] = client
    if target:
        conditions.append("cr.target_name = :target")
        params["target"] = target
    if user:
        conditions.append("cr.user_name = :user")
        params["user"] = user
    if start_date:
        conditions.append("cr.start_date::date = :start_date")
        params["start_date"] = start_date

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = text(
        f"""
        SELECT
            cr.clone_run_id,
            cr.client_id,
            c.client_name,
            cr.user_id,
            cr.user_name,
            cr.source_env_id,
            cr.target_env_id,
            cr.source_name,
            cr.target_name,
            cr.status,
            cr.start_date,
            cr.last_update,
            cr.log_location
        FROM ({_LATEST_RUNS_CTE}) cr
        JOIN clients c ON c.client_id = cr.client_id
        {where}
        ORDER BY cr.start_date DESC NULLS LAST, cr.clone_run_id DESC
        LIMIT :limit
        """
    )
    results = db.execute(query, params)
    columns = list(results.keys())
    return [dict(zip(columns, row)) for row in results.fetchall()]


def get_clone_run(db: Session, clone_run_id: int) -> dict | None:
    """Fetch a single ``clone_run_status`` row (with ``client_name`` joined).

    Returns ``None`` when no run matches ``clone_run_id``.
    """
    query = text(
        f"""
        SELECT
            cr.clone_run_id,
            cr.client_id,
            c.client_name,
            cr.user_id,
            cr.user_name,
            cr.source_env_id,
            cr.target_env_id,
            cr.source_name,
            cr.target_name,
            cr.status,
            cr.start_date,
            cr.last_update,
            cr.log_location
        FROM ({_LATEST_RUNS_CTE}) cr
        JOIN clients c ON c.client_id = cr.client_id
        WHERE cr.clone_run_id = :clone_run_id
        """
    )
    results = db.execute(query, {"clone_run_id": clone_run_id})
    columns = list(results.keys())
    row = results.fetchone()
    return dict(zip(columns, row)) if row else None


def get_run_steps(db: Session, clone_run_id: int) -> list[dict]:
    """Fetch the latest attempt of each step for a clone run.

    Returns rows from ``clone_function_run_status`` (joined with
    ``clone_functions`` for the function name), one row per function showing the
    most recent attempt, ordered by ``function_id``. ``retry_count`` is the
    number of prior attempts for that function.
    """
    query = text(
        """
        SELECT DISTINCT ON (cf.function_id)
            cfrs.clone_function_run_id,
            cfrs.clone_run_id,
            cfrs.function_id,
            cf.function_name,
            cfrs.status,
            cfrs.start_time,
            cfrs.end_time,
            cfrs.step_func_log_location,
            COUNT(*) OVER (PARTITION BY cfrs.clone_run_id, cfrs.function_id) - 1
                AS retry_count
        FROM clone_function_run_status cfrs
        JOIN clone_functions cf ON cf.function_id = cfrs.function_id
        WHERE cfrs.clone_run_id = :clone_run_id
        ORDER BY cf.function_id ASC, cfrs.clone_function_run_id DESC
        """
    )
    results = db.execute(query, {"clone_run_id": clone_run_id})
    columns = list(results.keys())
    return [dict(zip(columns, row)) for row in results.fetchall()]


def _get_failed_function_step(
    db: Session, clone_run_id: int, clone_function_run_id: int | None = None
) -> dict | None:
    """Return the failed function step to act on (latest FAILED unless id given)."""
    if clone_function_run_id is not None:
        query = text(
            """
            SELECT
                clone_function_run_id,
                clone_run_id,
                function_id,
                step_func_log_location
            FROM clone_function_run_status
            WHERE clone_function_run_id = :clone_function_run_id
              AND clone_run_id = :clone_run_id
              AND status = 'FAILED'
            """
        )
        params = {
            "clone_function_run_id": clone_function_run_id,
            "clone_run_id": clone_run_id,
        }
    else:
        query = text(
            """
            SELECT
                clone_function_run_id,
                clone_run_id,
                function_id,
                step_func_log_location
            FROM clone_function_run_status
            WHERE clone_run_id = :clone_run_id AND status = 'FAILED'
            ORDER BY clone_function_run_id DESC
            LIMIT 1
            """
        )
        params = {"clone_run_id": clone_run_id}

    row = db.execute(query, params).mappings().first()
    return dict(row) if row else None


def mark_run_action(
    db: Session,
    clone_run_id: int,
    new_status: str,
    clone_function_run_id: int | None = None,
) -> dict | None:
    """Append ABORTED/SKIPPED status rows for the run and the failed function step.

    Inserts a new ``clone_function_run_status`` row for the single failed step
    (preserving prior attempts) and a new ``clone_run_status`` row for the run.
    Returns the latest run row, or ``None`` when the run does not exist.
    Raises ``ValueError`` when the run is not FAILED or no failed step is found.
    """
    run = get_clone_run(db, clone_run_id)
    if run is None:
        return None
    if (run.get("status") or "").upper() != "FAILED":
        raise ValueError("Run is not in FAILED state")

    failed_step = _get_failed_function_step(db, clone_run_id, clone_function_run_id)
    if failed_step is None:
        raise ValueError("No failed function step found for this run")

    db.execute(
        text(
            """
            INSERT INTO clone_function_run_status (
                clone_run_id,
                function_id,
                status,
                start_time,
                end_time,
                step_func_log_location
            ) VALUES (
                :clone_run_id,
                :function_id,
                :status,
                NOW(),
                NOW(),
                :step_func_log_location
            )
            """
        ),
        {
            "clone_run_id": failed_step["clone_run_id"],
            "function_id": failed_step["function_id"],
            "status": new_status,
            "step_func_log_location": failed_step.get("step_func_log_location"),
        },
    )
    db.execute(
        text(
            f"""
            INSERT INTO clone_run_status (
                clone_run_id,
                client_id,
                user_id,
                user_name,
                source_env_id,
                target_env_id,
                source_name,
                target_name,
                status,
                start_date,
                last_update,
                log_location
            )
            SELECT
                clone_run_id,
                client_id,
                user_id,
                user_name,
                source_env_id,
                target_env_id,
                source_name,
                target_name,
                :status,
                start_date,
                NOW(),
                log_location
            FROM ({_LATEST_RUNS_CTE}) latest_runs
            WHERE clone_run_id = :clone_run_id
            """
        ),
        {"clone_run_id": clone_run_id, "status": new_status},
    )
    db.commit()
    latest = get_clone_run(db, clone_run_id)
    if latest is None:
        return None
    latest["acted_clone_function_run_id"] = failed_step["clone_function_run_id"]
    return latest
