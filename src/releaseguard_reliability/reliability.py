"""Synchronous resilience primitives with injectable time and randomness."""
import random
import time
from collections.abc import Callable
from threading import Lock, Semaphore

from .models import Attempt, CallResult, CircuitState, ReliabilityConfig


class ProviderTimeout(Exception): pass
class ProviderServerError(Exception): pass
class ProviderRateLimit(Exception): pass
class CircuitOpen(Exception): pass

class ResilientProvider:
    def __init__(self, config: ReliabilityConfig | None = None, fallback: Callable[[str], str] | None = None, clock=time.monotonic, sleeper=time.sleep, rng=random.random):
        self.config = config or ReliabilityConfig(); self.fallback = fallback; self.clock = clock; self.sleeper = sleeper; self.rng = rng
        self._lock = Lock(); self._semaphore = Semaphore(self.config.concurrency_limit); self._failures = 0; self._opened_at = None; self._calls: list[float] = []

    @property
    def state(self):
        if self._opened_at is not None and self.clock() - self._opened_at >= self.config.recovery_timeout_seconds:
            return CircuitState.HALF_OPEN
        return CircuitState.OPEN if self._opened_at is not None else CircuitState.CLOSED

    def _admit(self):
        now = self.clock()
        with self._lock:
            self._calls = [stamp for stamp in self._calls if now - stamp < 1]
            if len(self._calls) >= self.config.rate_limit_per_second: raise ProviderRateLimit("local rate limit exceeded")
            self._calls.append(now)

    def _record_failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self.config.failure_threshold: self._opened_at = self.clock()

    def _record_success(self):
        with self._lock: self._failures, self._opened_at = 0, None

    def call(self, request: str, provider: Callable[[str], str]) -> CallResult:
        attempts: list[Attempt] = []
        if self.state == CircuitState.OPEN:
            return self._fallback_or_reject(request, attempts, "CircuitOpen")
        if not self._semaphore.acquire(blocking=False): return self._fallback_or_reject(request, attempts, "ConcurrencyLimit")
        try:
            for number in range(1, self.config.max_retries + 2):
                try:
                    self._admit(); started = self.clock(); value = provider(request)
                    if self.clock() - started > self.config.timeout_seconds: raise ProviderTimeout("provider timeout")
                    self._record_success(); attempts.append(Attempt(number=number, outcome="success", delay_ms=0)); return CallResult(status="success", value=value, attempts=tuple(attempts), circuit_state=self.state)
                except (ProviderTimeout, ProviderServerError, ProviderRateLimit) as exc:
                    retryable = number <= self.config.max_retries
                    delay = self.config.backoff_base_seconds * (2 ** (number - 1)) + self.config.backoff_jitter_seconds * self.rng()
                    attempts.append(Attempt(number=number, outcome="retry" if retryable else "failed", error_type=type(exc).__name__, delay_ms=delay * 1000))
                    self._record_failure()
                    if retryable: self.sleeper(delay)
                    else: return self._fallback_or_reject(request, attempts, type(exc).__name__)
                except Exception as exc:
                    attempts.append(Attempt(number=number, outcome="failed", error_type=type(exc).__name__, delay_ms=0)); self._record_failure(); return self._fallback_or_reject(request, attempts, type(exc).__name__)
        finally: self._semaphore.release()

    def _fallback_or_reject(self, request, attempts, error_type):
        if self.fallback:
            value = self.fallback(request); attempts.append(Attempt(number=len(attempts) + 1, outcome="fallback", error_type=error_type, delay_ms=0)); return CallResult(status="fallback", value=value, attempts=tuple(attempts), circuit_state=self.state, error_type=error_type)
        return CallResult(status="rejected", value=None, attempts=tuple(attempts), circuit_state=self.state, error_type=error_type)

