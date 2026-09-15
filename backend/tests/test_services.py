import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.classifier import classify_claim
from services.confidence_engine import calculate_weighted_confidence, ConfidenceEngine

def test_classifier_inference():
    res = classify_claim("NASA confirmed liquid water discovered on Mars")
    assert "label" in res
    assert res["label"] in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"]
    assert "confidence" in res
    assert "probabilities" in res

def test_confidence_engine_calculation():
    engine = ConfidenceEngine()
    conf, breakdown = engine.calculate_confidence(
        classifier_confidence=80.0,
        cross_encoder_score=90.0,
        source_credibility=95.0,
        semantic_similarity=85.0
    )
    assert 0 <= conf <= 100
    assert "dataset_prediction" in breakdown
    assert "cross_encoder" in breakdown
    assert "weights_used" in breakdown
