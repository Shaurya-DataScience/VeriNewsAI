"""
AVeriTeC Dataset Integration & Quality Tests for VeriNews AI
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from training.dataset_preprocessor import (
    load_averitec, load_and_preprocess_datasets, normalize_label, LABEL_MAP
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def test_averitec_label_normalization():
    """Verify all AVeriTeC specific raw labels map accurately to 4-class taxonomy."""
    assert normalize_label("Supported") == "TRUE"
    assert normalize_label("Refuted") == "FALSE"
    assert normalize_label("Conflicting Evidence/Cherrypicking") == "MISLEADING"
    assert normalize_label("Conflicting Evidence/Cherry-picking") == "MISLEADING"
    assert normalize_label("Not Enough Evidence") == "UNVERIFIED"
    assert normalize_label("Not Enough Info") == "UNVERIFIED"
    assert normalize_label("NEE") == "UNVERIFIED"

def test_load_averitec_schema_and_integrity():
    """Verify AVeriTeC loader parses dataset splits into the unified schema."""
    records = load_averitec(str(DATA_DIR))
    
    assert len(records) > 0, "Expected AVeriTeC records to be loaded from backend/data/averitec/"

    # Check required common schema fields
    required_keys = {"claim", "label", "verdict", "evidence", "source", "source_url", "dataset"}
    
    label_set = set()
    has_evidence_count = 0
    has_url_count = 0

    for r in records:
        assert required_keys.issubset(r.keys()), f"Missing keys in record: {r}"
        assert r["dataset"] == "averitec"
        assert r["label"] in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"]
        assert r["verdict"] in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"]
        assert len(r["claim"].strip()) > 0
        assert isinstance(r["evidence"], list)

        label_set.add(r["label"])
        if len(r["evidence"]) > 0:
            has_evidence_count += 1
        if r["source_url"]:
            has_url_count += 1

    # Verify multi-class representation
    assert "TRUE" in label_set
    assert "FALSE" in label_set
    assert "MISLEADING" in label_set
    assert "UNVERIFIED" in label_set

    # Verify high evidence and source URL retention
    assert has_evidence_count / len(records) >= 0.90
    assert has_url_count / len(records) >= 0.90

def test_load_and_preprocess_datasets_includes_averitec():
    """Verify load_and_preprocess_datasets merges AVeriTeC along with all datasets without breakage."""
    texts, labels = load_and_preprocess_datasets(str(DATA_DIR))
    assert len(texts) > 0
    assert len(labels) == len(texts)
    assert all(l in [0, 1, 2, 3] for l in labels)
