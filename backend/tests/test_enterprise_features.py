import io
import os
import sys
import pytest
from PIL import Image
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from services.bias_radar import get_domain_bias_info, analyze_sources_bias
from services.xai_explainer import generate_token_heatmap, detect_logical_fallacies, build_xai_explanation_report
from services.multi_agent_jury import run_multi_agent_jury
from services.multimodal import perform_error_level_analysis, analyze_ai_generation_markers, process_multimodal_verification
from services.article_scanner import decompose_text_into_atomic_claims
from services.misinformation_radar import get_trending_misinformation_alerts

client = TestClient(app)

def test_bias_radar_domain_lookup():
    """Verify domain mapping against Media Bias Database."""
    reuters = get_domain_bias_info("reuters.com")
    assert reuters["bias"] == "CENTER"
    assert reuters["factuality"] == "VERY HIGH"
    assert reuters["score"] >= 95

    fox = get_domain_bias_info("https://www.foxnews.com/politics")
    assert fox["bias"] == "RIGHT"

    guardian = get_domain_bias_info("theguardian.com")
    assert guardian["bias"] == "LEFT"

    gov = get_domain_bias_info("https://data.nasa.gov")
    assert gov["factuality"] == "VERY HIGH"

def test_sources_bias_aggregation():
    """Verify aggregated bias spectrum and 2D radar coordinates."""
    sources = [
        {"domain": "reuters.com", "url": "https://reuters.com/1"},
        {"domain": "bbc.com", "url": "https://bbc.com/2"},
        {"domain": "apnews.com", "url": "https://apnews.com/3"}
    ]
    report = analyze_sources_bias(sources)
    assert report["overall_factuality_rating"] in ["VERY HIGH", "HIGH"]
    assert report["sources_analyzed"] == 3
    assert len(report["source_nodes"]) == 3
    assert "center" in report["bias_distribution"]

def test_xai_token_heatmap_and_fallacies():
    """Verify token attention heatmap generation and fallacy recognition."""
    claim = "Drinking salt water cures all viral infections immediately."
    heatmap = generate_token_heatmap(claim, verdict="FALSE")
    assert len(heatmap) > 0
    # "cures" should have high weight
    cure_tokens = [t for t in heatmap if t["token"].lower() == "cures"]
    assert len(cure_tokens) == 1
    assert cure_tokens[0]["weight"] >= 0.75

    fallacies = detect_logical_fallacies("X happened right after the event, which proves it caused the deadly threat.")
    assert len(fallacies) >= 1

    xai_pkg = build_xai_explanation_report(claim, "FALSE")
    assert "token_heatmap" in xai_pkg
    assert "interpretability_score" in xai_pkg

def test_multi_agent_jury():
    """Verify 3-agent deliberation, debate transcript, and consensus vote."""
    sup = [{"domain": "who.int", "quote": "Clinical studies confirm safety."}]
    con = []
    jury = run_multi_agent_jury(
        claim="Vaccines undergo multi-phase safety trials",
        verdict="TRUE",
        confidence=95.0,
        supporting_sources=sup,
        contradicting_sources=con,
        summary="Verified by clinical trials."
    )

    assert jury["jury_verdict"] == "TRUE"
    assert len(jury["debate_transcript"]) == 3
    assert jury["debate_transcript"][0]["speaker"] == "The Advocate Agent"
    assert jury["debate_transcript"][1]["speaker"] == "The Skeptic Agent"
    assert jury["debate_transcript"][2]["speaker"] == "The Presiding Judge Agent"
    assert jury["consensus_confidence"] >= 80

def test_multimodal_forensics():
    """Verify Image Forensics ELA and synthetic marker detection on generated image."""
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()

    ela = perform_error_level_analysis(img_bytes)
    assert "tamper_score" in ela
    assert ela["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

    ai_meta = analyze_ai_generation_markers(img_bytes, filename="test_dalle_image.png")
    assert ai_meta["is_ai_generated"] is True

    multimodal_res = process_multimodal_verification(img_bytes, "photo.jpg")
    assert multimodal_res["multimodal_status"] == "PROCESSED_SUCCESSFULLY"

def test_article_decomposition():
    """Verify atomic claim decomposition from paragraphs."""
    paragraphs = [
        "Global surface temperatures in 2023 were the warmest since modern record-keeping began in 1880. Climate scientists at NASA confirmed the findings.",
        "Renewable energy investments increased by twenty percent across European nations last year."
    ]
    claims = decompose_text_into_atomic_claims(paragraphs)
    assert len(claims) >= 1
    assert any("temperatures" in c["claim_text"] or "Renewable" in c["claim_text"] for c in claims)

def test_misinformation_radar():
    """Verify live misinformation radar alerts retrieval."""
    alerts = get_trending_misinformation_alerts()
    assert len(alerts) >= 5
    assert "headline" in alerts[0]
    assert "velocity" in alerts[0]

def test_api_enterprise_endpoints():
    """Verify FastAPI enterprise endpoints."""
    res_radar = client.get("/api/enterprise/radar/trending")
    assert res_radar.status_code == 200
    assert res_radar.json()["status"] == "LIVE"

    res_bias = client.get("/api/enterprise/bias/domain-info?domain=bbc.com")
    assert res_bias.status_code == 200
    assert res_bias.json()["bias"] == "CENTER"

    res_scan = client.post("/api/enterprise/article/deep-scan", json={
        "article_text": "Drinking water keeps humans hydrated and healthy. Eating fresh vegetables provides essential vitamins."
    })
    assert res_scan.status_code == 200
    data = res_scan.json()
    assert "truth_index" in data
    assert "paragraphs" in data
