from fastapi.testclient import TestClient

from demo.api import app

client = TestClient(app)
def test_timeout_demo():
    response = client.post("/api/reliability", json={"scenario":"timeout"})
    assert response.status_code == 200 and response.json()["result"]["status"] == "fallback"

