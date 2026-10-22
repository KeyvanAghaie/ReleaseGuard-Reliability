from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from releaseguard_reliability.scenarios import run_scenario

app = FastAPI(title="ReleaseGuard Reliability", version="0.1.0")
class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["success", "timeout", "server-error", "rate-limit"]
@app.get("/api/health")
def health(): return {"status":"ok","version":"0.1.0"}
@app.post("/api/reliability")
def reliability(request: Request): return run_scenario(request.scenario)

