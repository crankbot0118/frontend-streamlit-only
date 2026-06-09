#!/usr/bin/env python3
# =============================================================================
# agent.py
# VIGT Clone Automation — Target Instance Agent
#
# One agent per target instance. Polls clone_run_status for PENDING jobs
# assigned to this instance (target_env_id) and fires master_clone.sh.
#
# Run status is derived from clone_function_run_status via trg_sync_run_status;
# master_clone.sh owns step rows. This agent reads the latest status row per
# clone_run_id (append-only history) and calls finish_clone_run() when a job
# reaches a terminal state so environments.locked stays in sync.
#
# ~/.env required keys:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   INSTANCE_ENV_ID     — env_id of THIS machine in the environments table
#   INSTANCE_DBNAME     — optional override for script arg $1 (default: lowercased env_name)
#   MASTER_CLONE_SH     — full path to master_clone.sh
#   SKIP_FUNCTION_SH    — full path to skip_function.sh
#   NULLIFY_CLONE_SH    — full path to nullify_clone_control.sh
#   ABORT_CLONE_SH      — full path to abort_clone.sh
#   POLL_INTERVAL       — seconds between polls (default: 10)
#   INSTANCE_CLONE_DIR  — instance root (default: /u02/shared/AUTOMATION/Clone_Auto/Instances)
#   CLONE_LOG           — optional override for log file path ({run_id}, {dbname} placeholders)
# =============================================================================

from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")

# Latest clone_run_status row per clone_run_id (matches backend crud.py).
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


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"[AGENT] FATAL: missing env var: {name}", flush=True)
        sys.exit(1)
    return val


DB_CONFIG = {
    "host": _require("DB_HOST"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": _require("DB_NAME"),
    "user": _require("DB_USER"),
    "password": _require("DB_PASSWORD"),
}

INSTANCE_ENV_ID = int(_require("INSTANCE_ENV_ID"))
INSTANCE_DBNAME = os.environ.get("INSTANCE_DBNAME")
MASTER_CLONE_SH = _require("MASTER_CLONE_SH")
SKIP_FUNCTION_SH = _require("SKIP_FUNCTION_SH")
NULLIFY_CLONE_SH = _require("NULLIFY_CLONE_SH")
ABORT_CLONE_SH = _require("ABORT_CLONE_SH")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))
INSTANCE_CLONE_DIR = os.environ.get(
    "INSTANCE_CLONE_DIR",
    "/u02/shared/AUTOMATION/Clone_Auto/Instances",
)
LOG_LOCATION_MAX = 100

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("vigt_agent")

_shutdown = False
_SAFE_DBNAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_SUBPROCESS_TIMEOUT = int(os.environ.get("SUBPROCESS_TIMEOUT", "0")) or None


def validate_dbname(dbname: str) -> str:
    """Reject path traversal / shell metacharacters in the instance dbname key."""
    if not dbname or not _SAFE_DBNAME_RE.fullmatch(dbname):
        raise ValueError(f"Invalid INSTANCE dbname: {dbname!r}")
    return dbname


def validate_clone_run_id(clone_run_id: int) -> int:
    """Ensure clone_run_id is a positive integer before passing to shell scripts."""
    if clone_run_id <= 0:
        raise ValueError(f"Invalid clone_run_id: {clone_run_id}")
    return clone_run_id


def _handle_signal(signum, frame):
    global _shutdown
    log.info("Signal %s received — will shut down after current job finishes.", signum)
    _shutdown = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


def get_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def verify_instance_env(conn) -> dict:
    """Ensure INSTANCE_ENV_ID exists. Target agents must not run on PROD."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT env_id, env_name, locked
            FROM environments
            WHERE env_id = %s
            """,
            (INSTANCE_ENV_ID,),
        )
        row = cur.fetchone()
    if not row:
        log.error("INSTANCE_ENV_ID=%s not found in environments table.", INSTANCE_ENV_ID)
        sys.exit(1)
    env = dict(row)
    if env["env_name"].strip().upper() == "PROD":
        log.error(
            "INSTANCE_ENV_ID=%s is PROD (%s). Clone agents run on targets only.",
            INSTANCE_ENV_ID,
            env["env_name"],
        )
        sys.exit(1)
    return env


