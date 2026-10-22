# ReleaseGuard Reliability

**Keep provider failures from becoming user failures.**

Capability **08 / 09** in the AI ReleaseGuard portfolio. This package provides bounded retries, timeout classification, exponential backoff with injectable jitter, rate limiting, a concurrency gate, circuit breaker state, and an explicit fallback path.

## Quickstart

```powershell
python -m pip install -e ".[demo,dev]"
python -m pytest -q
releaseguard-reliability --scenario timeout
python -m uvicorn app:app --reload
```

The browser/API demo includes success, timeout, injected 5xx, and injected 429 scenarios. Provider responses are replayed; failure scenarios are labelled `failure_injection`. The public state is limited to the request and does not claim distributed coordination.

## Behavior

- Only timeout, server, and rate-limit errors are retried.
- Retries are bounded by `max_retries` and use exponential backoff plus jitter.
- A circuit opens after the configured consecutive failure threshold, then allows a half-open probe after recovery timeout.
- The semaphore rejects work when the local concurrency limit is full.
- The local rate limiter rejects excess calls in a one-second window.
- Fallback is explicit in the result; no fallback is silently counted as provider success.

All time, sleep, and randomness dependencies are injectable, making circuit and retry behavior deterministic in tests. This v0.1 implementation is process-local; production-wide rate limits and circuit state require a coordinated backend.

License: MIT.

