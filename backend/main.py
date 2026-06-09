"""FastAPI backend for the Clone Automation dashboard.

Run locally with:
    uvicorn main:app --reload --port 8000
(from inside the ``backend/`` directory)
"""

from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="Clone Automation API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Liveness/health check. Returns HTTP 200 when the service is up."""
    return {
        "status": "ok",
        "service": "clone-automation-api",
        "time": datetime.now(timezone.utc).isoformat(),
    }