def script_dbname(env: dict) -> str:
    """Instance key passed as $1 to master_clone.sh and helper scripts."""
    if INSTANCE_DBNAME:
        return validate_dbname(INSTANCE_DBNAME)
    return validate_dbname(env["env_name"].strip().lower())


def parse_shell_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines from a shell env file (no sourcing/eval)."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("."):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def expand_shell_vars(value: str, ctx: dict[str, str]) -> str:
    """Expand ${VAR} and $VAR references using ctx (same file as master_clone.sh)."""
    prev = None
    while prev != value:
        prev = value
        value = re.sub(
            r"\$\{([^}]+)\}",
            lambda m: ctx.get(m.group(1), m.group(0)),
            value,
        )
        value = re.sub(
            r"\$([A-Za-z_][A-Za-z0-9_]*)",
            lambda m: ctx.get(m.group(1), m.group(0)),
            value,
        )
    return value


def resolve_clone_log_path(dbname: str, clone_run_id: int) -> str | None:
    """
    Resolve CLONE_LOG the same way master_clone.sh does after sourcing db.env.
    Optional ~/.env CLONE_LOG override supports {run_id} and {dbname}.
    """
    validate_dbname(dbname)
    validate_clone_run_id(clone_run_id)
    override = os.environ.get("CLONE_LOG") or os.environ.get("CLONE_LOG_PATH")
    if override:
        return (
            override.replace("{run_id}", str(clone_run_id)).replace("{dbname}", dbname)
        )

    env_file = Path(INSTANCE_CLONE_DIR) / dbname / "env" / "DB" / f"{dbname}_db.env"
    ctx = parse_shell_env_file(env_file)
    raw = ctx.get("CLONE_LOG")
    if not raw:
        log.warning("CLONE_LOG not found in %s", env_file)
        return None
    return expand_shell_vars(raw, ctx)


def set_run_log_location(conn, clone_run_id: int, log_path: str) -> None:
    """Write clone_run_status.log_location so the dashboard can serve View Log."""
    if len(log_path) > LOG_LOCATION_MAX:
        log.warning(
            "[run=%s] log path exceeds %s chars and will be truncated: %s",
            clone_run_id,
            LOG_LOCATION_MAX,
            log_path,
        )
        log_path = log_path[:LOG_LOCATION_MAX]

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE clone_run_status
            SET log_location = %s,
                last_update  = NOW()
            WHERE clone_run_id = %s
            """,
            (log_path, clone_run_id),
        )
    conn.commit()
    log.info("[run=%s] log_location set: %s", clone_run_id, log_path)


def pg_subprocess_env() -> dict[str, str]:
    """Export DB creds for shell scripts (PG* with DB_* fallbacks)."""
    env = os.environ.copy()
    env["PGHOST"] = env.get("PGHOST") or DB_CONFIG["host"]
    env["PGPORT"] = str(env.get("PGPORT") or DB_CONFIG["port"])
    env["PGDATABASE"] = env.get("PGDATABASE") or DB_CONFIG["dbname"]
    env["PGUSER"] = env.get("PGUSER") or DB_CONFIG["user"]
    env["PGPASSWORD"] = env.get("PGPASSWORD") or DB_CONFIG["password"]
    env["DB_HOST"] = env["PGHOST"]
    env["DB_PORT"] = env["PGPORT"]
    env["DB_NAME"] = env["PGDATABASE"]
    env["DB_USER"] = env["PGUSER"]
    env["DB_PASSWORD"] = env["PGPASSWORD"]
    return env


def fetch_pending_job(conn) -> dict | None:
    """Oldest PENDING job for this target (by last_update, then clone_run_id)."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT
                r.clone_run_id,
                r.source_name,
                r.target_name,
                r.user_name,
                r.last_update
            FROM ({_LATEST_RUNS_CTE}) r
            WHERE r.status = 'PENDING'
              AND r.target_env_id = %s
            ORDER BY r.last_update ASC NULLS LAST, r.clone_run_id ASC
            LIMIT 1
            """,
            (INSTANCE_ENV_ID,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def get_latest_run_status(conn, clone_run_id: int) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT status
            FROM ({_LATEST_RUNS_CTE}) r
            WHERE r.clone_run_id = %s
            """,
            (clone_run_id,),
        )
        row = cur.fetchone()
    return row["status"] if row else None


