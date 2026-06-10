# Loose Ends & Audit Notes

Audit of the **frontend-streamlit-only** repo: known gaps, hardcoded values, and breakage risks.

Last updated after central logging and error-handling pass.

---

## Fixed in this pass

| Issue | Fix |
|-------|-----|
| No `.env` → cryptic import errors | `ConfigurationError` + clear message in `app.py` |
| `.env*` gitignore hid `.env.example` | `.gitignore` now keeps `!.env.example` |
| Silent `except Exception: pass` in API client | `BackendError` with status codes + logging |
| No request logging on backend | `RequestLoggingMiddleware` + structured log lines |
| DB errors bubbled as 500 tracebacks | `@app.exception_handler(SQLAlchemyError)` → 503 JSON |
| Missing `import os` in `main.py` | Restored (log download routes) |
| Assets missing crashed CSS import | `_asset_data_uri` returns `""` on missing files |
| Agent vars required for dashboard | Agent settings only validated when `agent()` is called |
| Scattered `st.error` strings | `frontend/ui_errors.py` + `show_error()` |

---

## Remaining loose ends (may still break)

### Critical — must exist before running

| Item | Risk | Action |
|------|------|--------|
| **No `.env` file** | App/API won't start | `copy .env.example .env` and edit |
| **PostgreSQL not running / schema missing** | All API routes return 503 | Apply `schema.sql`, seed clients/users/envs |
| **Backend not running** | Streamlit shows offline; pages empty | Start `uvicorn` before Streamlit |
| **`REQUIRE_API_KEY=true` without `API_KEY`** | API returns 503 | Set matching `API_KEY` on FE + BE, or disable auth |

### Missing from this repo snapshot

These are referenced in README but **not present** in the current directory:

- `agent.py` — no target-side job runner
- `master_clone.sh`, `skip_function.sh`, `abort_clone.sh`, `nullify_clone_control.sh`, `vigt_validate_args.sh`
- `schema.sql` — database DDL

The **dashboard and API work without them**; clone execution cannot run end-to-end until restored.

### Hardcoded values (intentional)

| Location | Value | Notes |
|----------|-------|-------|
| `frontend/app.py`, `styles.py`, `.streamlit/config.toml` | Brand colors `#e87511`, etc. | UI branding — not in `.env` by design |
| `frontend/styles.py` `NAV` | Page titles, icons, modules | App structure |
| `backend/main.py` | `version="0.1.0"`, service name | Metadata only |

### Configuration gaps

| Item | Risk |
|------|------|
| `LOG_ALLOWED_ROOTS` on Windows | Default `/u02/shared` won't match local log paths — set to your log directory |
| Empty agent script paths in `.env` | Fine for dashboard; **required** when `agent.py` is restored |
| `INSTANCE_ENV_ID=2` in `.env.example` | Must match your `environments` table when using agent |
| Uvicorn port vs `API_PORT` | Port is in `.env` for documentation; you still pass `--port` to uvicorn manually |

### Functional gaps (not bugs)

| Area | Status |
|------|--------|
| Home, DB Config, EBS Config, Integrations | Placeholder pages |
| Clients, Team, Targets | Nav disabled — "Coming soon" |
| User login / roles | Schema supports it; UI has no auth |
| `/health` | Does not check DB connectivity (liveness only) |

### Error-handling limits

- Streamlit reruns can log the same error multiple times — expected behavior.
- Log download links embed `api_key` in the URL when auth is enabled — don't share URLs.
- `get_run()` falls back to scanning run list if single-run endpoint fails — extra API call, logged at DEBUG.

---

## Central logging

All Python services use `config/logging.py`:

```python
from config.logging import setup_logging
log = setup_logging("api")       # backend
log = setup_logging("frontend")  # streamlit entry
log = setup_logging("frontend.api")
log = setup_logging("frontend.ui")
log = setup_logging("api.db")
```

**Env vars:** `LOG_LEVEL`, `LOG_DIR`, `LOG_TO_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`

Log file (when enabled): `logs/vigt.log` under repo root (or `LOG_DIR`).

---

## Quick pre-flight checklist

1. [ ] `copy .env.example .env` and set `DB_*`, `BACKEND_URL`
2. [ ] PostgreSQL up with schema + seed data
3. [ ] `pip install -r requirements.txt` and `pip install -r backend/requirements.txt`
4. [ ] Start backend from `backend/`: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. [ ] Start frontend from repo root: `streamlit run frontend/app.py`
6. [ ] Sidebar green dot = backend reachable
7. [ ] Set `LOG_ALLOWED_ROOTS` before using Download Log in production
