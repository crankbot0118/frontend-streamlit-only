"""Read helpers for clone run data."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_clone_runs(db: Session, limit: int = 50) -> list[dict]:
    """Fetch rows from ``clone_run_status`` ordered by execution time, newest
    first.

    Sorted by ``start_date`` descending (runs that have not started yet are
    pushed to the end), with ``clone_run_id`` descending as a tiebreaker.
    """
    query = text(
        """
        SELECT
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
        ORDER BY start_date DESC NULLS LAST, clone_run_id DESC
        LIMIT :limit
        """
    )
    results = db.execute(query, {"limit": limit})
    columns = list(results.keys())
    return [dict(zip(columns, row)) for row in results.fetchall()]
