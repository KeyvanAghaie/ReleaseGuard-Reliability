from releaseguard_reliability import (
    CircuitState,
    ProviderServerError,
    ReliabilityConfig,
    ResilientProvider,
)
from releaseguard_reliability.scenarios import run_scenario


def test_success_does_not_retry():
    result = run_scenario("success")["result"]
    assert result["status"] == "success" and len(result["attempts"]) == 1

def test_timeout_retries_then_fallback():
    result = run_scenario("timeout")["result"]
    assert result["status"] == "fallback" and len(result["attempts"]) == 4
    assert result["attempts"][-1]["outcome"] == "fallback"

def test_server_error_retries_are_bounded():
    result = run_scenario("server-error")["result"]
    assert result["status"] == "fallback"
    assert len(result["attempts"]) == 4

def test_circuit_opens_after_failures_and_fallbacks_without_provider_call():
    calls = []
    service = ResilientProvider(ReliabilityConfig(max_retries=0, failure_threshold=1), fallback=lambda _: "safe")
    def provider(_):
        calls.append(1)
        raise ProviderServerError("boom")
    assert service.call("a", provider).status == "fallback"
    assert service.state == CircuitState.OPEN
    assert service.call("b", provider).status == "fallback"
    assert len(calls) == 1

def test_non_retryable_error_does_not_retry():
    calls = []
    service = ResilientProvider(ReliabilityConfig(max_retries=3), fallback=lambda _: "safe")
    def provider(_):
        calls.append(1)
        raise ValueError("bad request")
    result = service.call("a", provider)
    assert result.status == "fallback" and len(calls) == 1

