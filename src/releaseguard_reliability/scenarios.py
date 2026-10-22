from .models import ReliabilityConfig
from .reliability import ProviderRateLimit, ProviderServerError, ProviderTimeout, ResilientProvider


def run_scenario(name: str):
    if name not in {"success", "timeout", "server-error", "rate-limit"}: raise ValueError("unknown scenario")
    calls = []
    def provider(request):
        calls.append(request)
        if name == "timeout": raise ProviderTimeout("injected timeout")
        if name == "server-error": raise ProviderServerError("injected 5xx")
        if name == "rate-limit": raise ProviderRateLimit("injected 429")
        return f"replayed response for {request}"
    service = ResilientProvider(ReliabilityConfig(max_retries=2, backoff_base_seconds=0, backoff_jitter_seconds=0), fallback=lambda request: f"fallback response for {request}")
    result = service.call("demo request", provider)
    return {"scenario": name, "result": result.model_dump(mode="json"), "provider_calls": len(calls), "state": service.state.value, "origin": "failure_injection" if name != "success" else "provider_replay"}

