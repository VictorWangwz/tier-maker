"""Integration tests for the API endpoints (requires running server or test client)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_generate_empty_text(client):
    resp = client.post("/generate", json={"text": ""})
    assert resp.status_code == 400


def test_generate_missing_body(client):
    resp = client.post("/generate")
    assert resp.status_code == 422  # validation error


# NOTE: The following test requires a running LLM server.
# Uncomment and configure .env to run it.
#
# def test_generate_full_pipeline(client):
#     resp = client.post("/generate", json={
#         "text": "Apple and Samsung in S tier, Google in A tier, Xiaomi in B tier"
#     })
#     assert resp.status_code == 200
#     data = resp.json()
#     assert "image_url" in data
#     assert "tier_data" in data
#     assert len(data["tier_data"]["categories"]) >= 2
