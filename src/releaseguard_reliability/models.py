from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
class Attempt(Contract):
    number: int = Field(ge=1)
    outcome: Literal["success", "retry", "failed", "fallback"]
    error_type: str | None = None
    delay_ms: float = Field(ge=0)
class CallResult(Contract):
    status: Literal["success", "fallback", "failed", "rejected"]
    value: str | None
    attempts: tuple[Attempt, ...]
    circuit_state: CircuitState
    error_type: str | None = None
class ReliabilityConfig(Contract):
    max_retries: int = Field(default=2, ge=0, le=10)
    timeout_seconds: float = Field(default=2, gt=0)
    backoff_base_seconds: float = Field(default=0.1, ge=0)
    backoff_jitter_seconds: float = Field(default=0, ge=0)
    failure_threshold: int = Field(default=3, ge=1)
    recovery_timeout_seconds: float = Field(default=10, gt=0)
    rate_limit_per_second: float = Field(default=10, gt=0)
    concurrency_limit: int = Field(default=4, ge=1)

