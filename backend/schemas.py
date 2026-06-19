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
    env_lock: bool = False
    start_date: datetime | None = None
    last_update: datetime | None = None
    log_location: str | None = None
    failed_function_name: str | None = None

    model_config = {"from_attributes": True}


class RunFiltersOut(BaseModel):
    """Distinct values for Run History filter dropdowns."""

    clients: list[str]
    targets: list[str]
    users: list[str]


class RunActionIn(BaseModel):
    """Optional body for abort/skip/retry — pin the failed function step to act on."""

    clone_function_run_id: int | None = None


class RunActionOut(BaseModel):
    """Response after aborting, skipping, or retrying a failed clone run."""

    clone_run_id: int
    status: str
    message: str
    clone_function_run_id: int | None = None


class UserOption(BaseModel):
    """User available for triggering a clone run."""

    user_id: int
    user_name: str
    client_id: int
    client_name: str

    model_config = {"from_attributes": True}


class EnvironmentOption(BaseModel):
    """Environment that can be selected as a clone source or target.

    ``locked`` is derived: another run holds ``env_lock`` on this target.
    """

    env_id: int
    env_name: str
    client_id: int
    client_name: str
    locked: bool

    model_config = {"from_attributes": True}


class ExecuteCloneOptionsOut(BaseModel):
    """Dropdown options for the Execute Clone page."""

    users: list[UserOption]
    environments: list[EnvironmentOption]


class CreateCloneRunIn(BaseModel):
    """Body for triggering a new clone run."""

    user_id: int
    source_env_id: int
    target_env_id: int


class CreateCloneRunOut(BaseModel):
    """Response after ``create_clone_run`` succeeds."""

    clone_run_id: int
    status: str
    source_name: str
    target_name: str
    user_name: str
    message: str


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


class FunctionStepAttemptOut(BaseModel):
    """One attempt row for a clone function within a clone run."""

    clone_function_run_id: int
    attempt_number: int
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    step_func_log_location: str | None = None
    is_current: bool = False

    model_config = {"from_attributes": True}


class FunctionStepDetailOut(BaseModel):
    """Detailed view of one function-step row and its attempt history."""

    clone_function_run_id: int
    clone_run_id: int
    function_id: int
    function_name: str
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    step_func_log_location: str | None = None
    base_pk: int
    attempt_number: int
    attempts: list[FunctionStepAttemptOut]

    model_config = {"from_attributes": True}


class StepFailureSummaryOut(BaseModel):
    """Failure count for one clone step across all runs (``idx_cfrs_status``)."""

    function_id: int
    function_name: str
    failure_count: int

    model_config = {"from_attributes": True}


class FunctionFailureHistoryOut(BaseModel):
    """One FAILED attempt for a step across runs (``idx_cfrs_function_id``)."""

    clone_run_id: int
    clone_function_run_id: int
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None

    model_config = {"from_attributes": True}
