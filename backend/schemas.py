"""Pydantic response models for the read endpoints."""

from datetime import datetime

from pydantic import BaseModel


class CloneRunOut(BaseModel):
    """One row from ``clone_run_status`` (with ``client_name`` joined in)."""

    clone_run_id: int
    client_id: int
    client_name: str
    user_id: int
    user_name: str
    source_env_id: int
    target_env_id: int
    source_name: str
    target_name: str
    status: str
    start_date: datetime | None = None
    last_update: datetime | None = None
    log_location: str | None = None

    model_config = {"from_attributes": True}


class CloneFunctionRunOut(BaseModel):
    """One step row from ``clone_function_run_status`` (latest attempt)."""

    clone_function_run_id: int
    clone_run_id: int
    function_id: int
    function_name: str
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    step_func_log_location: str | None = None
    retry_count: int | None = None

    model_config = {"from_attributes": True}
