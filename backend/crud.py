"""Read helpers for clone run data."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_clone_runs(db: Session, limit: int = 50) -> list[dict]:
    """Fetch rows from ``clone_run_status`` ordered by execution time, newest
    first.

    Sorted by ``start_date`` descending (runs that have not started yet are
    pushed to the end), with ``clone_run_id`` descending as a tiebreaker.
    Joins ``clients`` to include ``client_name``.
    """
    query = text(
        """
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
        FROM clone_run_status cr
        JOIN clients c ON c.client_id = cr.client_id
        ORDER BY cr.start_date DESC NULLS LAST, cr.clone_run_id DESC
        LIMIT :limit
        """
    )
    results = db.execute(query, {"limit": limit})
    columns = list(results.keys())
    return [dict(zip(columns, row)) for row in results.fetchall()]


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