def finish_clone_run(conn, clone_run_id: int) -> None:
    """Recalculate environments.locked for this run's target (schema helper)."""
    with conn.cursor() as cur:
        cur.execute("SELECT finish_clone_run(%s)", (clone_run_id,))
    conn.commit()


def get_failed_step(conn, clone_run_id: int) -> dict | None:
    """Latest FAILED step for this run (highest clone_function_run_id)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                cfrs.clone_function_run_id,
                cfrs.function_id,
                cf.function_name
            FROM clone_function_run_status cfrs
            JOIN clone_functions cf ON cf.function_id = cfrs.function_id
            WHERE cfrs.clone_run_id = %s
              AND cfrs.status = 'FAILED'
            ORDER BY cfrs.clone_function_run_id DESC
            LIMIT 1
            """,
            (clone_run_id,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def wait_for_operator(conn, clone_run_id: int, failed_step: dict | None) -> str:
    """
    After a step FAILS, poll until the operator acts via the dashboard backend.

    Returns: 'RETRY' | 'SKIP' | 'ABORTED'
    """
    log.info("[run=%s] Step failed. Waiting for operator (RETRY / SKIP / ABORT)...", clone_run_id)
    failed_pk = failed_step["clone_function_run_id"] if failed_step else -1

    while True:
        if _shutdown:
            return "ABORTED"

        run_status = get_latest_run_status(conn, clone_run_id)
        if run_status == "ABORTED":
            return "ABORTED"

        with conn.cursor() as cur:
            # New PENDING attempt after the failed row → retry.
            cur.execute(
                """
                SELECT status
                FROM clone_function_run_status
                WHERE clone_run_id = %s
                  AND clone_function_run_id > %s
                  AND status = 'PENDING'
                ORDER BY clone_function_run_id DESC
                LIMIT 1
                """,
                (clone_run_id, failed_pk),
            )
            retry_row = cur.fetchone()
            if retry_row:
                log.info("[run=%s] Operator chose RETRY — new PENDING step detected", clone_run_id)
                return "RETRY"

            # SKIPPED row inserted for the failed step → skip and continue.
            cur.execute(
                """
                SELECT status
                FROM clone_function_run_status
                WHERE clone_run_id = %s
                  AND clone_function_run_id > %s
                  AND status = 'SKIPPED'
                ORDER BY clone_function_run_id DESC
                LIMIT 1
                """,
                (clone_run_id, failed_pk),
            )
            skip_row = cur.fetchone()
            if skip_row:
                log.info("[run=%s] Operator chose SKIP — SKIPPED step detected", clone_run_id)
                return "SKIP"

        time.sleep(POLL_INTERVAL)


def run(cmd: list[str], label: str, *, env: dict[str, str] | None = None) -> int:
    log.info("%s → %s", label, " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            check=False,
            env=env or os.environ.copy(),
            timeout=_SUBPROCESS_TIMEOUT,
        )
        log.info("%s exited with code %s", label, result.returncode)
        return result.returncode
    except subprocess.TimeoutExpired:
        log.error("%s timed out after %ss", label, _SUBPROCESS_TIMEOUT)
        return -1
    except FileNotFoundError:
        log.error("%s script not found: %s", label, cmd[0])
        return -1
    except Exception as exc:
        log.error("%s unexpected error: %s", label, exc)
        return -1


def execute_job(conn, job: dict, dbname: str, script_env: dict[str, str]):
    clone_run_id = validate_clone_run_id(job["clone_run_id"])
    validate_dbname(dbname)
    source_name = job["source_name"]

    log.info(
        "[run=%s] Starting: %s → %s (user: %s)",
        clone_run_id,
        source_name,
        job["target_name"],
        job["user_name"],
    )

    log_path = resolve_clone_log_path(dbname, clone_run_id)
    if log_path:
        set_run_log_location(conn, clone_run_id, log_path)
    else:
        log.warning("[run=%s] Could not resolve clone log path", clone_run_id)

    while True:
        exit_code = run(
            [MASTER_CLONE_SH, dbname, str(clone_run_id)],
            label=f"[run={clone_run_id}] master_clone.sh",
            env=script_env,
        )

        if log_path:
            set_run_log_location(conn, clone_run_id, log_path)

        if exit_code == 0:
            run_status = get_latest_run_status(conn, clone_run_id)
            log.info(
                "[run=%s] master_clone.sh completed (run status: %s)",
                clone_run_id,
                run_status or "unknown",
            )
            finish_clone_run(conn, clone_run_id)
            log.info("[run=%s] Job finished — target lock recalculated", clone_run_id)
            return

        log.warning(
            "[run=%s] master_clone.sh exited %s — step failed",
            clone_run_id,
            exit_code,
        )

        failed_step = get_failed_step(conn, clone_run_id)
        if failed_step:
            log.warning(
                "[run=%s] Failed step: %s (function_id=%s, clone_function_run_id=%s)",
                clone_run_id,
                failed_step["function_name"],
                failed_step["function_id"],
                failed_step["clone_function_run_id"],
            )

        action = wait_for_operator(conn, clone_run_id, failed_step)

        if action == "RETRY":
            log.info("[run=%s] Retrying — relaunching master_clone.sh", clone_run_id)
            continue

        if action == "SKIP":
            log.info("[run=%s] Skipping failed step — running skip_function.sh", clone_run_id)
            run(
                [SKIP_FUNCTION_SH, dbname, str(clone_run_id)],
                label=f"[run={clone_run_id}] skip_function.sh",
                env=script_env,
            )
            log.info("[run=%s] Relaunching master_clone.sh from next step", clone_run_id)
            continue

        if action == "ABORTED":
            log.warning("[run=%s] ABORT received — running cleanup scripts", clone_run_id)
            run(
                [NULLIFY_CLONE_SH, dbname, str(clone_run_id)],
                label=f"[run={clone_run_id}] nullify_clone_control.sh",
                env=script_env,
            )
            run(
                [ABORT_CLONE_SH, dbname, str(clone_run_id)],
                label=f"[run={clone_run_id}] abort_clone.sh",
                env=script_env,
            )
            finish_clone_run(conn, clone_run_id)
            log.warning("[run=%s] Job ABORTED — target lock recalculated", clone_run_id)
            return


def main():
    log.info("=" * 60)
    log.info("VIGT Clone Agent starting")
    log.info("  Instance env_id : %s", INSTANCE_ENV_ID)
    log.info("  master_clone.sh : %s", MASTER_CLONE_SH)
    log.info("  Poll interval   : %ss", POLL_INTERVAL)
    log.info("=" * 60)

    try:
        conn = get_conn()
        instance_env = verify_instance_env(conn)
        dbname = script_dbname(instance_env)
        script_env = pg_subprocess_env()
        conn.close()
        log.info(
            "  Instance env    : %s (locked=%s, script dbname=%s)",
            instance_env["env_name"],
            instance_env["locked"],
            dbname,
        )
    except psycopg2.OperationalError as exc:
        log.error("Cannot connect to database at startup: %s", exc)
        sys.exit(1)

    while not _shutdown:
        conn = None
        try:
            conn = get_conn()
            job = fetch_pending_job(conn)

            if not job:
                log.debug("No pending jobs — sleeping %ss", POLL_INTERVAL)
                conn.close()
                time.sleep(POLL_INTERVAL)
                continue

            execute_job(conn, job, dbname, script_env)

        except psycopg2.OperationalError as exc:
            log.error("DB connection error: %s — retrying in %ss", exc, POLL_INTERVAL)
            time.sleep(POLL_INTERVAL)

        except Exception as exc:
            log.exception("Unexpected error: %s", exc)
            time.sleep(POLL_INTERVAL)

        finally:
            if conn and not conn.closed:
                conn.close()

    log.info("VIGT Clone Agent shut down cleanly.")


if __name__ == "__main__":
    main()
