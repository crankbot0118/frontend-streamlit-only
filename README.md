# VIGT Clone Automation — Project Reference

Complete reference for the **Clone Automation Dashboard** (VIGT): a web UI and API for triggering, monitoring, and managing Oracle EBS environment clone jobs across multiple clients and target instances.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [Repository Layout](#4-repository-layout)
5. [Data Model (PostgreSQL)](#5-data-model-postgresql)
6. [End-to-End Clone Workflow](#6-end-to-end-clone-workflow)
7. [Status Model and Rollups](#7-status-model-and-rollups)
8. [Frontend (Streamlit)](#8-frontend-streamlit)
9. [Backend (FastAPI)](#9-backend-fastapi)
10. [Target Agent (`agent.py`)](#10-target-agent-agentpy)
11. [Shell Scripts](#11-shell-scripts)
12. [API Reference](#12-api-reference)
13. [Environment Variables](#13-environment-variables)
14. [Security](#14-security)
15. [Running Locally](#15-running-locally)
16. [UI Pages Guide](#16-ui-pages-guide)
17. [Key Design Decisions](#17-key-design-decisions)
18. [Extending the Project](#18-extending-the-project)

---

## 1. What This Project Does

VIGT automates **Oracle EBS (E-Business Suite) clone/refresh** operations: copying a production (or source) environment onto a non-production target (UAT, DEV, etc.).

Operators use a **Streamlit dashboard** to:

- Trigger new clone jobs (source → target)
- Monitor run history and live step progress
- Download master and per-step logs
- **Abort** or **Skip** failed steps and let execution continue or stop

Behind the UI:

- A **FastAPI backend** reads/writes PostgreSQL and serves log files
- One **Python agent per target server** polls for pending jobs and runs shell automation
- **`master_clone.sh`** executes 36 predefined clone steps, updating the database as each step runs

The system is **multi-tenant**: clients, users, environments, and runs are scoped per client.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Operator Browser                                 │
│                    Streamlit Dashboard (port 8501)                       │
│   frontend/app.py  +  app_pages/*  +  api.py  +  styles.py            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP (JSON + log downloads)
                                │ Header: X-API-Key
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                           │
│              backend/main.py  +  crud.py  +  security.py                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ SQLAlchemy / psycopg2
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL                                       │
│   schema.sql — tables, triggers, create_clone_run(), finish_clone_run() │
└───────────────▲─────────────────────────────────────▲───────────────────┘
                │                                     │
                │ direct psycopg2                     │ direct psql via shell
                │                                     │
┌───────────────┴──────────────┐    ┌─────────────────┴───────────────────┐
│   agent.py (per target)      │    │   master_clone.sh + helper scripts   │
│   Polls PENDING jobs         │───▶│   Runs on target EBS instance        │
│   Runs master_clone.sh       │    │   Updates clone_function_run_status  │
└──────────────────────────────┘    └───────────────────────────────────────┘
```

**Data flow for a new clone:**

1. Operator submits **Execute Clone** form → backend calls `create_clone_run()` → 1 run row + 36 PENDING step rows; target env locked
2. Target **agent** picks up the PENDING job → runs `master_clone.sh`
3. Shell script updates step rows (RUNNING → COMPLETED/FAILED); DB trigger rolls up run status
4. Dashboard polls steps (auto-refresh every 3s on Run Details)
5. On failure: operator chooses **Skip** or **Abort** in UI → backend inserts status rows → agent reacts

---

## 3. Technology Stack

| Layer | Technology |
|-------|------------|
| UI | [Streamlit](https://streamlit.io/) multipage app, custom CSS, Material icons |
| API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Database | PostgreSQL (schema in `schema.sql`) |
| ORM | SQLAlchemy 2.x (raw SQL via `text()` — no ORM models for tables) |
| Agent | Python 3 + psycopg2 + python-dotenv |
| Automation | POSIX shell (`master_clone.sh`, helpers) |
| Auth | Shared secret API key (`API_KEY` env var) |

**Frontend dependencies:** Streamlit only (HTTP client uses stdlib `urllib`).

**Backend dependencies:** See `backend/requirements.txt`.

---

## 4. Repository Layout

```
frontend-streamlit-only/
├── frontend/
│   ├── app.py                 # Streamlit entry point, sidebar, page registry
│   ├── api.py                 # HTTP client for backend (stdlib urllib)
│   ├── styles.py              # Global CSS, nav, shared UI helpers
│   └── app_pages/
│       ├── home.py            # Landing page (placeholder content)
│       ├── execute_clone.py   # Trigger new clone runs
│       ├── run_history.py     # Filterable list of past runs
│       ├── run_details.py     # Step list, abort/skip, auto-refresh
│       ├── db_config.py       # Placeholder
│       ├── ebs_config.py      # Placeholder
│       ├── integrations.py    # Placeholder
│       ├── clients.py         # Placeholder (nav disabled)
│       ├── team.py            # Placeholder (nav disabled)
│       └── targets.py         # Placeholder (nav disabled)
├── backend/
│   ├── main.py                # FastAPI routes
│   ├── crud.py                # SQL queries and business logic
│   ├── schemas.py             # Pydantic request/response models
│   ├── database.py            # SQLAlchemy engine + get_db()
│   ├── security.py            # API key, rate limit, log path validation
│   └── requirements.txt
├── agent.py                   # Target-instance job poller + script launcher
├── schema.sql                 # Full PostgreSQL DDL, seeds, triggers, functions
├── master_clone.sh            # 36-step clone driver (updates DB per step)
├── skip_function.sh           # Advance checkpoint after operator SKIP
├── abort_clone.sh             # Target cleanup after operator ABORT
├── nullify_clone_control.sh   # Reset clone control file on ABORT
├── vigt_validate_args.sh      # Shared arg validation for shell scripts
├── assets/                    # logo.svg, status icons (referenced by styles.py)
├── .streamlit/config.toml     # Light theme, minimal toolbar
└── PROJECT_REFERENCE.md       # This document
```

---

## 5. Data Model (PostgreSQL)

Apply `schema.sql` to create the database. Key objects:

### 5.1 Enum Types

| Enum | Values |
|------|--------|
| `clone_status` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`, `ABORTED` |
| `vigt_role` | `ADMIN`, `VIEWER` |

### 5.2 Core Tables

| Table | Purpose |
|-------|---------|
| `clients` | Tenant organisations |
| `users` | Login accounts (bcrypt password via `pgcrypto`) |
| `user_roles` | Role assignments per user/client |
| `environments` | EBS instances (source or target); `locked` flag prevents concurrent target clones |
| `clone_functions` | Master list of **36 clone steps** (function_id 0, 10, … 350) |
| `clone_run_status` | One row per clone job (append-only status history on abort/skip) |
| `clone_function_run_status` | One row per **step attempt** (supports retries) |

### 5.3 ID Conventions

**Clone run IDs** — multiples of 1000 (1000, 2000, …), from sequence `clone_run_id_seq`:

```
clone_run_id = nextval('clone_run_id_seq')  -- START 1000, INCREMENT 1000
```

**Step primary keys** — formula leaves room for up to 10 retries per step:

```
clone_function_run_id = clone_run_id + 1 + (function_id * 2) + attempt_offset
```

Example for run `1000`:

| function_id | Step name (sample) | Base PK |
|-------------|-------------------|---------|
| 0 | apps_shutdown | 1001 |
| 10 | db_shutdown | 1021 |
| 350 | ebs_final_apps_startall | 1701 |

Retries insert new rows with `clone_function_run_id = base_pk + attempt_number` (max 9 retries).

### 5.4 The 36 Clone Steps

Seeded in `clone_functions` (function_id → name):

```
0   apps_shutdown              180 ebs_adcfg_primary_node
10  db_shutdown                190 ebs_adcfg_secondary_node
20  db_mount_restrict          200 ebs_fndcpass
30  db_drop                    210 ebs_start_run_admin_server
40  db_nomount                 220 ebs_context_updates
50  db_restore                 230 ebs_soft_link_updates
60  db_startup                 240 ebs_autoconfig
70  db_validate_temp           250 ebs_profile_resp_conc_updates
80  db_rename_cdb              260 ebs_custom_updates
90  db_rename_pdb              270 ebs_stop_run_admin_server
100 db_util_file               280 ebs_integrations
110 db_conc_clean              290 ebs_custom_patch_fs_updates
120 db_autoconfig              300 ebs_final_apps_shutdown
130 db_custom_users            310 db_final_shutdown
140 db_custom_directories      320 db_final_startup
150 ebs_binaries_cleanup       330 db_final_autoconfig
160 ebs_binaries_download      340 ebs_final_autoconfig
170 ebs_binaries_untar         350 ebs_final_apps_startall
```

### 5.5 Database Functions and Triggers

| Object | Role |
|--------|------|
| `create_clone_run(client_id, user_id, source_env_id, target_env_id)` | Atomically inserts run + 36 PENDING steps; rejects if target locked |
| `finish_clone_run(run_id)` | Recalculates `environments.locked` for the run's target |
| `sync_clone_run_status()` + `trg_sync_run_status` | After step INSERT/UPDATE: rolls up parent run status |
| `sync_env_lock()` + `trg_sync_env_lock` | Locks target when run is PENDING/RUNNING/FAILED |

**Run status rollup priority:** `ABORTED > FAILED > RUNNING > COMPLETED > PENDING`

A run becomes `COMPLETED` when every step is `COMPLETED` or `SKIPPED`.

### 5.6 Append-Only Status History

Both `clone_run_status` and `clone_function_run_status` support **history rows**. The backend always reads the **latest row per `clone_run_id`** using:

```sql
SELECT DISTINCT ON (clone_run_id) ...
FROM clone_run_status
ORDER BY clone_run_id, last_update DESC NULLS LAST, clone_run_id DESC
```

Abort/Skip actions **INSERT** new rows rather than UPDATE existing ones.

---

## 6. End-to-End Clone Workflow

### 6.1 Trigger (Dashboard)

1. Operator opens **Execute Clone**
2. Selects user, source env, target env (same client; target ≠ source; target ≠ PROD; target not locked)
3. Clicks **Trigger job** → `POST /api/v1/execute-clone/trigger`
4. Backend validates and calls `create_clone_run()` → returns `clone_run_id`
5. UI redirects to **Run Details** with auto-refresh enabled

### 6.2 Execution (Agent + Shell)

1. `agent.py` on the **target** polls for oldest `PENDING` job where `target_env_id = INSTANCE_ENV_ID`
2. Resolves log path from instance `*_db.env` (or `CLONE_LOG` override)
3. Writes `log_location` on the run row
4. Executes: `master_clone.sh <dbname> <clone_run_id>`
5. Script sources instance env, runs steps in order, calling `vigt_step_start/done/fail` helpers that UPDATE/INSERT into `clone_function_run_status`
6. On script exit code 0 → agent calls `finish_clone_run()` to unlock target if appropriate

### 6.3 Failure Handling

When a step fails (`master_clone.sh` exits non-zero):

1. Run status becomes `FAILED` (via trigger)
2. Agent enters `wait_for_operator()` loop, polling every `POLL_INTERVAL` seconds
3. Operator on **Run Details** clicks **Skip** or **Abort** (only enabled when status is FAILED)

| Operator action | Backend | Agent detects | Agent runs |
|----------------|---------|---------------|------------|
| **Skip** | Inserts SKIPPED rows for failed step + run | New SKIPPED step row | `skip_function.sh` → relaunch `master_clone.sh` |
| **Abort** | Inserts ABORTED rows | Run status ABORTED | `nullify_clone_control.sh` + `abort_clone.sh` → `finish_clone_run()` |
| **Retry** (implicit) | Shell/master inserts new PENDING attempt row | New PENDING row after failed PK | Relaunch `master_clone.sh` |

---

## 7. Status Model and Rollups

### Step-level statuses

| Status | Meaning |
|--------|---------|
| `PENDING` | Created, not started |
| `RUNNING` | Currently executing |
| `COMPLETED` | Finished successfully |
| `FAILED` | Error; waits for operator |
| `SKIPPED` | Operator bypassed this step |
| `ABORTED` | Operator terminated the run |

### Environment locking

Target `environments.locked = TRUE` when **any** latest run for that target has status in:

`PENDING`, `RUNNING`, `FAILED`

Lock clears when all such runs reach terminal states (`COMPLETED`, `ABORTED`, or fully skipped through).

### UI status colors

Defined in `frontend/styles.py`:

| Status | Badge color |
|--------|-------------|
| COMPLETED | green |
| RUNNING | blue |
| PENDING | gray |
| FAILED | red |
| SKIPPED | orange |
| ABORTED | violet |

---

## 8. Frontend (Streamlit)

### 8.1 Entry Point — `frontend/app.py`

- Sets light theme (`st.set_theme` when available)
- `st.set_page_config`: wide layout, expanded sidebar
- Builds page registry via `build_pages()` from `styles.py`
- Uses `st.navigation(..., position="hidden")` — custom sidebar only
- Sidebar: logo, nav, backend health indicator (green pulse = live)

**Run from repo root** so `.streamlit/config.toml` is picked up:

```bash
streamlit run frontend/app.py
```

### 8.2 API Client — `frontend/api.py`

| Function | Backend endpoint |
|----------|------------------|
| `check_backend_health()` | `GET /health` (no API key) |
| `get_run_filters()` | `GET /api/v1/runs/filters` |
| `get_runs(...)` | `GET /api/v1/runs` |
| `get_run(id)` | `GET /api/v1/runs/{id}` |
| `get_run_steps(id)` | `GET /api/v1/runs/{id}/steps` |
| `get_step_detail(...)` | `GET /api/v1/runs/{id}/steps/{step_id}` |
| `run_log_url(id)` | Signed URL for log download |
| `step_log_url(...)` | Signed URL for step log |
| `abort_run(...)` | `POST /api/v1/runs/{id}/abort` |
| `skip_run(...)` | `POST /api/v1/runs/{id}/skip` |
| `get_execute_clone_options()` | `GET /api/v1/execute-clone/options` |
| `trigger_clone_run(...)` | `POST /api/v1/execute-clone/trigger` |

**Env vars:** `BACKEND_URL` (default `http://localhost:8000`), `API_KEY`.

Log download links append `?api_key=...` for browser access.

### 8.3 Navigation — `styles.py` `NAV` registry

| Section | Pages | Notes |
|---------|-------|-------|
| Top | Home | Default page |
| Admin (group) | Clients, Team, Targets | **Disabled** — "Coming soon!" |
| Clone Setup (group) | DB Config, EBS Config, Integrations | Placeholder content |
| — divider — | | |
| Actions | Execute Clone, Run History | Fully wired to backend |
| Hidden | Run details | Reachable via `st.switch_page` / card click |

Helper functions: `render_title`, `render_run_card`, `render_sidebar_nav`, `goto_page`, `status_badge_html`, etc.

### 8.4 Session State and Deep Linking

**Run Details** persists selection via:

- `st.session_state["selected_run_id"]`
- URL query param `?run=<clone_run_id>` (survives browser refresh)

Auto-refresh: `st.fragment(run_every=3)` when toggle is on.

---

## 9. Backend (FastAPI)

### 9.1 Startup

From `backend/` directory:

```bash
uvicorn main:app --reload --port 8000
```

### 9.2 Middleware Stack

1. **CORS** — origins from `ALLOWED_ORIGINS` (default Streamlit URLs)
2. **Rate limiting** — `RATE_LIMIT_REQUESTS` per `RATE_LIMIT_WINDOW_SEC` per client IP
3. **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, etc.

### 9.3 Global Dependency

All routes except `/health` require API key via `verify_api_key`:

- Header: `X-API-Key: <secret>`
- Or query param: `?api_key=<secret>` (for log downloads in browser)

### 9.4 CRUD Highlights — `backend/crud.py`

| Function | Description |
|----------|-------------|
| `get_clone_runs` | Latest run rows with optional filters |
| `get_run_steps` | Latest attempt per function_id, ordered by step |
| `get_function_step_detail` | Step row + full attempt history |
| `trigger_clone_run` | Validates business rules, calls `create_clone_run()` |
| `mark_run_action` | Abort/Skip: inserts new status rows |

**Business rules in `trigger_clone_run`:**

- User, source, target must exist
- Source and target must belong to user's client
- Source ≠ target
- Target cannot be named PROD
- Target must not be locked (also enforced in SQL)

**Business rules in `mark_run_action`:**

- Latest run status must be `FAILED`
- Must have a failed function step

### 9.5 Log Serving

Log endpoints resolve `log_location` / `step_func_log_location`:

- **HTTP(S) URL** → redirect (only if `ALLOW_LOG_URL_REDIRECT=true`)
- **Local path** → `FileResponse` if file exists and path is under `LOG_ALLOWED_ROOTS` (default `/u02/shared`)

---

## 10. Target Agent (`agent.py`)

One agent process runs on **each non-PROD target instance**.

### Responsibilities

- Connect to PostgreSQL using `~/.env` credentials
- Verify `INSTANCE_ENV_ID` exists and is not PROD
- Poll for PENDING jobs assigned to this target
- Run `master_clone.sh`, handle failures, wait for operator actions
- Call `finish_clone_run()` when job completes or is aborted

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection |
| `INSTANCE_ENV_ID` | This machine's `environments.env_id` |
| `MASTER_CLONE_SH` | Full path to `master_clone.sh` |
| `SKIP_FUNCTION_SH` | Full path to `skip_function.sh` |
| `NULLIFY_CLONE_SH` | Full path to `nullify_clone_control.sh` |
| `ABORT_CLONE_SH` | Full path to `abort_clone.sh` |

### Optional

| Variable | Default |
|----------|---------|
| `INSTANCE_DBNAME` | Lowercased `env_name` |
| `POLL_INTERVAL` | `10` (seconds) |
| `INSTANCE_CLONE_DIR` | `/u02/shared/AUTOMATION/Clone_Auto/Instances` |
| `CLONE_LOG` | Resolved from instance `*_db.env` |
| `SUBPROCESS_TIMEOUT` | None (no timeout) |

### Safety

- Validates dbname and clone_run_id before passing to shell (regex `^[a-zA-Z0-9_-]+$`)
- Graceful shutdown on SIGINT/SIGTERM

---

## 11. Shell Scripts

### `master_clone.sh <dbname> <clone_run_id>`

Main clone driver on the target. Arguments:

- `$1` — instance key under `INSTANCE_CLONE_DIR` (e.g. `uat`)
- `$2` — clone run ID from agent

Sources `${INSTANCE_CLONE_DIR}/${1}/env/DB/${1}_db.env` for paths and config.

**VIGT DB helpers** (defined in script):

| Function | Effect |
|----------|--------|
| `vigt_step_start(id)` | Set step RUNNING, stamp start_time |
| `vigt_step_done(id)` | Set step COMPLETED, stamp end_time |
| `vigt_step_fail(id)` | Set step FAILED |
| `vigt_fail_run()` | Mark current step failed on script error exit |
| `vigt_set_log_location()` | Write master log path to run row |

Uses `PGHOST`/`PG*` env vars (set by agent subprocess env).

### `skip_function.sh`

Advances clone control checkpoint so `master_clone.sh` resumes at the **next** function after a SKIPPED step.

### `nullify_clone_control.sh`

Resets clone control state when operator aborts.

### `abort_clone.sh`

Placeholder for target-side cleanup after abort (extend with real commands).

### `vigt_validate_args.sh`

Shared validation: rejects invalid dbname/clone_run_id before any script runs.

---

## 12. API Reference

Base URL: `{BACKEND_URL}` (default `http://localhost:8000`)

Authentication: `X-API-Key` header on all routes except `/health`.

### Health

| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/health` | No | `{ status, service, time }` |

### Runs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/runs/filters` | Distinct clients, targets, users for filters |
| GET | `/api/v1/runs` | List runs (`limit`, `client`, `target`, `user`, `start_date` query params) |
| GET | `/api/v1/runs/{clone_run_id}` | Single run |
| GET | `/api/v1/runs/{clone_run_id}/log` | Download master log |
| GET | `/api/v1/runs/{clone_run_id}/steps` | Latest step per function |
| GET | `/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}` | Step detail + attempts |
| GET | `/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}/log` | Download step log |
| POST | `/api/v1/runs/{clone_run_id}/abort` | Abort failed run (optional body: `{ clone_function_run_id }`) |
| POST | `/api/v1/runs/{clone_run_id}/skip` | Skip failed step (optional body: `{ clone_function_run_id }`) |

### Execute Clone

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/execute-clone/options` | Users and environments for form |
| POST | `/api/v1/execute-clone/trigger` | Body: `{ user_id, source_env_id, target_env_id }` |

OpenAPI docs available at `/docs` when `ENABLE_DOCS=true`.

### Response Models

See `backend/schemas.py` for full Pydantic models: `CloneRunOut`, `CloneFunctionRunOut`, `FunctionStepDetailOut`, `CreateCloneRunOut`, etc.

---

## 13. Environment Variables

### Shared (`~/.env` — used by backend, agent)

| Variable | Required by | Description |
|----------|-------------|-------------|
| `DB_HOST` | Backend, Agent | PostgreSQL host |
| `DB_PORT` | Backend, Agent | PostgreSQL port |
| `DB_NAME` | Backend, Agent | Database name |
| `DB_USER` | Backend, Agent | Database user |
| `DB_PASSWORD` | Backend, Agent | Database password |
| `DB_MIN_CONN` | Backend | Pool size (default 1) |
| `DB_MAX_CONN` | Backend | Max connections (default 10) |

### Backend only

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | (empty) | Shared secret; required if `REQUIRE_API_KEY=true` |
| `REQUIRE_API_KEY` | `true` | Fail closed if no key configured |
| `ALLOWED_ORIGINS` | Streamlit localhost URLs | CORS origins (comma-separated) |
| `LOG_ALLOWED_ROOTS` | `/u02/shared` | Allowed local log path roots (`:` separated) |
| `ALLOW_LOG_URL_REDIRECT` | `false` | Allow redirect to http(s) log URLs |
| `RATE_LIMIT_REQUESTS` | `120` | Max requests per window per IP |
| `RATE_LIMIT_WINDOW_SEC` | `60` | Rate limit window |
| `ENABLE_DOCS` | `false` | Expose `/docs`, `/redoc`, `/openapi.json` |

### Frontend only

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | FastAPI base URL |
| `API_KEY` | (empty) | Sent as `X-API-Key` and in log download URLs |

### Agent only

See [Section 10](#10-target-agent-agentpy).

---

## 14. Security

| Control | Implementation |
|---------|----------------|
| API authentication | Constant-time compare of `API_KEY` |
| Public endpoint | Only `/health` |
| Log path traversal | `resolve_local_log_path()` restricts to `LOG_ALLOWED_ROOTS` |
| Remote log URLs | Disabled by default (`ALLOW_LOG_URL_REDIRECT=false`) |
| Rate limiting | Per-IP sliding window |
| Security headers | nosniff, DENY frame, referrer policy |
| Shell injection | Agent validates dbname/run_id; scripts use `vigt_validate_shell_args` |
| PROD protection | Cannot trigger clone to PROD target; agent refuses PROD `INSTANCE_ENV_ID` |
| CORS | Restricted to configured origins |

**Note:** User/password auth in the schema exists for future use; the Streamlit app currently does not implement login — access control is via API key at the backend layer.

---

## 15. Running Locally

### Prerequisites

- PostgreSQL with `schema.sql` applied
- Seed data: at least one client, user, two environments (source + target)
- Python 3 with Streamlit, FastAPI dependencies, psycopg2

### Typical startup order

1. **Database** — ensure PostgreSQL is running and schema is loaded
2. **Backend** — from `backend/`:
   ```bash
   export API_KEY=your-secret-key
   uvicorn main:app --reload --port 8000
   ```
3. **Frontend** — from repo root:
   ```bash
   export BACKEND_URL=http://localhost:8000
   export API_KEY=your-secret-key
   streamlit run frontend/app.py
   ```
4. **Agent** — on each target server (production-like setup):
   ```bash
   python3 agent.py
   ```

Sidebar shows green pulse when backend `/health` returns 200.

---

## 16. UI Pages Guide

| Page | Status | Functionality |
|------|--------|---------------|
| **Home** | Placeholder | Title + subtitle only |
| **Clients** | Disabled nav | Coming soon |
| **Team** | Disabled nav | Coming soon |
| **Targets** | Disabled nav | Coming soon |
| **DB Config** | Placeholder | Future: DB connection settings |
| **EBS Config** | Placeholder | Future: EBS-specific config |
| **Integrations** | Placeholder | Future: external integrations |
| **Execute Clone** | **Live** | Form → trigger run → redirect to details |
| **Run History** | **Live** | Filters + run cards → open details |
| **Run Details** | **Live** | Steps, abort/skip, logs, auto-refresh, step attempt dialog |

### Run History filters

- Client, Target, User (dropdowns from `/api/v1/runs/filters`)
- Start date (calendar day match on `start_date`)

### Run Details actions

- **Abort / Skip** — only when run status is FAILED
- **Download Log** — master run log via backend
- **Auto refresh** — polls steps every 3 seconds
- Per-step **Details** dialog — attempt history table
- Per-step **Download Step Log** — when `step_func_log_location` is set

---

## 17. Key Design Decisions

1. **Append-only status history** — Abort/Skip and rollups use INSERTs; "latest row" CTE is the source of truth.

2. **Trigger-driven rollups** — Shell scripts only touch step rows; PostgreSQL triggers maintain run status and env locks.

3. **Target-only locking** — Source environments stay available; only the clone target is locked during active/failed runs.

4. **Separation of concerns** — Dashboard never runs shell scripts; agent never serves HTTP. Backend is the only write path from UI.

5. **Stdlib HTTP client** — Frontend has zero extra dependencies beyond Streamlit.

6. **Light theme locked** — CSS + `config.toml` prevent dark mode drift.

7. **Hidden Streamlit nav** — Custom sidebar is the single navigation UX.

8. **PK spacing** — Run IDs (×1000) and function IDs (×10) reserve ID space for retries without collisions.

---

## 18. Extending the Project

### Add a new dashboard page

1. Create `frontend/app_pages/your_page.py`
2. Add entry to `NAV` in `styles.py`
3. Use `render_title`, `apply_global_styles` patterns from existing pages

### Add a new API endpoint

1. Add query/action in `backend/crud.py`
2. Add Pydantic schema in `backend/schemas.py`
3. Register route in `backend/main.py`
4. Add client function in `frontend/api.py`

### Add a clone step

1. Insert into `clone_functions` with next function_id (increment by 10)
2. Implement step logic in `master_clone.sh`
3. Add to `skip_function.sh` step order list
4. `create_clone_run()` loop will pick up new functions automatically

### Wire Admin pages

Remove `"disabled": True` from nav items in `styles.py` and implement CRUD against new backend endpoints.

### Production deployment checklist

- [ ] Set strong `API_KEY`; `REQUIRE_API_KEY=true`
- [ ] Configure `ALLOWED_ORIGINS` for production Streamlit URL
- [ ] Set `LOG_ALLOWED_ROOTS` to actual log directories
- [ ] Keep `ENABLE_DOCS=false` in production
- [ ] Run agent as a supervised service on each target
- [ ] Ensure `assets/` directory exists with logo and status icons
- [ ] Restrict PostgreSQL network access to backend + agents only

---

## Quick Reference Card

```
Trigger clone:     Execute Clone → POST create_clone_run
Monitor:           Run History / Run Details (auto-refresh 3s)
Failed run:        Abort (stop) or Skip (continue next step)
Agent picks up:    status=PENDING AND target_env_id=INSTANCE_ENV_ID
Lock rule:         target locked while run ∈ {PENDING, RUNNING, FAILED}
Step count:        36 functions (function_id 0–350)
Run ID format:     1000, 2000, 3000, …
```

---

*Document generated from repository source. For schema details, always treat `schema.sql` as authoritative.*
