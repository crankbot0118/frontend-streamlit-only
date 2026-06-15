"""Indexed SQL for ``clone_function_run_status``.

Maps to schema indexes (see ``schema.sql``):

- ``idx_cfrs_run_id``     — ``(clone_run_id)`` per-job step polls
- ``idx_cfrs_function_id`` — ``(function_id)`` cross-run step analytics
- ``idx_cfrs_status``     — ``(status)`` FAILED / RUNNING lookups
"""

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

# idx_cfrs_run_id — filter the hot path (Run Details poll) by run first.
_STEPS_FOR_RUN = """
    SELECT *
    FROM clone_function_run_status
    WHERE clone_run_id = :clone_run_id
"""

GET_RUN_STEPS = text(
    f"""
    WITH steps_for_run AS (
        {_STEPS_FOR_RUN}
    )
    SELECT DISTINCT ON (cf.function_id)
        cfrs.clone_function_run_id,
        cfrs.clone_run_id,
        cfrs.function_id,
        cf.function_name,
        cfrs.status,
        cfrs.start_time,
        cfrs.end_time,
        cfrs.step_func_log_location,
        COUNT(*) OVER (PARTITION BY cfrs.function_id) - 1 AS retry_count
    FROM steps_for_run cfrs
    JOIN clone_functions cf ON cf.function_id = cfrs.function_id
    ORDER BY cf.function_id ASC, cfrs.clone_function_run_id DESC
    """
)

GET_STEP_BY_PK = text(
    f"""
    WITH steps_for_run AS (
        {_STEPS_FOR_RUN}
    )
    SELECT
        cfrs.clone_function_run_id,
        cfrs.clone_run_id,
        cfrs.function_id,
        cf.function_name,
        cfrs.status,
        cfrs.start_time,
        cfrs.end_time,
        cfrs.step_func_log_location
    FROM steps_for_run cfrs
    JOIN clone_functions cf ON cf.function_id = cfrs.function_id
    WHERE cfrs.clone_function_run_id = :clone_function_run_id
    """
)

GET_ATTEMPTS_FOR_FUNCTION = text(
    f"""
    WITH steps_for_run AS (
        {_STEPS_FOR_RUN}
    )
    SELECT
        clone_function_run_id,
        status,
        start_time,
        end_time,
        step_func_log_location,
        (clone_function_run_id - :base_pk) AS attempt_number
    FROM steps_for_run
    WHERE function_id = :function_id
    ORDER BY COALESCE(end_time, start_time) DESC NULLS LAST,
             clone_function_run_id DESC
    """
)

GET_STEP_LOG_LOCATION = text(
    f"""
    WITH steps_for_run AS (
        {_STEPS_FOR_RUN}
    )
    SELECT step_func_log_location
    FROM steps_for_run
    WHERE clone_function_run_id = :clone_function_run_id
    """
)

# idx_cfrs_status — locate FAILED rows, scoped by run when possible.
GET_FAILED_STEP_FOR_RUN = text(
    """
    SELECT
        clone_function_run_id,
        clone_run_id,
        function_id,
        step_func_log_location
    FROM clone_function_run_status
    WHERE status = 'FAILED'
      AND clone_run_id = :clone_run_id
    ORDER BY clone_function_run_id DESC
    LIMIT 1
    """
)

GET_FAILED_STEP_BY_PK = text(
    """
    SELECT
        clone_function_run_id,
        clone_run_id,
        function_id,
        step_func_log_location
    FROM clone_function_run_status
    WHERE status = 'FAILED'
      AND clone_run_id = :clone_run_id
      AND clone_function_run_id = :clone_function_run_id
    """
)

# idx_cfrs_status — batch lookup of latest FAILED step name per run (Run History).
GET_FAILED_STEP_NAMES_FOR_RUNS = (
    text(
        """
    SELECT DISTINCT ON (cfrs.clone_run_id)
        cfrs.clone_run_id,
        cf.function_name
    FROM clone_function_run_status cfrs
    JOIN clone_functions cf ON cf.function_id = cfrs.function_id
    WHERE cfrs.status = 'FAILED'
      AND cfrs.clone_run_id IN :run_ids
    ORDER BY cfrs.clone_run_id, cfrs.clone_function_run_id DESC
    """
    ).bindparams(bindparam("run_ids", expanding=True))
)

# idx_cfrs_status — failure counts grouped by step (cross-run analytics).
GET_STEP_FAILURE_SUMMARY = text(
    """
    SELECT
        cf.function_id,
        cf.function_name,
        COUNT(*) AS failure_count
    FROM clone_function_run_status cfrs
    JOIN clone_functions cf ON cf.function_id = cfrs.function_id
    WHERE cfrs.status = 'FAILED'
    GROUP BY cf.function_id, cf.function_name
    ORDER BY failure_count DESC, cf.function_id ASC
    LIMIT :limit
    """
)

# idx_cfrs_function_id — recent failures for one clone step across runs.
GET_FUNCTION_FAILURE_HISTORY = text(
    """
    SELECT
        cfrs.clone_run_id,
        cfrs.clone_function_run_id,
        cfrs.status,
        cfrs.start_time,
        cfrs.end_time
    FROM clone_function_run_status cfrs
    WHERE cfrs.function_id = :function_id
      AND cfrs.status = 'FAILED'
    ORDER BY COALESCE(cfrs.end_time, cfrs.start_time) DESC NULLS LAST,
             cfrs.clone_function_run_id DESC
    LIMIT :limit
    """
)


def fetch_run_steps(db: Session, clone_run_id: int) -> list[dict]:
    results = db.execute(GET_RUN_STEPS, {"clone_run_id": clone_run_id})
    columns = list(results.keys())
    return [dict(zip(columns, row)) for row in results.fetchall()]


def fetch_failed_step_names_for_runs(
    db: Session, clone_run_ids: list[int]
) -> dict[int, str]:
    if not clone_run_ids:
        return {}
    rows = db.execute(
        GET_FAILED_STEP_NAMES_FOR_RUNS,
        {"run_ids": clone_run_ids},
    ).mappings().all()
    return {int(row["clone_run_id"]): row["function_name"] for row in rows}


def fetch_step_failure_summary(db: Session, limit: int = 50) -> list[dict]:
    rows = db.execute(GET_STEP_FAILURE_SUMMARY, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def fetch_function_failure_history(
    db: Session, function_id: int, limit: int = 50
) -> list[dict]:
    rows = db.execute(
        GET_FUNCTION_FAILURE_HISTORY,
        {"function_id": function_id, "limit": limit},
    ).mappings().all()
    return [dict(row) for row in rows]
