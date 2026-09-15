import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)

def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data

def test_admin_stats_endpoint():
    response = client.get("/api/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "db_size_mb" in data
    assert "embedding_count" in data

def test_analytics_summary_endpoint():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_verified_claims" in data

def test_verify_claim_endpoint():
    response = client.post("/api/verify", json={"claim": "NASA confirmed liquid water discovered on Mars"})
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert "confidence" in data
    assert "confidence_breakdown" in data
