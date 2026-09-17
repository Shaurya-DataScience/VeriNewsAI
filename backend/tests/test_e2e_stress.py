"""
End-to-End Stress & Integration Test Suite for VeriNews AI Platform.
Validates live backend verification pipeline, fake/hoax detection, streaming SSE,
edge cases, and frontend payload contract compatibility.
"""

import os
import sys
import pytest
import requests
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

BASE_URL = "http://127.0.0.1:8000"

try:
    _r = requests.get(f"{BASE_URL}/health", timeout=1.0)
    _live_server = (_r.status_code == 200)
except Exception:
    _live_server = False

class ClientWrapper:
    def __init__(self, test_client):
        self.tc = test_client

    def get(self, url, params=None, timeout=None, stream=False):
        if _live_server:
            return requests.get(url, params=params, timeout=timeout, stream=stream)
        path = url.replace(BASE_URL, "")
        return self.tc.get(path, params=params)

http_client = ClientWrapper(TestClient(app))

def test_health_check():
    """Verify backend health and operational status."""
    res = http_client.get(f"{BASE_URL}/health", timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "healthy"
    assert "project" in data

def test_wild_fake_claim_detection():
    """
    Stress test with an outrageous fabricated conspiracy claim:
    'NASA discovered a massive alien spaceship buried under the ice in Antarctica'
    Expect the model and consensus to detect falsehood or lack of verified evidence.
    """
    fake_claim = "NASA discovered a massive alien spaceship buried under the ice in Antarctica"
    res = http_client.get(
        f"{BASE_URL}/search",
        params={"query": fake_claim, "force_refresh": "true"},
        timeout=30
    )
    assert res.status_code == 200
    data = res.json()
    
    # 1. Verify required root fields
    assert "verdict" in data
    assert "confidence" in data
    assert "confidence_breakdown" in data
    assert "claim" in data or "query" in data
    
    verdict = data.get("verdict", "").upper()
    print(f"\n[Wild Fake Claim Result] Verdict: {verdict}, Confidence: {data.get('confidence')}%")
    
    # Verdict should NEVER be 'TRUE' for this fabricated claim
    assert verdict in ["FALSE", "MISLEADING", "UNVERIFIED"], f"Expected non-true verdict for hoax, got {verdict}"
    
    # 2. Check XAI explanation
    assert "xai_explanation" in data
    xai = data["xai_explanation"]
    assert "token_heatmap" in xai or "interpretability_score" in xai
    
    # 3. Check Multi-Agent Jury
    assert "multi_agent_jury" in data
    jury = data["multi_agent_jury"]
    assert "jury_verdict" in jury
    
    # 4. Check Hallucination report
    assert "hallucination_report" in data

def test_genuine_claim_verification():
    """
    Test standard factual claim: 'NASA confirmed liquid water discovered on Mars'
    """
    true_claim = "NASA confirmed liquid water discovered on Mars"
    res = http_client.get(
        f"{BASE_URL}/search",
        params={"query": true_claim},
        timeout=30
    )
    assert res.status_code == 200
    data = res.json()
    
    verdict = data.get("verdict", "").upper()
    confidence = data.get("confidence", 0)
    print(f"\n[Genuine Claim Result] Verdict: {verdict}, Confidence: {confidence}%")
    assert verdict in ["TRUE", "VERIFIED", "MISLEADING"], f"Unexpected verdict {verdict}"
    assert confidence > 0

def test_edge_case_special_characters_and_emojis():
    """
    Test robustness against emojis, symbols, and formatting noise.
    """
    claim = "🚀 BREAKING: Scientist finds 100% cure for all aging in 2026? [SHOCKING] #viral @science"
    res = http_client.get(
        f"{BASE_URL}/search",
        params={"query": claim},
        timeout=30
    )
    assert res.status_code == 200
    data = res.json()
    assert "verdict" in data
    assert isinstance(data.get("confidence"), (int, float))

def test_edge_case_long_article_payload():
    """
    Test deep scan capability with multi-paragraph text (1500+ characters).
    """
    long_text = (
        "An international consortium of climate researchers published findings today "
        "indicating global sea levels rose by an average of 3.4 millimeters per year over the last decade. "
        "The peer-reviewed analysis combined radar altimetry from European Space Agency satellites "
        "with thousands of autonomous ocean floats known as Argo. "
    ) * 4
    
    res = http_client.get(
        f"{BASE_URL}/search",
        params={"query": long_text},
        timeout=30
    )
    assert res.status_code == 200
    data = res.json()
    assert "verdict" in data

def test_streaming_summary_endpoint():
    """
    Verify the SSE streaming endpoint responds with event stream headers.
    """
    # 1. Do a search to generate a search_id
    res = http_client.get(f"{BASE_URL}/search", params={"query": "Mars water"}, timeout=20)
    assert res.status_code == 200
    data = res.json()
    search_id = data.get("search_id")
    
    if search_id:
        stream_res = http_client.get(
            f"{BASE_URL}/stream-summary/{search_id}",
            stream=True,
            timeout=10
        )
        assert stream_res.status_code == 200
        content_type = stream_res.headers.get("content-type", "")
        assert "text/event-stream" in content_type or "text/plain" in content_type

def test_frontend_contract_compatibility():
    """
    Verify all fields required by frontend/script.js normalizeResponse exist and have safe types.
    """
    res = http_client.get(f"{BASE_URL}/search", params={"query": "Apple acquired OpenAI"}, timeout=20)
    assert res.status_code == 200
    data = res.json()
    
    # Frontend script.js critical keys
    assert "verdict" in data and isinstance(data["verdict"], str)
    assert "confidence" in data and isinstance(data["confidence"], (int, float))
    assert "supporting_sources" in data and isinstance(data["supporting_sources"], list)
    assert "contradicting_sources" in data and isinstance(data["contradicting_sources"], list)
    assert "bias_radar" in data and isinstance(data["bias_radar"], dict)
    assert "xai_explanation" in data and isinstance(data["xai_explanation"], dict)
