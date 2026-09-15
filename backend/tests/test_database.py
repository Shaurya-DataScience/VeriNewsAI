import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import get_connection, init_db, save_to_cache, get_from_cache, get_admin_stats, get_analytics_summary, get_system_config, save_system_config

def test_database_connection():
    conn = get_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    res = cursor.fetchone()
    conn.close()
    assert res[0] == 1

def test_cache_set_and_get():
    query = "pytest unit test claim"
    data = {"claim": query, "verdict": "SUPPORTED", "confidence": 99, "summary": "Test summary"}
    save_to_cache(query, data)

    cached = get_from_cache(query)
    assert cached is not None
    assert cached["claim"] == query
    assert cached["verdict"] == "SUPPORTED"

def test_admin_stats_and_analytics():
    stats = get_admin_stats()
    assert "db_size_mb" in stats
    assert "embedding_count" in stats
    assert stats["system_status"] in ["HEALTHY", "DEGRADED"]

    analytics = get_analytics_summary()
    assert "total_verified_claims" in analytics
    assert "verdict_counts" in analytics

def test_system_config():
    cfg = get_system_config()
    assert "weights" in cfg
    assert "similarity_threshold" in cfg

    updated = {"weights": {"dataset_prediction": 0.40, "cross_encoder": 0.30, "source_credibility": 0.20, "semantic_similarity": 0.10}, "similarity_threshold": 0.88}
    success = save_system_config(updated)
    assert success is True

    new_cfg = get_system_config()
    assert new_cfg["weights"]["dataset_prediction"] == 0.40
